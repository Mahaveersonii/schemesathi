"""Draw docs/architecture.svg (hand-placed, so it stays tidy) and render docs/architecture.png with headless Chrome.

    python docs/make_architecture.py
"""
import subprocess
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent
W, H = 1600, 1060
INK, MUTED, PAPER, LINE = "#1F2A44", "#5E6678", "#FBF7F0", "#E3D6C2"
SAFFRON, GREEN, AMBER, RED, INDIGO = "#E07A2E", "#1E8C5A", "#C98A12", "#B4473A", "#3B4C7A"
FONT = "Inter, Helvetica, Arial, sans-serif"
SERIF = "Fraunces, Georgia, serif"

parts = []


def add(s):
    parts.append(s)


def text(x, y, s, size=15, weight=400, color=INK, anchor="start", family=FONT, italic=False):
    st = ' font-style="italic"' if italic else ""
    add(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{color}" '
        f'text-anchor="{anchor}"{st}>{escape(s)}</text>')


def box(x, y, w, h, fill="#FFFFFF", stroke=LINE, r=16, top=None, sw=1.5):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    if top:
        add(f'<path d="M{x},{y + r} a{r},{r} 0 0 1 {r},-{r} h{w - 2 * r} a{r},{r} 0 0 1 {r},{r} v-2 h-{w} z" fill="{top}"/>')
        add(f'<rect x="{x}" y="{y}" width="{w}" height="6" rx="3" fill="{top}"/>')


def pill(x, y, w, label, fill, color="#FFFFFF", size=13):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="28" rx="14" fill="{fill}"/>')
    text(x + w / 2, y + 19, label, size, 600, color, "middle")


