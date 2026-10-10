"""Offline tests: no AI model and no embedding server needed.   pytest -q"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from schemesathi import agent, rag, tools  # noqa: E402
from schemesathi.personas import BY_ID, PERSONAS  # noqa: E402
from schemesathi.rules import BY_SLUG, SCHEMES, evaluate, summary  # noqa: E402


def fits(profile):
    return {r["short"] for r in evaluate(profile) if r["relevant"] and r["verdict"] != "not_eligible"}


def verdict(profile, short):
    return next(r for r in evaluate(profile) if r["short"] == short)


# ---------- rule engine ----------
def test_32_schemes_with_quotes_and_data():
    assert len(SCHEMES) == 32 and len(BY_SLUG) == 32
    for s in SCHEMES:
        assert (ROOT / "data" / "schemes" / f"{s.slug}.md").exists(), s.slug
        assert s.checks and all(c.quote for c in s.checks), s.short


@pytest.mark.parametrize("persona", PERSONAS, ids=[p["id"] for p in PERSONAS])
def test_personas_match_hand_labels(persona):
    assert fits(persona["profile"]) == persona["expected"]


def test_failed_check_gives_not_eligible_with_reason():
    p = dict(BY_ID["sanjay"]["profile"])            # tenant farmer: land not in his name
    r = verdict(p, "PM-KISAN")
    assert r["verdict"] == "not_eligible"
    assert [f["label"] for f in r["failed"]] == ["Cultivable land in your own name"]


def test_unknown_answer_means_likely_not_eligible():
    p = {"age": 30, "occupation": "farmer"}           # land ownership not given
    assert verdict(p, "PM-KISAN")["verdict"] == "likely"


def test_office_only_conditions_keep_verdict_at_likely():
    assert verdict(BY_ID["ramesh"]["profile"], "PM-KISAN")["verdict"] == "likely"
    assert verdict(BY_ID["ramesh"]["profile"], "KCC")["verdict"] == "eligible"


def test_business_loans_hidden_when_not_a_goal():
    p = {**BY_ID["imran"]["profile"], "goals": ["pension"]}
    r = verdict(p, "MUDRA")
    assert r["verdict"] != "not_eligible" and r["relevant"] is False


def test_life_situation_schemes_are_only_if():
    p = {k: v for k, v in BY_ID["fatima"]["profile"].items() if k != "pregnant"}
    r = verdict(p, "JSSK")
    assert r["only_if"] == ["Pregnant"] and not r["relevant"]


def test_men_are_not_shown_maternity_or_widow_schemes():
    p = {"age": 30, "gender": "male", "area": "rural"}
    assert verdict(p, "JSSK")["verdict"] == "not_eligible"
    assert verdict(p, "IGNWPS")["verdict"] == "not_eligible"


def test_summary_counts_only_relevant_cash():
    s = summary(evaluate(BY_ID["ramesh"]["profile"]))
    assert s["yearly_cash"] == 6000 and s["eligible"] == 4 and s["likely"] == 2


def test_pm_kmy_requires_land_in_own_name():
    p = {**BY_ID["sanjay"]["profile"], "age": 30}
    assert verdict(p, "PM-KMY")["verdict"] == "not_eligible"


# ---------- library (RAG helpers that need no embeddings) ----------
def test_sections_and_chunks():
    md = (ROOT / "data" / "schemes" / "pm-kisan.md").read_text()
    names = [n for n, _ in rag.sections(md)]
    assert {"Benefits", "Eligibility", "Documents Required"} <= set(names)
    parts = rag.chunks("word " * 600) + rag.chunks("A sentence that ends here. " * 120)
    assert len(parts) > 1 and all(len(p) <= 900 + 160 for p in parts)


def test_documents_are_merged_across_schemes():
    docs = rag.documents(["pm-kisan", "kcc", "pmfby", "mgnrega"])
    aadhaar = next(d for d in docs if d["document"] == "Aadhaar card")
    assert len(aadhaar["for"]) == 4 and docs[0] is aadhaar


@pytest.mark.parametrize("q,section", [("What documents do I need?", "Documents Required"),
                                       ("How do I apply for it?", "Application Process"),
                                       ("How much money will I get?", "Benefits"),
                                       ("Who can apply, what are the criteria", "Eligibility")])
def test_question_intent(q, section):
    assert rag.intent(q) == section


def test_rich_text_documents_are_converted():
    import fetch_schemes
    tree = [{"type": "heading_four", "children": [{"text": "Indicative Documents"}]},
            {"type": "ol_list", "children": [{"type": "list_item", "children": [{"text": "Aadhaar Card"}]},
                                             {"type": "list_item", "children": [{"text": "Landholding papers"}]}]}]
    md = fetch_schemes.documents_md({"data": {"en": {"documents_required": tree}}})
    assert "- Aadhaar Card" in md and "- Landholding papers" in md


# ---------- the agent's guardrail ----------
@pytest.fixture
def run():
    tools.reset(0, BY_ID["ramesh"]["profile"])
    tools.RUN["citations"] = {"[PM-KISAN · Benefits]", "[KCC · Eligibility]", "[PM-SYM · Eligibility]"}
    tools.RUN["called"], tools.RUN["seen"], tools.RUN["domains"], tools.RUN["question"] = [], set(), set(), ""
    return tools.RUN


def test_guardrail_accepts_real_citation_in_model_format(run):
    ok, text = agent.check_answer("You get ₹6,000 a year【PM‑KISAN · Benefits】.")
    assert ok and "[PM-KISAN · Benefits]" in text


def test_guardrail_rejects_invented_citation(run):
    ok, why = agent.check_answer("You get a house [PMAY-G · Benefits].")
    assert not ok and "not returned by any tool" in why


def test_guardrail_requires_a_citation(run):
    ok, _ = agent.check_answer("You get ₹6,000 a year.")
    assert not ok


def test_guardrail_blocks_contradicting_the_rules(run):
    ok, why = agent.check_answer("You are eligible for PM-SYM [PM-SYM · Eligibility].")
    assert not ok and "NOT eligible" in why
    ok, why = agent.check_answer("You are not eligible for KCC [KCC · Eligibility].")
    assert not ok and "IS eligible" in why


def test_guardrail_blocks_schemes_outside_the_library(run):
    ok, why = agent.check_answer("Join NPS for a pension [PM-KISAN · Benefits].")
    assert not ok and "NPS" in why


def test_terms_from_official_text_are_allowed(run):
    run["seen"] = {"EWS"}
    assert agent.check_answer("PMAY-U covers EWS families [PM-KISAN · Benefits].")[0]


def test_guardrail_checks_the_cash_total(run):
    run["called"].append("benefit_estimate")
    assert not agent.check_answer("Your total is ₹53,600 a year [PM-KISAN · Benefits].")[0]
    assert agent.check_answer("Your total is ₹6,000 a year [PM-KISAN · Benefits].")[0]


def test_guardrail_blocks_invented_web_addresses(run):
    assert not agent.check_answer("Apply on mangalmart.com [PM-KISAN · Benefits].")[0]
    run["domains"] = {"pmkisan.gov.in"}
    assert agent.check_answer("Apply on pmkisan.gov.in or myscheme.gov.in [PM-KISAN · Benefits].")[0]


def test_document_questions_need_the_document_tool(run):
    run["question"] = "What documents do I need?"
    ok, why = agent.check_answer("Bring Aadhaar [PM-KISAN · Benefits].")
    assert not ok and "document_checklist" in why
    run["called"].append("document_checklist")
    assert agent.check_answer("Bring Aadhaar [PM-KISAN · Benefits].")[0]


def test_tool_names_are_removed_from_answers(run):
    assert agent.normalize("Total ₹6,000 [benefit_estimate]. Aadhaar [Document checklist].") == "Total ₹6,000. Aadhaar."


def test_check_eligibility_tool_output(run):
    import json
    out = json.loads(tools.check_eligibility.run(scope="all"))
    assert {r["scheme"] for r in out["fits_you"]} == BY_ID["ramesh"]["expected"]
    assert "[PM-KISAN · Eligibility]" in tools.RUN["citations"]
