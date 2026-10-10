"""SchemeSathi: one agent, five tools, one guardrail.

  ask(question, profile)  ->  {"answer", "citations", "model", "seconds", "retries", "run_id", "trace"}

The agent plans its own tool calls (ReAct loop in CrewAI). Two things are never left to the model:
  - eligibility verdicts come from the rule engine (rules.py), the agent may only explain them;
  - every citation in the answer must be a passage a tool actually returned this run.
The guardrail checks both and sends the answer back with the reason if either is broken.
"""
import re
import time

from crewai import Agent, Crew, Process, Task

from . import log, tools
from .llm import make_llm, model_chain
from .rules import BY_SLUG, SCHEMES, summary

CITE = re.compile(r"\[([^\[\]·]+?) · ([^\[\]]+?)\]")
NEG = re.compile(r"\b(not eligible|ineligible|do(?:es)? not qualify|cannot apply|not qualify)\b", re.I)
# Upper-case words that are not scheme names (eligibility and paperwork vocabulary).
GENERIC = set("""BPL APL SC ST OBC EBC DNT CSC PSU PSE EPFO EPF ESIC ITI KYC EKYC SECC ULB LPG TB DBT IFSC PAN UT ID OTP SMS UPI
GOI NGO SHG FAQ PDF URL ATM PIN CA NOTE AND OR THE FOR NOT YES ALL INR RS GST MSME KVIC DIC SBI RRB NBFC MFI EMI CIBIL
SIDBI NABARD NREGA MGNREGS NIC IT UG PG II III PIB EWS LIG MIG NSAP ASHA ANM AWW ICDS NHM PHC CHC""".split())
KNOWN = {re.sub(r"[^A-Z]", "", w.upper()) for sc in SCHEMES for w in [sc.short, sc.slug, *sc.short.split()]} | \
        {"PMAY", "PMKVY", "SVANIDHI", "MUDRA", "YASASVI", "STANDUP", "VISHWAKARMA", "NIKSHAY", "KISAN", "MAANDHAN"}
POS = re.compile(r"\b(you are eligible|you qualify|you can apply|eligible for)\b", re.I)


def _profile_text(p: dict) -> str:
    shown = {k: v for k, v in p.items() if v not in (None, "", [], "unknown")}
    return "; ".join(f"{k}={v}" for k, v in shown.items()) or "nothing yet (ask the person for age, state, income and occupation)"


def normalize(text: str) -> str:
    """Models write tags as 【PM‑KISAN · Benefits】 (CJK brackets, non-breaking hyphens): make them plain."""
    text = text.replace("【", "[").replace("】", "]")
    text = re.sub("[\u2010\u2011\u2012\u2013]", "-", text)
    return re.sub(r"\s?\[(?:check_eligibility|search_schemes|scheme_section|document_checklist|benefit_estimate)\]", "", text)


def check_answer(text: str) -> tuple[bool, str]:
    """Return (ok, text_or_problem). Pure function so it can be unit-tested without an LLM."""
    text = normalize(text)
    allowed = tools.RUN["citations"]
    cited = {f"[{a.strip()} · {b.strip()}]" for a, b in CITE.findall(text)}
    if not cited:
        return False, "Cite at least one source tag exactly as a tool returned it, for example [PM-KISAN · Eligibility]."
    fake = sorted(cited - allowed)
    if fake:
        return False, (f"These citations were not returned by any tool in this conversation: {fake}. "
                       f"Use only: {sorted(allowed)[:12]}")
    outside = sorted({w for w in re.findall(r"\b[A-Z][A-Z\-]{2,}\b", text)
                      if w not in GENERIC and w not in tools.RUN.get("seen", ())
                      and re.sub(r"[^A-Z]", "", w) not in KNOWN})
    if outside:
        return False, (f"{outside} are not schemes SchemeSathi has official text for. Do not describe them; "
                       "talk only about schemes the tools returned, and point to myScheme.gov.in for others.")
    total = summary(tools.RUN["results"])["yearly_cash"]
    for amount in re.findall(r"total[^.\n]{0,80}?₹\s?([\d,]+)", text, flags=re.I):
        if int(amount.replace(",", "") or 0) not in (total, 0) and "benefit_estimate" in tools.RUN["called"]:
            return False, f"The yearly cash total from benefit_estimate is ₹{total:,}. Quote that number, do not add it up yourself."
    verdicts = {r["short"].lower(): r["verdict"] for r in tools.RUN["results"]}
    for sentence in re.split(r"(?<=[.!?\n])\s+", text):
        low = sentence.lower()
        for short, verdict in verdicts.items():
            if not re.search(rf"(?<![\w-]){re.escape(short)}(?![\w-])", low):
                continue
            if verdict == "not_eligible" and POS.search(sentence) and not NEG.search(sentence):
                return False, f"The rule engine says the person is NOT eligible for {short.upper()}. Do not say they qualify."
            if verdict == "eligible" and NEG.search(sentence):
                return False, f"The rule engine says the person IS eligible for {short.upper()}. Do not say they are not."
    return True, text


def guardrail(output):
    tools.RUN["last_raw"] = output.raw
    ok, value = check_answer(output.raw)
    if not ok:
        tools.RUN["retries"] = tools.RUN.get("retries", 0) + 1
        log.event(tools.RUN["run_id"], "guardrail_retry", "answer", value + "\n---\n" + output.raw[:1500])
    return ok, value


