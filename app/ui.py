"""SchemeSathi's look: warm paper, deep indigo ink, saffron and leaf-green accents, serif headings."""
import html

import streamlit as st

INK, SAFFRON, GREEN, AMBER, RED = "#1F2A44", "#E07A2E", "#1E8C5A", "#C98A12", "#B4473A"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Inter:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;600&display=swap');
:root { --ink:#1F2A44; --muted:#5E6678; --paper:#FBF7F0; --card:#FFFFFF; --line:#EADFCF;
        --saffron:#E07A2E; --saffron-soft:#FCEBDD; --green:#1E8C5A; --green-soft:#E3F3EA;
        --amber:#C98A12; --amber-soft:#FBF0D6; --red:#B4473A; --red-soft:#F7E3E0; --indigo-soft:#E8EBF4; }
html, body, [class*="css"], .stMarkdown, .stText, p, li, label, input, textarea, button {
  font-family: 'Inter', 'Noto Sans Devanagari', system-ui, sans-serif; }
.stApp { background: var(--paper); color: var(--ink); }
h1, h2, h3, .serif { font-family: 'Fraunces', Georgia, serif !important; color: var(--ink); letter-spacing: -0.01em; }
section[data-testid="stSidebar"] { background: #F4EDE1; border-right: 1px solid var(--line); }
section[data-testid="stSidebar"] h3 { font-size: 1.05rem; margin-top: .4rem; }
.block-container { padding-top: 3.2rem; max-width: 1240px; }
div[data-testid="stTabs"] button[role="tab"] { font-weight: 600; color: var(--muted); }
div[data-testid="stTabs"] button[aria-selected="true"] { color: var(--ink); }
div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] { background: var(--saffron); }

/* hero */
.hero { margin-top: 14px; position: relative; overflow: hidden; border-radius: 22px; padding: 30px 34px 26px;
        background: radial-gradient(1200px 300px at 0% 0%, #2B3A63 0%, #1F2A44 55%, #172036 100%); color: #FFF; }
.hero:after { content:""; position:absolute; right:-60px; top:-60px; width:260px; height:260px; border-radius:50%;
              background: radial-gradient(circle, rgba(224,122,46,.55), rgba(224,122,46,0) 70%); }
.hero .eyebrow { font-size: .78rem; letter-spacing: .14em; text-transform: uppercase; color: #F6C9A5; font-weight: 600; }
.hero h1 { color: #FFF; font-size: 2.35rem; margin: .25rem 0 .2rem; line-height: 1.12; }
.hero .hi { font-family: 'Noto Sans Devanagari', sans-serif; color: #F6C9A5; font-size: 1.02rem; }
.hero p { color: #D6DCEC; max-width: 760px; margin: .55rem 0 0; font-size: .98rem; }
.chips { display:flex; gap:8px; flex-wrap:wrap; margin-top: 16px; }
.chip { background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.18); color: #F3F5FA;
        padding: 5px 12px; border-radius: 999px; font-size: .8rem; }
.chip b { color: #FFF; }

/* KPI tiles */
.kpis { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 12px; margin: 18px 0 6px; }
.kpi { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 14px 16px; }
.kpi .label { font-size: .76rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; font-weight: 600; }
.kpi .value { font-family: 'Fraunces', serif; font-size: 2rem; font-weight: 700; line-height: 1.1; margin-top: 4px; }
.kpi .sub { font-size: .8rem; color: var(--muted); }
.kpi.green .value { color: var(--green); } .kpi.amber .value { color: var(--amber); }
.kpi.saffron .value { color: var(--saffron); } .kpi.ink .value { color: var(--ink); }

/* scheme cards */
.grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); gap: 14px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 16px 18px 14px;
        border-top: 5px solid var(--line); display:flex; flex-direction:column; gap: 6px; }
.card.eligible { border-top-color: var(--green); } .card.likely { border-top-color: var(--amber); }
.card.not_eligible { border-top-color: var(--red); } .card.other { border-top-color: #9AA3B5; }
.card .top { display:flex; justify-content:space-between; align-items:center; }
.badge { font-size: .72rem; font-weight: 700; padding: 3px 10px; border-radius: 999px; letter-spacing: .02em; }
.badge.eligible { background: var(--green-soft); color: var(--green); }
.badge.likely { background: var(--amber-soft); color: #8C600B; }
.badge.not_eligible { background: var(--red-soft); color: var(--red); }
.badge.other { background: var(--indigo-soft); color: var(--ink); }
.group { font-size: .72rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }
.card h4 { font-family: 'Fraunces', serif; font-size: 1.28rem; margin: 2px 0 0; color: var(--ink); }
.card .full { font-size: .82rem; color: var(--muted); margin-top: -4px; }
.card .value { font-weight: 700; color: var(--saffron); font-size: 1.02rem; }
.card .benefit { font-size: .88rem; color: #333B4F; }
.checks { list-style:none; padding:0; margin: 4px 0 0; font-size: .84rem; }
.checks li { padding: 2px 0; display:flex; gap: 7px; align-items: baseline; }
.checks .ic { width: 16px; flex: none; text-align:center; font-weight:700; }
.checks .ok .ic { color: var(--green); } .checks .no .ic { color: var(--red); } .checks .q .ic { color: var(--amber); }
.checks .no { color: var(--red); font-weight: 600; }
.checks .quote { display:block; color: var(--muted); font-size: .76rem; font-style: italic; margin-left: 23px; }
.confirm { background: var(--amber-soft); border-radius: 10px; padding: 7px 10px; font-size: .8rem; color: #6B4A08; }
.card a.src { font-size: .8rem; color: var(--ink); font-weight: 600; text-decoration: none; margin-top: auto;
              border-top: 1px dashed var(--line); padding-top: 8px; }
.card a.src:hover { color: var(--saffron); }

/* chat + citations */
.cite { display:inline-block; background: var(--indigo-soft); color: var(--ink); border-radius: 8px; padding: 3px 9px;
        margin: 3px 6px 0 0; font-size: .78rem; font-weight: 600; text-decoration:none; }
.cite:hover { background: var(--saffron-soft); color: var(--saffron); }
.meta { font-size: .76rem; color: var(--muted); margin-top: 6px; }
.trace { font-family: ui-monospace, Menlo, monospace; font-size: .78rem; color: var(--muted); }

/* documents */
.doc { display:flex; justify-content:space-between; gap: 12px; background: var(--card); border:1px solid var(--line);
       border-radius: 12px; padding: 10px 14px; margin-bottom: 8px; }
.doc .name { font-weight: 600; } .doc .for { font-size: .78rem; color: var(--muted); }
.count { font-family:'Fraunces',serif; font-weight:700; color: var(--saffron); font-size: 1.3rem; min-width: 34px; text-align:right; }
.passage { background: var(--card); border: 1px solid var(--line); border-left: 4px solid var(--saffron);
           border-radius: 12px; padding: 12px 14px; margin-bottom: 10px; font-size: .88rem; white-space: pre-wrap; }
.note { font-size: .82rem; color: var(--muted); }
.section-title { font-family: 'Fraunces', serif; font-size: 1.35rem; font-weight: 700; margin: 18px 0 8px; }
@media (max-width: 900px) { .kpis { grid-template-columns: repeat(2, minmax(0,1fr)); } .hero h1 { font-size: 1.8rem; } }
</style>
"""


def esc(x) -> str:
    return html.escape(str(x or ""))


def inject():
    st.html(CSS)


def hero(n_schemes: int, n_passages: int):
    st.html(f"""
    <div class="hero">
      <div class="eyebrow">SchemeSathi · AI agent for India's welfare schemes</div>
      <h1>Every government scheme you are owed,<br>with the official proof.</h1>
      <div class="hi">आपकी हक़ की हर सरकारी योजना — सरकारी स्रोत के साथ</div>
      <p>Tell us about yourself once. SchemeSathi checks you against the official rules of {n_schemes} central schemes,
         explains every yes and no, adds up the money, and builds one document list. Every fact links to myScheme.</p>
      <div class="chips"><span class="chip"><b>{n_schemes}</b> schemes</span>
        <span class="chip"><b>{n_passages}</b> official passages indexed</span>
        <span class="chip">Verdicts by <b>rules</b>, not guesses</span>
        <span class="chip">English · <b>हिन्दी</b></span></div>
    </div>""")


def kpis(items):
    """items: list of (label, value, sub, color)."""
    tiles = "".join(f'<div class="kpi {c}"><div class="label">{esc(l)}</div><div class="value">{esc(v)}</div>'
                    f'<div class="sub">{esc(s)}</div></div>' for l, v, s, c in items)
    st.html(f'<div class="kpis">{tiles}</div>')


BADGE = {"eligible": "✓ Eligible", "likely": "◐ Likely — confirm", "not_eligible": "✕ Not eligible", "other": "○ Only if"}


def card(r: dict, kind: str | None = None) -> str:
    kind = kind or r["verdict"]
    checks = "".join(f'<li class="ok"><span class="ic">✓</span><span>{esc(c["label"])}</span></li>' for c in r["passed"])
    checks += "".join(f'<li class="no"><span class="ic">✕</span><span>{esc(c["label"])}'
                      f'<span class="quote">“{esc(c["quote"])}”</span></span></li>' for c in r["failed"])
    checks += "".join(f'<li class="q"><span class="ic">?</span><span>{esc(c["label"])}</span></li>' for c in r["unknown"])
    confirm = (f'<div class="confirm"><b>Confirm at the office:</b> {esc("; ".join(r["confirm"]))}</div>'
               if r["confirm"] and kind != "not_eligible" else "")
    if kind == "other" and r.get("only_if"):
        confirm = f'<div class="confirm"><b>Only if:</b> {esc(", ".join(r["only_if"]).lower())}</div>'
    value = f'<div class="value">{esc(r["value_note"])}</div>' if r["value_note"] else ""
    return f"""<div class="card {kind}"><div class="top"><span class="badge {kind}">{BADGE[kind]}</span>
      <span class="group">{esc(r["group"])}</span></div><h4>{esc(r["short"])}</h4><div class="full">{esc(r["name"])}</div>
      {value}<div class="benefit">{esc(r["benefit"])}</div><ul class="checks">{checks}</ul>{confirm}
      <a class="src" href="{esc(r["url"])}" target="_blank">Official page on myScheme ↗</a></div>"""


def grid(cards: list[str]):
    st.html(f'<div class="grid">{"".join(cards)}</div>')


def citations(sources: list[dict]):
    if sources:
        st.html("".join(f'<a class="cite" href="{esc(s["url"])}" target="_blank">{esc(s["citation"][1:-1])} ↗</a>'
                        for s in sources))


def section_title(text: str):
    st.html(f'<div class="section-title">{esc(text)}</div>')
