"""The agent's five tools. Each returns short JSON, is logged, and never crashes the run."""
import functools
import json
import re
import time

from crewai.tools import tool

from . import log, rag
from .rules import BY_SLUG, SCHEMES, evaluate, summary

RUN = {"run_id": None, "profile": {}, "results": [], "citations": set(), "called": [], "seen": set(),
       "domains": set(), "question": ""}
DOMAIN = re.compile(r"\b(?:[a-z0-9-]+\.)+(?:gov\.in|nic\.in|co\.in|org\.in|com|in|org|net)\b", re.I)
_SHORT = {s.short.lower(): s.slug for s in SCHEMES}


def reset(run_id, profile, question=""):
    RUN.update(run_id=run_id, profile=profile or {}, results=evaluate(profile or {}), citations=set(), called=[],
               seen=set(), domains=set(), question=question)


def _slug(name: str) -> str | None:
    n = (name or "").strip().lower()
    return n if n in BY_SLUG else _SHORT.get(n) or next((s.slug for s in SCHEMES if n and n in s.name.lower()), None)


def _logged(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.time()
        RUN["called"].append(fn.__name__)
        try:
            out = fn(*args, **kwargs)
            RUN["seen"].update(re.findall(r"\b[A-Z][A-Z\-]{2,}\b", out))   # terms the official text used
            RUN["domains"].update(d.lower() for d in DOMAIN.findall(out))   # web addresses it mentions
            log.event(RUN["run_id"], "tool_call", fn.__name__, json.dumps([args, kwargs])[:300], (time.time() - t0) * 1000)
            return out
        except Exception as exc:  # noqa: BLE001
            log.event(RUN["run_id"], "error", fn.__name__, str(exc))
            return json.dumps({"error": str(exc), "hint": "Continue with what you have and say what is missing."})
    return wrapper


@tool("check_eligibility")
@_logged
def check_eligibility(scope: str = "all") -> str:
    """Run the official eligibility rules for the person's profile. Returns, for each scheme,
    the verdict (eligible / likely / not_eligible), the reasons, and what still needs confirming.
    Use scope='all' or a scheme short name. These verdicts are final: never change them."""
    res = RUN["results"]
    if scope and scope.lower() != "all":
        slug = _slug(scope)
        res = [r for r in res if r["slug"] == slug]
    RUN["citations"].update(rag.tag(r["short"], "Eligibility") for r in res)
    fits = [{"scheme": r["short"], "citation": rag.tag(r["short"], "Eligibility"), "verdict": r["verdict"],
             "benefit": r["value_note"] or r["benefit"], "still_to_confirm": [u["label"] for u in r["unknown"]] + r["confirm"]}
            for r in res if r["relevant"] and r["verdict"] != "not_eligible"]
    out = {"summary": summary(RUN["results"]), "fits_you": fits,
           "not_eligible": [{"scheme": r["short"], "because_not": [f["label"] for f in r["failed"]]}
                            for r in res if r["verdict"] == "not_eligible"],
           "only_if_this_applies": [{"scheme": r["short"], "only_if": r["only_if"]} for r in res
                                    if r["only_if"] and r["verdict"] != "not_eligible"],
           "not_your_goal": [r["short"] for r in res if not r["relevant"] and not r["only_if"]
                             and r["verdict"] != "not_eligible"]}
    return json.dumps(out, ensure_ascii=False)


@tool("search_schemes")
@_logged
def search_schemes(question: str, scheme: str = "") -> str:
    """Search the official scheme text (myScheme) and return the most relevant passages, each with a
    citation tag like [PM-KISAN · Eligibility]. Optionally limit to one scheme by its short name."""
    hits = rag.search(question, k=4, slug=_slug(scheme) if scheme else None)
    RUN["citations"].update(h["citation"] for h in hits)
    return json.dumps([{"citation": h["citation"], "text": h["text"][:650]} for h in hits], ensure_ascii=False)


@tool("scheme_section")
@_logged
def scheme_section(scheme: str, section: str) -> str:
    """Exact official text of one section of one scheme. section is one of: Benefits, Eligibility,
    Exclusions, Application Process, Documents Required."""
    slug = _slug(scheme)
    if not slug:
        return json.dumps({"error": f"Unknown scheme '{scheme}'."})
    text = rag.section_text(slug, section)
    cite = rag.tag(BY_SLUG[slug].short, section.title() if section.islower() else section)
    RUN["citations"].add(cite)
    return json.dumps({"citation": cite, "text": text[:1800]}, ensure_ascii=False)


@tool("document_checklist")
@_logged
def document_checklist(schemes: str) -> str:
    """One combined, de-duplicated list of documents for several schemes (comma-separated short names)."""
    slugs = [x for x in (_slug(n) for n in schemes.split(",")) if x]
    RUN["citations"].update(rag.tag(BY_SLUG[x].short, "Documents Required") for x in slugs)
    docs = [{"document": d["document"], "for": d["for"]} for d in rag.documents(slugs)[:30]]
    cites = [rag.tag(BY_SLUG[x].short, "Documents Required") for x in slugs]
    return json.dumps({"cite_with": cites, "documents": docs}, ensure_ascii=False)


@tool("benefit_estimate")
@_logged
def benefit_estimate(scope: str = "eligible") -> str:
    """Money the person could receive: yearly cash from schemes they qualify for, plus one-time and
    future benefits described in words. Use it for 'how much could I get?'."""
    rows = [r for r in RUN["results"] if r["verdict"] in ("eligible", "likely") and r["relevant"]]
    return json.dumps({"yearly_cash_total": sum(r["yearly_value"] or 0 for r in rows),
                       "items": [{"scheme": r["short"], "verdict": r["verdict"], "yearly_value": r["yearly_value"],
                                  "value": r["value_note"] or r["benefit"]} for r in rows]}, ensure_ascii=False)


TOOLS = [check_eligibility, search_schemes, scheme_section, document_checklist, benefit_estimate]