def build(question: str, profile: dict, language: str, llm) -> Crew:
    agent = Agent(
        role="SchemeSathi, a government-scheme guide for Indian citizens",
        goal="Tell a person, truthfully and with sources, which central government schemes they can get, "
             "how much they are worth, and exactly how to apply.",
        backstory="You help people who are often first-time applicants: farmers, street vendors, widows, students, "
                  "workers. You use plain words, short sentences and numbers in rupees. You never guess: "
                  "eligibility comes from the check_eligibility tool and facts come from official scheme text.",
        tools=tools.TOOLS,
        llm=llm,
        max_iter=8,
        max_retry_limit=0,                # on a rate limit, move to the next model instead of waiting
        allow_delegation=False,
        verbose=False,
    )
    lang = "Hindi (Devanagari script; keep scheme names and citation tags in English)" if language == "hi" else "English"
    task = Task(
        description=(
            f"PERSON'S PROFILE: {_profile_text(profile)}\n"
            f"QUESTION: {question}\n\n"
            "How to work:\n"
            "1. If the question is about what this person can get, call check_eligibility first. Its verdicts are "
            "final: 'eligible', 'likely' (needs one more thing confirmed) or 'not_eligible'. Never change one.\n"
            "2. For facts (amounts, documents, steps, rules) call search_schemes or scheme_section. For a document "
            "list across schemes call document_checklist. For money questions call benefit_estimate.\n"
            "3. Talk only about schemes the tools return. If nothing fits, say so honestly and suggest myscheme.gov.in.\n"
            "4. Put a citation tag after every fact, copied exactly from a tool result, e.g. [PM-KISAN · Benefits]. "
            "Never write a tag no tool returned.\n"
            "5. If the profile is missing something that decides a verdict, say what to confirm. Mention schemes under "
            "'only_if_this_applies' in one line at most; skip 'not_your_goal' unless asked.\n"
            "6. For money, quote yearly_cash_total from benefit_estimate exactly; do not add numbers yourself.\n"
            f"Answer in {lang}. Use short headings and bullets, no tables, at most about 250 words. End with the next step the "
            "person should take (where to apply)."
        ),
        expected_output="A short, friendly answer with citation tags after facts.",
        agent=agent,
        guardrail=guardrail,
        guardrail_max_retries=2,
    )
    return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)


def _strip_bad_citations(text: str) -> str:
    """Last resort after the retries: remove any tag no tool returned, rather than show a fake source."""
    allowed = tools.RUN["citations"]
    return CITE.sub(lambda m: m.group(0) if f"[{m.group(1).strip()} · {m.group(2).strip()}]" in allowed else "", text)


def ask(question: str, profile: dict | None = None, language: str = "en", emit=print) -> dict:
    t0 = time.time()
    run_id = log.start(question, language)
    tools.reset(run_id, profile or {})
    tools.RUN["retries"] = 0
    answer, used, last_error, verified = None, None, None, True
    tools.RUN["last_raw"] = None
    for model in model_chain():
        for attempt in (1, 2):
            emit(f"Thinking with {model.split('/')[-1]}" + (" (retry)" if attempt == 2 else ""))
            try:
                answer = build(question, profile or {}, language, make_llm(model)).kickoff().raw
                used = model
                break
            except Exception as exc:  # noqa: BLE001
                last_error = f"{type(exc).__name__}: {exc}"
                if "guardrail" in str(exc).lower() and tools.RUN.get("last_raw"):
                    # The model kept breaking a rule. Keep its last answer, remove unverified citations, flag it.
                    answer, used, verified = tools.RUN["last_raw"], model, False
                    log.event(run_id, "guardrail_exhausted", model, last_error[:500])
                    break
                log.event(run_id, "llm_fallback", model, last_error[:500])
                emit(f"{model.split('/')[-1]} unavailable ({'daily limit reached' if 'rate_limit' in str(exc) else type(exc).__name__}), trying the next model")
                if attempt == 1 and "tool_use_failed" in str(exc):
                    continue                     # a malformed tool call is a one-off slip: retry once
                break
        if answer is not None:
            break
    if answer is None:
        log.finish(run_id, status="failed", seconds=time.time() - t0, answer=last_error)
        raise RuntimeError(f"No model could answer. Last error: {last_error}")
    answer = _strip_bad_citations(normalize(answer))
    seconds = round(time.time() - t0, 1)
    log.finish(run_id, status="ok" if verified else "unverified", model=used, seconds=seconds, retries=tools.RUN["retries"], answer=answer)
    cited = sorted({f"[{a.strip()} · {b.strip()}]" for a, b in CITE.findall(answer)})
    sources = []
    for c in cited:
        short = c[1:].split(" · ")[0]
        slug = next((s for s, v in BY_SLUG.items() if v.short == short), None)
        sources.append({"citation": c, "url": f"https://www.myscheme.gov.in/schemes/{slug}" if slug else None})
    return {"answer": answer, "citations": sources, "model": used, "seconds": seconds,
            "retries": tools.RUN["retries"], "run_id": run_id, "verified": verified, "tools": list(tools.RUN["called"])}
