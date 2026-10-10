"""SchemeSathi web app:  streamlit run app/streamlit_app.py"""
import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ui  # noqa: E402
from schemesathi import config, log, rag  # noqa: E402
from schemesathi.personas import BY_ID, PERSONAS  # noqa: E402
from schemesathi.rules import GOALS, SCHEMES, evaluate, summary  # noqa: E402

st.set_page_config(page_title="SchemeSathi · योजना साथी", page_icon="🪔", layout="wide")
ui.inject()

STATES = ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Delhi", "Goa", "Gujarat", "Haryana",
          "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Madhya Pradesh",
          "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan",
          "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Other UT"]
OCCUPATIONS = {"farmer": "Farmer (own or tenant)", "farm_labourer": "Farm labourer", "street_vendor": "Street vendor",
               "artisan": "Artisan / craftsperson", "unorganised_worker": "Daily-wage / domestic / gig worker",
               "entrepreneur": "Small business owner", "salaried": "Salaried job", "student": "Student",
               "unemployed": "Looking for work", "homemaker": "Homemaker", "retired": "Retired"}
LEVELS = {"none": "Not studying", "class_11_12": "Class 11–12", "diploma": "Diploma / ITI",
          "undergraduate": "Undergraduate", "postgraduate": "Postgraduate"}
SITUATIONS = {"pregnant": "Pregnant", "first_child": "First child", "widow": "Widow", "disability": "Living with a disability",
              "tb_patient": "In TB treatment", "hospitalised_govt": "Treated in a govt hospital",
              "has_course_admission": "Admitted to a course"}
FLAGS = {"has_aadhaar": "Has Aadhaar", "has_bank_account": "Has a bank account", "bpl": "BPL / ration card household",
         "owns_pucca_house": "Owns a pucca house", "has_lpg_connection": "Has an LPG connection",
         "income_tax_payer": "Pays income tax", "govt_employee": "Family member in govt job",
         "formal_social_security": "In EPFO / ESIC / NPS"}

DEFAULT = BY_ID["ramesh"]["profile"]


# ---------- profile state ----------------------------------------------------------------------------------
def load(profile: dict):
    p = profile
    ss = st.session_state
    ss.age, ss.gender, ss.area = p.get("age", 30), p.get("gender", "female"), p.get("area", "rural")
    ss.state_, ss.category = p.get("state", "Uttar Pradesh"), p.get("category", "General")
    ss.occupation = p.get("occupation", "farmer")
    ss.family_income, ss.monthly_income = p.get("annual_family_income", 100000), p.get("monthly_income", 8000)
    ss.flags = [k for k in FLAGS if p.get(k)]
    ss.situations = [k for k in SITUATIONS if k != "disability" and p.get(k)] + \
                    (["disability"] if (p.get("disability_percent") or 0) > 0 else [])
    ss.disability = p.get("disability_percent") or 40
    ss.land_own, ss.land_ha = bool(p.get("land_in_own_name")), float(p.get("land_hectares") or 1.0)
    ss.level = p.get("student_level") or "none"
    ss.top20, ss.other_sch = bool(p.get("class12_top20")), bool(p.get("other_scholarship"))
    ss.defaulter, ss.prior_loan = bool(p.get("loan_defaulter")), bool(p.get("prior_govt_business_loan"))
    ss.goals = list(p.get("goals") or [])


def profile() -> dict:
    ss = st.session_state
    sit = set(ss.situations)
    p = {"age": ss.age, "gender": ss.gender, "area": ss.area, "state": ss.state_, "category": ss.category,
         "occupation": ss.occupation, "annual_family_income": ss.family_income, "monthly_income": ss.monthly_income,
         **{k: k in ss.flags for k in FLAGS},
         **{k: k in sit for k in SITUATIONS if k != "disability"},
         "disability_percent": ss.disability if "disability" in sit else 0,
         "loan_defaulter": ss.defaulter, "prior_govt_business_loan": ss.prior_loan,
         "other_scholarship": ss.other_sch, "goals": ss.goals}
    if ss.occupation == "farmer":
        p.update(land_in_own_name=ss.land_own, land_hectares=ss.land_ha)
    else:
        p.update(land_in_own_name=False, land_hectares=0)
    if ss.level != "none":
        p.update(student_level=ss.level, class12_top20=ss.top20)
    return p


