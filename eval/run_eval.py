"""Evaluate SchemeSathi. Writes eval/results.json (shown in the app) and prints a summary.

    python eval/run_eval.py                 # rules + retrieval (free, offline)
    python eval/run_eval.py --baseline      # + the same LLM without tools, guessing eligibility (12 calls)
    python eval/run_eval.py --agent 4       # + the full agent end to end on 4 personas (uses more Groq tokens)

1. Eligibility: rule engine vs hand labels from the official text (12 personas x 32 schemes).
2. Baseline:   the LLM alone, given the same profile and the list of 32 schemes, picks the ones that fit.
3. Retrieval:  24 questions with a known answer location. Hit@1, Hit@3, MRR; vector-only vs hybrid.
4. Agent:      latency, guardrail retries, citations that are real, verdict agreement with the rules.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemesathi import config, rag  # noqa: E402
from schemesathi.personas import PERSONAS  # noqa: E402
from schemesathi.rules import SCHEMES, evaluate  # noqa: E402

ALL = {s.short for s in SCHEMES}


def prf(expected: set, got: set) -> tuple[int, int, int]:
    return len(expected & got), len(got - expected), len(expected - got)


def scores(tp, fp, fn) -> dict:
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 1.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(2 * p * r / (p + r), 3) if p + r else 0.0}


def eval_rules() -> dict:
    tp = fp = fn = 0
    rows = []
    for per in PERSONAS:
        got = {r["short"] for r in evaluate(per["profile"]) if r["relevant"] and r["verdict"] != "not_eligible"}
        a, b, c = prf(per["expected"], got)
        tp, fp, fn = tp + a, fp + b, fn + c
        rows.append({"persona": per["name"], "expected": len(per["expected"]), "rules_tp": a, "rules_fp": b, "rules_fn": c})
    return {**scores(tp, fp, fn), "rows": rows}


def eval_baseline(model: str) -> dict:
    from crewai import LLM  # noqa: F401  (import check)
    from schemesathi.llm import make_llm
    llm = make_llm(model)
    names = "\n".join(f"- {s.short}: {s.name}" for s in SCHEMES)
    tp = fp = fn = 0
    rows, secs = [], []
    for per in PERSONAS:
        prof = {k: v for k, v in per["profile"].items()}
        prompt = (f"An Indian citizen has this profile: {json.dumps(prof)}\n\nFrom ONLY this list of central government "
                  f"schemes, pick every scheme this person is eligible for and that matches their goals "
                  f"(goals: {prof.get('goals')}). Schemes whose main purpose is a goal they did not pick (business loans, "
                  f"job training) should be left out.\n{names}\n\nReply with a JSON list of the short names only.")
        t0 = time.time()
        for attempt in range(3):
            try:
                text = llm.call([{"role": "user", "content": prompt}])
                break
            except Exception as exc:  # noqa: BLE001
                text = ""
                print("  baseline error:", str(exc)[:120])
                time.sleep(8)
        secs.append(time.time() - t0)
        m = re.search(r"\[.*\]", text or "", re.S)
        try:
            got = {x.strip() for x in json.loads(m.group(0))} & ALL if m else set()
        except json.JSONDecodeError:
            got = set()
        a, b, c = prf(per["expected"], got)
        tp, fp, fn = tp + a, fp + b, fn + c
        rows.append({"persona": per["name"], "llm_tp": a, "llm_fp": b, "llm_fn": c,
                     "llm_wrong": sorted(got - per["expected"]), "llm_missed": sorted(per["expected"] - got)})
        print(f"  {per['name']:8} tp={a} fp={b} fn={c}")
        time.sleep(2)
    return {**scores(tp, fp, fn), "model": model, "avg_seconds": round(sum(secs) / len(secs), 1), "rows": rows}


def eval_retrieval() -> dict:
    qs = yaml.safe_load((ROOT / "eval" / "questions.yaml").read_text())
    out = {}
    variants = (("vector only", 1.0, 0.0), ("hybrid (0.9 vector + 0.1 keyword)", 0.9, 0.0),
                ("hybrid + intent boost", 0.9, rag.INTENT_BOOST))
    for label, alpha, boost in variants:
        config.ALPHA = alpha
        h1 = h3 = mrr = 0.0
        for q in qs:
            hits = rag.search(q["q"], k=5, boost=boost)
            ranks = [i for i, h in enumerate(hits, 1) if h["slug"] == q["slug"] and h["section"] == q["section"]]
            scheme_ranks = [i for i, h in enumerate(hits, 1) if h["slug"] == q["slug"]]
            r = ranks[0] if ranks else None
            h1 += r == 1
            h3 += bool(r and r <= 3)
            mrr += 1 / r if r else 0
            q.setdefault("scheme_hit1", {})[label] = bool(scheme_ranks and scheme_ranks[0] == 1)
        n = len(qs)
        out[label] = {"hit@1": round(h1 / n, 3), "hit@3": round(h3 / n, 3), "mrr": round(mrr / n, 3),
                      "scheme_hit@1": round(sum(q["scheme_hit1"][label] for q in qs) / n, 3)}
    config.ALPHA = 0.9
    return {"n": len(qs), **out}


def eval_agent(n: int) -> dict:
    from schemesathi.agent import CITE, ask
    q = "Which schemes can I get, how much money a year, and what should I do first?"
    rows = []
    for per in PERSONAS[:n]:
        try:
            out = ask(q, per["profile"], emit=lambda m: None)
        except Exception as exc:  # noqa: BLE001
            rows.append({"persona": per["name"], "error": str(exc)[:200]})
            continue
        fits = {r["short"] for r in evaluate(per["profile"]) if r["relevant"] and r["verdict"] != "not_eligible"}
        mentioned = {s for s in ALL if re.search(rf"(?<![\w-]){re.escape(s)}(?![\w-])", out["answer"], re.I)}
        cites = CITE.findall(out["answer"])
        rows.append({"persona": per["name"], "seconds": out["seconds"], "model": out["model"].split("/")[-1],
                     "retries": out["retries"], "verified": out["verified"], "citations": len(cites),
                     "fitting_mentioned": f"{len(mentioned & fits)}/{len(fits)}",
                     "non_fitting_mentioned": sorted(mentioned - fits)})
        print("  ", rows[-1])
    ok = [r for r in rows if "error" not in r]
    return {"rows": rows, "avg_seconds": round(sum(r["seconds"] for r in ok) / len(ok), 1) if ok else None,
            "verified_rate": round(sum(r["verified"] for r in ok) / len(ok), 3) if ok else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--agent", type=int, default=0)
    ap.add_argument("--model", default=None)
    a = ap.parse_args()
    path = ROOT / "eval" / "results.json"
    res = json.loads(path.read_text()) if path.exists() else {}
    print("1. eligibility rules");  res["rules"] = eval_rules(); print("  ", {k: v for k, v in res["rules"].items() if k != "rows"})
    print("3. retrieval");  res["retrieval"] = eval_retrieval(); print("  ", res["retrieval"])
    if a.baseline or a.agent:
        from schemesathi.llm import model_chain
        model = a.model or model_chain()[0]
    if a.baseline:
        print(f"2. LLM-only baseline on {model}"); res["baseline"] = eval_baseline(model)
        print("  ", {k: v for k, v in res["baseline"].items() if k != "rows"})
    if a.agent:
        print(f"4. agent end to end ({a.agent} personas)"); res["agent"] = eval_agent(a.agent)
    # tiles + table for the app
    tiles = [("Rules F1", f'{res["rules"]["f1"]:.0%}', f'P {res["rules"]["precision"]:.0%} · R {res["rules"]["recall"]:.0%}', "green")]
    if "baseline" in res:
        b = res["baseline"]
        tiles.append(("LLM alone F1", f'{b["f1"]:.0%}', f'P {b["precision"]:.0%} · R {b["recall"]:.0%} ({b["model"].split("/")[-1]})', "amber"))
    hy = res["retrieval"]["hybrid + intent boost"]
    tiles.append(("Retrieval Hit@3", f'{hy["hit@3"]:.0%}', f'MRR {hy["mrr"]:.2f} · {res["retrieval"]["n"]} questions', "saffron"))
    if res.get("agent", {}).get("avg_seconds"):
        tiles.append(("Agent answer time", f'{res["agent"]["avg_seconds"]} s', f'verified {res["agent"]["verified_rate"]:.0%}', "ink"))
    res["tiles"] = tiles
    table = []
    for r in res["rules"]["rows"]:
        row = dict(r)
        b = next((x for x in res.get("baseline", {}).get("rows", []) if x["persona"] == r["persona"]), None)
        if b:
            row.update(llm_tp=b["llm_tp"], llm_fp=b["llm_fp"], llm_fn=b["llm_fn"], llm_wrong=", ".join(b["llm_wrong"]),
                       llm_missed=", ".join(b["llm_missed"]))
        table.append(row)
    res["table"] = table
    path.write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("saved", path)


if __name__ == "__main__":
    main()
