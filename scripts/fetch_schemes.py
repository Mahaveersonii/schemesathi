"""Download the official text of each scheme from myScheme (Government of India's scheme portal).

myScheme's robots.txt allows crawling. We fetch one scheme per second, keep the raw JSON for
traceability, and write a clean Markdown file per scheme that the report library (RAG) indexes.

    python scripts/fetch_schemes.py            # all schemes in data/scheme_list.yaml
    python scripts/fetch_schemes.py pm-kisan   # just one
    python scripts/fetch_schemes.py --rebuild  # rewrite the Markdown from the saved JSON (no network)
"""
import html
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "schemes"
API = "https://www.myscheme.gov.in/api/apisetu/schemes"
HEADERS = {"User-Agent": "SchemeSathi student project (AABA, FORE School of Management)"}


def clean(md: str) -> str:
    md = html.unescape(md or "")
    md = re.sub(r"<[^>]+>", "", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def rich_text(nodes, depth=0) -> str:
    """myScheme stores some sections only as rich-text trees (lists, headings): turn them into Markdown."""
    out = []
    for n in nodes or []:
        kind, kids = n.get("type"), n.get("children")
        if "text" in n and not kind:
            out.append(n["text"])
        elif kind in ("ol_list", "ul_list"):
            items = [rich_text(k.get("children"), depth + 1).strip() for k in kids or []]
            out.append("\n" + "\n".join("  " * depth + f"- {i}" for i in items if i) + "\n")
        elif kind and kind.startswith("heading"):
            out.append(f"\n**{rich_text(kids, depth).strip()}**\n")
        else:
            out.append(rich_text(kids, depth) + ("\n" if kind == "paragraph" else ""))
    return re.sub(r"\n{3,}", "\n\n", "".join(out))


def documents_md(docs: dict) -> str:
    en = (docs.get("data") or {}).get("en") or {}
    return clean(en.get("documentsRequired_md") or rich_text(en.get("documents_required")))


def to_markdown(slug: str, d: dict, faqs: list) -> str:
    b, c, e = d["basicDetails"], d["schemeContent"], d["eligibilityCriteria"]
    ministry = (b.get("nodalMinistryName") or {}).get("label", "")
    parts = [f"# {b['schemeName']}", "",
             f"Short name: {b.get('schemeShortTitle') or slug} | Ministry: {ministry} | "
             f"Level: {(b.get('level') or {}).get('label', '')}",
             f"Source: https://www.myscheme.gov.in/schemes/{slug} (fetched {date.today().isoformat()})", "",
             "## Details", clean(c.get("detailedDescription_md")), "",
             "## Benefits", clean(c.get("benefits_md")), "",
             "## Eligibility", clean(e.get("eligibilityDescription_md")), ""]
    if c.get("exclusions_md"):
        parts += ["## Exclusions", clean(c["exclusions_md"]), ""]
    steps = []
    for mode in d.get("applicationProcess") or []:
        steps.append(f"### {mode.get('mode', 'Application')}\n{clean(mode.get('process_md'))}")
    if steps:
        parts += ["## Application Process", "\n\n".join(steps), ""]
    if faqs:
        parts += ["## Frequently Asked Questions"]
        for f in faqs:
            parts.append(f"**Q: {clean(f.get('question'))}**\n{clean(f.get('answer_md') or f.get('answer'))}\n")
    refs = c.get("references") or []
    if refs:
        parts += ["## Sources And References"] + [f"- {r['title']}: {r['url'].strip()}" for r in refs]
    return "\n".join(parts).strip() + "\n"


def build(slug: str, data: dict, docs: dict, faqs: dict) -> str:
    d = data["en"]
    faq_list = ((faqs.get("data") or {}).get("en") or {}).get("faqs", []) or []
    md = to_markdown(slug, d, faq_list)
    docs_text = documents_md(docs)
    if docs_text:
        md = md.replace("## Frequently Asked Questions", f"## Documents Required\n{docs_text}\n\n## Frequently Asked Questions") \
            if "## Frequently Asked Questions" in md else md + f"\n## Documents Required\n{docs_text}\n"
    (OUT / f"{slug}.md").write_text(md)
    return md


def fetch(slug: str) -> dict:
    r = requests.get(API, params={"slug": slug, "lang": "en"}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()["data"]
    sid = data["_id"]
    docs = requests.get(f"{API}/{sid}/documents", params={"lang": "en"}, headers=HEADERS, timeout=30).json()
    faqs = requests.get(f"{API}/{sid}/faqs", params={"lang": "en"}, headers=HEADERS, timeout=30).json()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{slug}.json").write_text(json.dumps({"scheme": data, "documents": docs, "faqs": faqs}, ensure_ascii=False, indent=1))
    md = build(slug, data, docs, faqs)
    return {"slug": slug, "name": data["en"]["basicDetails"]["schemeName"], "chars": len(md)}


def rebuild() -> None:
    for path in sorted(OUT.glob("*.json")):
        raw = json.loads(path.read_text())
        md = build(path.stem, raw["scheme"], raw["documents"], raw["faqs"])
        print(path.stem, len(md), "Documents Required" in md)


if __name__ == "__main__":
    if sys.argv[1:] == ["--rebuild"]:
        rebuild()
        sys.exit()
    wanted = sys.argv[1:] or [s["slug"] for s in yaml.safe_load((ROOT / "data" / "scheme_list.yaml").read_text())["schemes"]]
    for slug in wanted:
        try:
            print(fetch(slug))
        except Exception as exc:  # noqa: BLE001
            print({"slug": slug, "error": str(exc)})
        time.sleep(1)