def pick_persona():
    choice = st.session_state.get("persona")
    if choice:
        load(BY_ID[choice]["profile"])


if "age" not in st.session_state:
    load(DEFAULT)
    st.session_state.persona = "ramesh"

# ---------- sidebar: the profile ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🪔 Try a person")
    st.pills("persona", [p["id"] for p in PERSONAS], key="persona", on_change=pick_persona, label_visibility="collapsed",
             format_func=lambda i: f'{BY_ID[i]["emoji"]} {BY_ID[i]["name"]}')
    if st.session_state.get("persona"):
        st.caption(BY_ID[st.session_state.persona]["tagline"] + " — edit anything below.")
    st.markdown("### About you")
    c1, c2 = st.columns(2)
    c1.number_input("Age", 0, 100, key="age")
    c2.selectbox("Gender", ["female", "male", "other"], key="gender", format_func=str.title)
    c1.selectbox("Category", ["General", "OBC", "EBC", "DNT", "SC", "ST"], key="category")
    c2.selectbox("State", STATES, key="state_")
    st.segmented_control("Lives in", ["rural", "urban"], key="area", format_func=lambda x: "Village" if x == "rural" else "Town / city")
    st.markdown("### Work and money")
    st.selectbox("Main occupation", list(OCCUPATIONS), key="occupation", format_func=OCCUPATIONS.get)
    c1, c2 = st.columns(2)
    c1.number_input("Family income / year (₹)", 0, 10_000_000, step=10_000, key="family_income")
    c2.number_input("Your income / month (₹)", 0, 1_000_000, step=1_000, key="monthly_income")
    if st.session_state.occupation == "farmer":
        c1, c2 = st.columns(2)
        c1.toggle("Land in my name", key="land_own")
        c2.number_input("Land (hectares)", 0.0, 100.0, step=0.1, key="land_ha")
    st.pills("Tick what is true", list(FLAGS), key="flags", selection_mode="multi", format_func=FLAGS.get)
    st.markdown("### Life right now")
    st.pills("Situations", list(SITUATIONS), key="situations", selection_mode="multi", format_func=SITUATIONS.get,
             label_visibility="collapsed")
    if "disability" in st.session_state.situations:
        st.slider("Disability (%)", 0, 100, key="disability")
    st.selectbox("Studying", list(LEVELS), key="level", format_func=LEVELS.get)
    if st.session_state.level != "none":
        c1, c2 = st.columns(2)
        c1.toggle("Top 20% in Class 12", key="top20")
        c2.toggle("Already on a scholarship", key="other_sch")
    st.markdown("### What do you need?")
    st.pills("Goals", list(GOALS), key="goals", selection_mode="multi", format_func=GOALS.get, label_visibility="collapsed")
    if "business" in st.session_state.goals:
        c1, c2 = st.columns(2)
        c1.toggle("Ever defaulted on a loan", key="defaulter")
        c2.toggle("Govt business loan in last 5 yrs", key="prior_loan")
    st.caption("Nothing you enter leaves this computer except the question you ask the AI.")

P = profile()
results = evaluate(P)
S = summary(results)
fits = [r for r in results if r["relevant"] and r["verdict"] != "not_eligible"]


@st.cache_data(show_spinner=False)
def passages() -> int:
    try:
        return rag.collection().count()
    except Exception:  # noqa: BLE001
        return 0


ui.hero(len(SCHEMES), passages())
ui.kpis([("Eligible now", S["eligible"], "every rule passed", "green"),
         ("Likely", S["likely"], "one thing to confirm", "amber"),
         ("Cash you could receive", f'₹{S["yearly_cash"]:,}', "a year, where the official text gives an amount", "saffron"),
         ("Documents to gather", len(rag.documents([r["slug"] for r in fits])), "for all fitting schemes", "ink")])

tab_fit, tab_ask, tab_docs, tab_explore, tab_hood = st.tabs(
    ["🎯 Your schemes", "💬 Ask SchemeSathi", "📋 Document checklist", "🔎 Explore all schemes", "⚙️ Under the hood"])