def arrow(points, color=MUTED, label=None, lx=None, ly=None, dash=False):
    d = "M" + " L".join(f"{x},{y}" for x, y in points)
    da = ' stroke-dasharray="6 5"' if dash else ""
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.2"{da} marker-end="url(#a-{color[1:]})"/>')
    if label:
        tw = len(label) * 6.6 + 14
        add(f'<rect x="{lx - tw / 2}" y="{ly - 14}" width="{tw}" height="20" rx="10" fill="{PAPER}" stroke="{LINE}"/>')
        text(lx, ly + 1, label, 11.5, 600, color, "middle")


def lines(x, y, rows, size=13.5, gap=21, color=INK, weight=400):
    for i, r in enumerate(rows):
        text(x, y + i * gap, r, size, weight, color)


# canvas + markers
add(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')
markers = "".join(f'<marker id="a-{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                  f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
                  for c in (MUTED, SAFFRON, GREEN, INDIGO, RED, INK))
add(f"<defs>{markers}</defs>")

# title
text(40, 58, "SchemeSathi", 38, 700, INK, family=SERIF)
text(312, 58, "· architecture of a single-agent, rules-grounded RAG assistant", 20, 400, MUTED)
text(40, 88, "Mahaveer Soni (065089) · AABA – Agentic AI for Business Automation · FORE School of Management", 14, 500, MUTED)

# column headers
cols = [(40, "1  OFFICIAL SOURCE"), (390, "2  KNOWLEDGE (deterministic + retrieval)"),
        (820, "3  THE AGENT"), (1250, "4  PEOPLE AND PROOF")]
for x, label in cols:
    text(x, 132, label, 12.5, 700, SAFFRON)
    add(f'<line x1="{x}" y1="142" x2="{x + 310}" y2="142" stroke="{SAFFRON}" stroke-width="2"/>')

# 1. sources
box(40, 165, 310, 150, top=INDIGO)
text(60, 202, "myScheme.gov.in", 19, 700, INK, family=SERIF)
lines(60, 228, ["Government of India's scheme portal", "public API · robots.txt allows", "32 central schemes, 7 life areas"], 13, 20, MUTED)
box(40, 345, 310, 128)
text(60, 378, "scripts/fetch_schemes.py", 15, 700, INK)
lines(60, 402, ["1 request / second, polite user-agent", "raw JSON kept for traceability", "→ clean Markdown, 8 sections each"], 13, 20, MUTED)
box(40, 503, 310, 110, fill="#F4EDE1")
text(60, 536, "data/schemes/", 15, 700, INK)
lines(60, 560, ["32 × .json (raw)  +  32 × .md", "Benefits · Eligibility · Exclusions ·", "Application · Documents · FAQs"], 13, 20, MUTED)
arrow([(195, 315), (195, 343)], INDIGO)
arrow([(195, 473), (195, 501)], INDIGO)

# 2. knowledge: rules + library
box(390, 165, 390, 270, top=GREEN)
text(410, 202, "Rule engine", 20, 700, INK, family=SERIF)
text(560, 202, "rules.py", 13, 600, MUTED)
lines(410, 230, ["32 schemes · each check written from the", "official eligibility line (quote kept beside it)"], 13, 20, MUTED)
pill(410, 278, 108, "✓ eligible", GREEN)
pill(526, 278, 108, "◐ likely", AMBER)
pill(642, 278, 118, "✕ not eligible", RED)
lines(410, 336, ["unknown ≠ no  ·  goal-gated loans hidden", "life situations shown as “only if”", "verdicts are FINAL: the LLM cannot change them"], 13, 21, INK)

box(390, 465, 390, 250, top=SAFFRON)
text(410, 502, "Scheme library (RAG)", 20, 700, INK, family=SERIF)
text(640, 502, "rag.py", 13, 600, MUTED)
lines(410, 530, ["split by section → ≤900-char passages (150 overlap)",
                 "context header: scheme name · section",
                 "nomic-embed-text via Ollama (on this Mac)",
                 "ChromaDB · 522 passages · cosine"], 13, 21, MUTED)
pill(410, 628, 360, "score = 0.9 meaning + 0.1 keywords + intent boost", SAFFRON, "#FFFFFF", 12.5)
text(410, 690, "every passage carries a citation tag  [PM-KISAN · Benefits]", 12.5, 600, INK)

arrow([(350, 545), (370, 545), (370, 590), (388, 590)], SAFFRON, "index", 370, 620)
arrow([(350, 240), (388, 240)], GREEN, "quotes", 369, 228)

# 3. agent
box(820, 165, 400, 405, fill="#FFFFFF", stroke=INK, sw=2.2, top=INK)
text(840, 205, "SchemeSathi agent", 21, 700, INK, family=SERIF)
text(840, 230, "one CrewAI agent · plans its own tool calls (ReAct)", 13, 500, MUTED)
box(840, 248, 360, 58, fill="#E8EBF4", stroke="#E8EBF4", r=12)
text(856, 272, "LLM on Groq (free)  with automatic fallback", 13, 700, INK)
text(856, 293, "gpt-oss-120b  →  gpt-oss-20b  →  qwen3-27b", 13, 500, INDIGO)
text(840, 336, "FIVE TOOLS", 12, 700, SAFFRON)
tools_ = [("check_eligibility", GREEN, "rule engine verdicts + reasons"),
          ("benefit_estimate", GREEN, "yearly cash, one-time, future"),
          ("search_schemes", SAFFRON, "hybrid search, cited passages"),
          ("scheme_section", SAFFRON, "exact official section text"),
          ("document_checklist", SAFFRON, "merged list across schemes")]
for i, (name, c, desc) in enumerate(tools_):
    y = 350 + i * 40
    pill(840, y, 170, name, c, size=12.5)
    text(1022, y + 19, desc, 12.5, 500, MUTED)
text(840, 560, "answers in English or हिन्दी · plain words · rupees", 12.5, 600, INK)

box(820, 600, 400, 200, fill="#FFF6EF", stroke=RED, sw=2, top=RED)
text(840, 638, "Guardrail  (checked in code)", 19, 700, INK, family=SERIF)
lines(840, 666, ["• every citation must come from a tool this run",
                 "• no verdict may contradict the rule engine",
                 "• no schemes outside the official library",
                 "• cash total must equal benefit_estimate"], 13, 22, INK)
text(840, 766, "fail → reason sent back, retry ×2 → else answer flagged", 12.5, 600, RED)
text(840, 786, "“not fully verified” and unverified tags removed", 12.5, 600, RED)

arrow([(780, 300), (800, 300), (800, 385), (838, 385)], GREEN)
arrow([(780, 590), (800, 590), (800, 480), (838, 480)], SAFFRON)
arrow([(1020, 570), (1020, 598)], RED, "answer", 1060, 586)

# 4. people & proof
box(1250, 165, 310, 300, top=SAFFRON)
text(1270, 202, "Streamlit app", 20, 700, INK, family=SERIF)
lines(1270, 230, ["Profile in the sidebar (12 sample people)",
                  "🎯 Your schemes: verdict cards, why-not",
                  "💬 Ask: agent chat, citations link to source",
                  "📋 One merged document checklist",
                  "🔎 Explore: search all official text",
                  "⚙️ Under the hood: eval + activity"], 13, 22, INK)
pill(1270, 380, 270, "cards are instant: rules only, no AI", GREEN, size=12.5)
pill(1270, 418, 270, "AI only for questions → saves tokens", INDIGO, size=12.5)

box(1250, 495, 310, 130)
text(1270, 528, "Audit log", 17, 700, INK, family=SERIF)
text(1370, 528, "SQLite", 13, 600, MUTED)
lines(1270, 552, ["every run: question, model, seconds,", "retries · every tool call with timing", "every guardrail rejection with text"], 13, 20, MUTED)

box(1250, 655, 310, 145)
text(1270, 688, "Evaluation", 17, 700, INK, family=SERIF)
text(1385, 688, "eval/run_eval.py", 13, 600, MUTED)
lines(1270, 712, ["12 hand-labelled people × 32 schemes", "LLM-alone baseline vs rules", "24 retrieval questions: Hit@k, MRR",
                  "agent: time, retries, verified rate"], 13, 20, MUTED)

arrow([(1220, 700), (1236, 700), (1236, 330), (1248, 330)], INK, None)
text(1196, 330, "", 1)
arrow([(1220, 760), (1236, 760), (1236, 560), (1248, 560)], MUTED, None, dash=True)

# bottom: two paths
box(40, 850, 1520, 170, fill="#FFFFFF")
text(60, 886, "Two paths through the system", 19, 700, INK, family=SERIF)
steps1 = ["Person fills profile", "Rule engine runs 32 schemes", "Cards: ✓ ◐ ✕ with official quotes", "Cash total + document list"]
steps2 = ["Person asks a question", "Agent picks tools (ReAct)", "Cited answer drafted", "Guardrail checks it", "Answer + source links"]
text(60, 926, "Instant (no AI)", 13, 700, GREEN)
x = 200
for i, s in enumerate(steps1):
    w = len(s) * 7.3 + 30
    pill(x, 908, w, s, "#E3F3EA", GREEN, 12.5)
    if i < len(steps1) - 1:
        arrow([(x + w + 4, 922), (x + w + 26, 922)], GREEN)
    x += w + 32
text(60, 986, "Agent (AI)", 13, 700, INK)
x = 200
for i, s in enumerate(steps2):
    w = len(s) * 7.3 + 30
    pill(x, 968, w, s, "#E8EBF4", INK, 12.5)
    if i < len(steps2) - 1:
        arrow([(x + w + 4, 982), (x + w + 26, 982)], INK)
    x += w + 32
text(1540, 1046, "github.com/Mahaveersonii/schemesathi", 12.5, 600, MUTED, "end")

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
       + "".join(parts) + "</svg>")
(OUT / "architecture.svg").write_text(svg)
page = OUT / "_arch.html"
page.write_text('<html><head><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700&'
                'family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"><style>body{margin:0}</style></head>'
                f"<body>{svg}</body></html>")
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={W},{H}",
                "--force-device-scale-factor=2", "--virtual-time-budget=4000",
                f"--screenshot={OUT / 'architecture.png'}", page.as_uri()], check=True, capture_output=True)
page.unlink()
print("wrote", OUT / "architecture.svg", OUT / "architecture.png")