# ---------- tab 1: verdict cards ---------------------------------------------------------------------------
with tab_fit:
    view = st.segmented_control("Show", ["Fits you", "Not eligible (and why)", "Only if your situation changes"],
                                default="Fits you", key="view", label_visibility="collapsed")
    if view == "Fits you":
        goals = set(P["goals"])
        mine = [r for r in fits if r["goal"] in goals] if goals else fits
        rest = [r for r in fits if r not in mine]
        if not fits:
            st.info("No scheme fits this profile yet. Try adding your goals or checking your details.")
        if mine:
            ui.section_title(f"For what you need · {len(mine)}" if goals else f"Schemes that fit you · {len(mine)}")
            ui.grid([ui.card(r) for r in mine])
        if rest:
            ui.section_title(f"Also open to you · {len(rest)}")
            ui.grid([ui.card(r) for r in rest])
        if fits:
            df = pd.DataFrame([{"Scheme": r["short"], "₹ a year": r["yearly_value"] or 0, "Verdict": r["verdict"]}
                               for r in fits if r["yearly_value"]])
            if not df.empty:
                ui.section_title("Where the yearly cash comes from")
                fig = px.bar(df.sort_values("₹ a year"), x="₹ a year", y="Scheme", orientation="h", color="Verdict",
                             color_discrete_map={"eligible": ui.GREEN, "likely": ui.AMBER}, text="₹ a year")
                fig.update_traces(texttemplate="₹%{x:,}", textposition="outside", cliponaxis=False)
                fig.update_layout(height=80 + 46 * len(df), margin=dict(l=0, r=40, t=10, b=0), plot_bgcolor="rgba(0,0,0,0)",
                                  paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter", color=ui.INK), legend_title="")
                st.plotly_chart(fig, width="stretch")
    elif view.startswith("Not eligible"):
        no = [r for r in results if r["verdict"] == "not_eligible"]
        st.caption("The red line is the official rule you do not meet, quoted from the scheme's eligibility text.")
        ui.grid([ui.card(r) for r in no])
    else:
        other = [r for r in results if r["verdict"] != "not_eligible" and not r["relevant"]]
        st.caption("These depend on a life situation or a goal you have not selected. They appear here, not in your count.")
        ui.grid([ui.card(r, "other") for r in other])

# ---------- tab 2: the agent -------------------------------------------------------------------------------
with tab_ask:
    left, right = st.columns([3, 1])
    with right:
        lang = st.segmented_control("Answer in", ["en", "hi"], default="en", key="lang",
                                    format_func=lambda x: "English" if x == "en" else "हिन्दी")
        st.markdown("**Try asking**")
        samples = ["Which schemes should I apply for first, and how much money is that?",
                   "What documents do I need, and where do I apply?",
                   "Why am I not eligible for PM-KISAN?",
                   "मुझे पेंशन के लिए कौन सी योजना मिल सकती है?"]
        for q in samples:
            if st.button(q, width="stretch", key=f"s_{hash(q)}"):
                st.session_state.pending = q
    with left:
        st.session_state.setdefault("chat", [])
        for m in st.session_state.chat:
            with st.chat_message(m["role"], avatar="🙂" if m["role"] == "user" else "🪔"):
                st.markdown(m["content"])
                if m.get("sources"):
                    ui.citations(m["sources"])
                if m.get("meta"):
                    st.html(f'<div class="meta">{ui.esc(m["meta"])}</div>')
        question = st.chat_input("Ask about any scheme, in English or Hindi") or st.session_state.pop("pending", None)
        if question:
            st.session_state.chat.append({"role": "user", "content": question})
            with st.chat_message("user", avatar="🙂"):
                st.markdown(question)
            with st.chat_message("assistant", avatar="🪔"):
                with st.status("SchemeSathi is checking the official rules…", expanded=False) as status:
                    from schemesathi.agent import ask
                    try:
                        out = ask(question, P, lang or "en", emit=lambda msg: status.write(msg))
                        status.update(label=f"Done in {out['seconds']} s · tools used: {', '.join(dict.fromkeys(out['tools']))}",
                                      state="complete")
                    except Exception as exc:  # noqa: BLE001
                        out = None
                        status.update(label="Could not answer", state="error")
                        st.error(f"{exc}\n\nThe eligibility cards still work without the AI.")
                if out:
                    st.markdown(out["answer"])
                    ui.citations(out["citations"])
                    meta = (f'{out["model"].split("/")[-1]} · {out["seconds"]} s · '
                            f'{len(out["citations"])} official sources · guardrail retries: {out["retries"]}' +
                            ("" if out["verified"] else " · ⚠ not fully verified: check the official pages"))
                    st.html(f'<div class="meta">{ui.esc(meta)}</div>')
                    st.session_state.chat.append({"role": "assistant", "content": out["answer"],
                                                  "sources": out["citations"], "meta": meta})
        if not st.session_state.chat:
            st.caption("The agent sees the profile on the left, decides which tools to use, and must cite the official "
                       "text for every fact. It cannot change a verdict from the rule engine.")

# ---------- tab 3: documents -------------------------------------------------------------------------------
with tab_docs:
    names = {r["short"]: r["slug"] for r in results}
    chosen = st.multiselect("Schemes to apply for", list(names), default=[r["short"] for r in fits])
    docs = rag.documents([names[c] for c in chosen])
    ui.section_title(f"{len(docs)} documents for {len(chosen)} schemes")
    st.caption("Common documents are merged, so you gather each one once. The number shows how many schemes need it.")
    c1, c2 = st.columns(2)
    for i, d in enumerate(docs):
        col = c1 if i % 2 == 0 else c2
        with col:
            st.html(f'<div class="doc"><div><div class="name">{ui.esc(d["document"])}</div>'
                    f'<div class="for">{ui.esc(", ".join(d["for"]))}</div></div><div class="count">{len(d["for"])}</div></div>')
    if docs:
        text = "SchemeSathi document checklist\n\n" + "\n".join(f"[ ] {d['document']}  ({', '.join(d['for'])})" for d in docs)
        st.download_button("Download checklist (.txt)", text, "schemesathi_checklist.txt")

# ---------- tab 4: explore ---------------------------------------------------------------------------------
with tab_explore:
    q = st.text_input("Search the official text of all schemes", placeholder="e.g. pension for a widow, loan without collateral")
    if q:
        for h in rag.search(q, k=5):
            st.html(f'<div class="passage"><a class="cite" href="{ui.esc(h["url"])}" target="_blank">'
                    f'{ui.esc(h["citation"][1:-1])} ↗</a> <span class="note">match {h["score"]:.2f}</span>\n\n'
                    f'{ui.esc(rag.plain(h["text"]))}</div>')
    ui.section_title("Read a scheme")
    by_short = {s.short: s for s in SCHEMES}
    pick = st.selectbox("Scheme", list(by_short), format_func=lambda x: f"{x} — {by_short[x].name}")
    s = by_short[pick]
    md = (config.SCHEMES_DIR / f"{s.slug}.md").read_text()
    secs = [x for x in rag.sections(md) if x[0] not in ("Sources And References",)]
    for name, tab in zip([n for n, _ in secs], st.tabs([n for n, _ in secs])):
        with tab:
            st.markdown(dict(secs)[name])
    st.caption(f"Source: https://www.myscheme.gov.in/schemes/{s.slug}")

# ---------- tab 5: under the hood --------------------------------------------------------------------------
with tab_hood:
    arch = config.ROOT / "docs" / "architecture.png"
    if arch.exists():
        st.image(str(arch), width="stretch")
    res_path = config.ROOT / "eval" / "results.json"
    if res_path.exists():
        R = json.loads(res_path.read_text())
        ui.section_title("Evaluation")
        ui.kpis([(k, v, s, c) for k, v, s, c in R.get("tiles", [])])
        if R.get("table"):
            st.dataframe(pd.DataFrame(R["table"]), width="stretch", hide_index=True)
    ui.section_title("Agent activity")
    runs = log.rows("select id, datetime(ts, 'unixepoch', 'localtime') as time, question, language, model, status, "
                    "seconds, retries from runs order by id desc limit 50")
    if runs:
        st.dataframe(pd.DataFrame(runs), width="stretch", hide_index=True)
        ev = pd.DataFrame(log.rows("select name, count(*) as calls, round(avg(ms)) as avg_ms from events "
                                   "where kind = 'tool_call' group by name order by calls desc"))
        if not ev.empty:
            fig = px.bar(ev, x="calls", y="name", orientation="h", color_discrete_sequence=[ui.SAFFRON], text="calls")
            fig.update_layout(height=260, margin=dict(l=0, r=20, t=10, b=0), plot_bgcolor="rgba(0,0,0,0)",
                              paper_bgcolor="rgba(0,0,0,0)", yaxis_title="", xaxis_title="tool calls")
            st.plotly_chart(fig, width="stretch")
    else:
        st.caption("No questions asked yet.")
