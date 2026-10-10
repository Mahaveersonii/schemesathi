// Builds docs/report/SchemeSathi_Report_Mahaveer_Soni_065089.docx from the repo's results and images.
// node build_report.js   (needs the "docx" npm package)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType, HeadingLevel,
  LevelFormat, WidthType, ShadingType, BorderStyle, PageBreak, Header, Footer, PageNumber, TableOfContents,
  ExternalHyperlink, VerticalAlign, TabStopType,
} = require("docx");

const ROOT = path.resolve(__dirname, "..", "..");
const R = JSON.parse(fs.readFileSync(path.join(ROOT, "eval", "results.json"), "utf8"));
const REPO = "https://github.com/Mahaveersonii/schemesathi";
const INK = "1F2A44", SAFFRON = "E07A2E", GREEN = "1E8C5A", MUTED = "5E6678", SOFT = "F4EDE1", LINE = "D9CBB5";
const PAGE_W = 11906, MARGIN = 1300, CONTENT = PAGE_W - 2 * MARGIN; // A4

const pct = (x) => `${Math.round(x * 100)}%`;

// ---------- text helpers: **bold** and *italic* inside strings ----------
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}
const P = (text, o = {}) => new Paragraph({ children: runs(text, o.run || {}), spacing: { after: 140, line: 300 },
  alignment: o.align || AlignmentType.JUSTIFIED, ...o.para });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)], pageBreakBefore: true });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const B = (text, level = 0) => new Paragraph({ numbering: { reference: "bullets", level }, children: runs(text),
  spacing: { after: 70, line: 290 } });
const N = (text) => new Paragraph({ numbering: { reference: "steps", level: 0 }, children: runs(text),
  spacing: { after: 70, line: 290 } });
const Caption = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 220 },
  children: [new TextRun({ text: t, italics: true, size: 19, color: MUTED })] });
const Code = (t) => new Paragraph({ spacing: { after: 0, line: 260 }, shading: { type: ShadingType.CLEAR, fill: "F6F1E8" },
  children: [new TextRun({ text: t, font: "Consolas", size: 18, color: INK })] });

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
function Img(file, widthPt, caption) {
  const s = pngSize(file);
  const w = widthPt, h = Math.round((widthPt * s.h) / s.w);
  const items = [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: w, height: h },
      altText: { title: caption || "figure", description: caption || "figure", name: path.basename(file) } })] })];
  if (caption) items.push(Caption(caption));
  return items;
}

// ---------- tables ----------
const border = { style: BorderStyle.SINGLE, size: 4, color: LINE };
const borders = { top: border, bottom: border, left: border, right: border };
function Tbl(head, rows, widths, opts = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, i, isHead) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, borders,
    shading: { type: ShadingType.CLEAR, fill: isHead ? INK : (opts.zebra && opts._r % 2 ? "FBF7F0" : "FFFFFF") },
    margins: { top: 70, bottom: 70, left: 110, right: 110 }, verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ spacing: { after: 0, line: 260 }, children: runs(String(t),
      isHead ? { bold: true, color: "FFFFFF", size: 19 } : { size: 19 }) })],
  });
  const trs = [new TableRow({ tableHeader: true, children: head.map((t, i) => cell(t, i, true)) })];
  rows.forEach((r, k) => { opts._r = k; trs.push(new TableRow({ children: r.map((t, i) => cell(t, i, false)) })); });
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, rows: trs });
}
const gap = () => new Paragraph({ spacing: { after: 120 }, children: [] });

// ---------- numbers from the evaluation ----------
const base = R.baseline, rules = R.rules, ret = R.retrieval, ag = R.agent;
const bt = base.rows.reduce((a, r) => [a[0] + r.llm_tp, a[1] + r.llm_fp, a[2] + r.llm_fn], [0, 0, 0]);
const hyb = ret["hybrid + intent boost"], vec = ret["vector only"];
const hybKey = Object.keys(ret).find((k) => k.startsWith("hybrid ("));

// ---------- cover ----------
const logo = path.join(__dirname, "fore_logo.png");
const ls = pngSize(logo);
const cover = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600, after: 60 },
    children: [new TextRun({ text: "Agentic AI for Business Automation (AABA)", bold: true, size: 30, color: INK, font: "Cambria" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1500 },
    children: [new TextRun({ text: "PGDM-BDA, Term 04, 2026-27", size: 24, color: MUTED })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
    children: [new TextRun({ text: "Report on", italics: true, size: 26, color: MUTED, font: "Cambria" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: "SchemeSathi", bold: true, size: 64, color: INK, font: "Cambria" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1300 },
    children: [new TextRun({ text: "A Single-Agent, Rules-Grounded AI Assistant that Helps Citizens Find and Claim the Government Schemes They Are Entitled To",
      size: 28, color: SAFFRON, font: "Cambria" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 },
    children: [new TextRun({ text: "Submitted in partial fulfilment of the requirements for the Post Graduate Diploma in Management (PGDM)",
      italics: true, size: 22, color: INK })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 400, after: 1100 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(logo), transformation: { width: 300, height: Math.round(300 * ls.h / ls.w) },
      altText: { title: "FORE School of Management", description: "FORE School of Management logo", name: "fore_logo" } })] }),
  new Table({
    width: { size: CONTENT, type: WidthType.DXA }, columnWidths: [CONTENT / 2, CONTENT / 2],
    borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE },
      right: { style: BorderStyle.NONE }, insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE } },
    rows: [new TableRow({ children: [
      new TableCell({ width: { size: CONTENT / 2, type: WidthType.DXA }, borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
        children: [
          new Paragraph({ children: [new TextRun({ text: "Submitted to", bold: true, size: 24, color: SAFFRON })], spacing: { after: 80 } }),
          new Paragraph({ children: [new TextRun({ text: "Faculty Name: Prof. Shiva Botchu", size: 23 })] })] }),
      new TableCell({ width: { size: CONTENT / 2, type: WidthType.DXA }, borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
        children: [
          new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "Submitted by", bold: true, size: 24, color: SAFFRON })], spacing: { after: 80 } }),
          new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "Mahaveer Soni", size: 23 })] }),
          new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "Roll No. 065089", size: 23 })] })] }),
    ] })],
  }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1500, after: 60 },
    children: [new TextRun({ text: "FORE School of Management, New Delhi", bold: true, size: 22, color: INK })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({ text: "Individual Assignment · October 2026", size: 21, color: MUTED })] }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Code: ", size: 21, color: MUTED }),
      new ExternalHyperlink({ link: REPO, children: [new TextRun({ text: REPO, style: "Hyperlink", size: 21 })] })] }),
];

// ---------- body ----------
const S = path.join(ROOT, "docs", "screens");
const body = [
  new Paragraph({ children: [new TextRun({ text: "Contents", bold: true, size: 32, color: INK, font: "Cambria" })], spacing: { after: 200 } }),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  P("*Right-click the table and choose Update Field if page numbers are not shown.*", { run: { color: MUTED, size: 18 } }),

  H1("1. Executive Summary"),
  P("India runs hundreds of welfare schemes for farmers, workers, widows, students, pregnant women and people with disabilities. The benefits are real: cash every year, pensions, cheap insurance, collateral-free loans and free health care. But the people who most need them are the least able to find out which ones they qualify for, what the rules mean, which documents to carry and where to apply. A general-purpose chatbot looks like the obvious fix, but it guesses: in this project's tests an LLM working alone got eligibility wrong roughly one time in three."),
  P("**SchemeSathi** (\"scheme companion\") is a single AI agent built so that it cannot guess. A person fills in a short profile once. A **rule engine** checks them against the official eligibility rules of **32 central schemes** (95 checks, each with its official quote kept beside it) and returns *eligible*, *likely* or *not eligible* with the reason. For questions, **one CrewAI agent** plans its own calls to **five tools**: eligibility, benefit estimate, search over the official text, exact section lookup and a merged document checklist. It answers in English or Hindi. Facts come from a **retrieval (RAG) library** of 522 passages from myScheme, the Government of India portal. A **guardrail written in code** rejects any answer that:"),
  B("cites a source no tool returned;"),
  B("contradicts a rule-engine verdict;"),
  B("names a scheme or website that is not in the official text;"),
  B("states a cash total different from the computed one."),
  P(`On 12 hand-labelled people × 32 schemes, the rule engine matched the labels with **F1 = ${pct(rules.f1)}**. The same LLM answering alone scored **F1 = ${pct(base.f1)}**: it made ${bt[1]} wrong suggestions and missed ${bt[2]} schemes people qualified for. Retrieval finds the exact official section within the top three results for **${pct(hyb["hit@3"])}** of 24 test questions. In end-to-end runs, **${pct(ag.verified_rate)}** of agent answers passed every guardrail check. The whole system runs on free tiers: Groq for the LLM, and Ollama and ChromaDB on a laptop.`),
  P(`The code, data, tests and evaluation are public at ${REPO}.`),

  H1("2. The Problem"),
  H2("2.1 Benefits exist, but people do not reach them"),
  P("Government schemes are published, but they are written for administrators rather than citizens. Each scheme has its own eligibility rules (age bands, land in one's own name, income ceilings, BPL status, caste category, not being an income-tax payer, not being in EPFO), its own exclusions, its own document list and its own application route. A small farmer who wants to know what he can claim has to read dozens of guideline pages, many of them only in English. In practice people depend on word of mouth or on middlemen, and both miss schemes and sometimes charge for free services."),
  P("The Government's own myScheme portal brings scheme information into one place, which is a major step. It still leaves the person to read every scheme's rules and work out their own answer. The rules also interact: someone may be eligible for PM-KISAN, \"likely\" for crop insurance and ineligible for a pension scheme only because they are two years too old. SchemeSathi adds the missing layer: *apply the rules to me, explain the result, and tell me what to do next.*"),
  H2("2.2 Why a plain chatbot is not the answer"),
  P("An LLM can talk fluently about schemes, but it has three failure modes that matter more here than in most domains:"),
  B("**It guesses eligibility.** In this project's baseline (section 8.2) the model offered the old-age pension to a 34-year-old, the widow pension to a married street vendor, and PM-KISAN to a tenant farmer whose land is not in his name. It also forgot MGNREGA for almost every rural person."),
  B("**It invents details.** During development the agent wrote web addresses that do not exist (for example a made-up \"pradhanmantrijeevanjyotibima.gov.in\"), brought in schemes outside its library, and added up a yearly cash total that was more than eight times the real figure."),
  B("**It cannot show its source.** A citizen, a Common Service Centre operator or an NGO worker needs to be able to show the official line to a bank or a block office."),
  P("A wrong \"yes\" wastes a poor family's day and bus fare at an office. A wrong \"no\" quietly costs them money they are owed. So the design goal was not \"a better chatbot\" but **an agent whose every claim can be checked**."),
  H2("2.3 Who benefits"),
  Tbl(["User", "What SchemeSathi gives them"], [
    ["Citizens and families", "One profile, every scheme checked, the money added up, one document list, answers in Hindi"],
    ["Common Service Centre operators / village-level entrepreneurs", "A screening step that takes seconds per visitor instead of reading guidelines, with official quotes to show"],
    ["NGOs and self-help-group federations", "Bulk screening of members; reasons for each \"no\" to guide follow-up (for example getting land records corrected)"],
    ["Bank business correspondents and microfinance staff", "Quick checks for PMJJBY, PMSBY, APY, MUDRA and SVANidhi at the point of contact"],
    ["CSR teams and government departments", "An audit log of what was asked and answered, and evidence of which rules most often block people"],
  ], [3000, CONTENT - 3000], { zebra: true }),

  H1("3. Objectives"),
  N("Decide eligibility for 32 central schemes **deterministically**, with the official rule behind every \"yes\" and \"no\"."),
  N("Answer free-text questions in **English or Hindi** with an agent that chooses its own tools and **cites the official text** for every fact."),
  N("Make it **impossible for the LLM to overrule** an eligibility verdict or to cite something it did not retrieve."),
  N("Turn the result into action: **money per year**, a **merged document checklist** and **where to apply**."),
  N("**Measure** it against a hand-labelled test set and against the same LLM working alone."),
  N("Keep it **free and private**: free LLM tier, local embeddings, and no personal data stored beyond the question log."),

  H1("4. Why a Single Agent"),
  P("The assignment asked for a single-agent design, and this problem suits one. There is one user, one conversation and one decision to make: which tools to call to answer this question for this person. Splitting that across several agents (a \"researcher\", an \"eligibility officer\", a \"writer\") would add hand-offs where facts can be lost or rewritten, multiply token use on a free tier, and make it harder to say which component is responsible for a wrong answer."),
  P("SchemeSathi puts the intelligence in a **single reasoning loop** (CrewAI's ReAct-style agent: think, call a tool, read the result, decide again) and puts the **reliability in deterministic tools and a code guardrail**. That split is the main design idea of the project:"),
  Tbl(["Job", "Done by", "Why"], [
    ["Deciding who qualifies", "Rule engine (Python)", "Rules are exact; an LLM is not. Verdicts must be repeatable and explainable."],
    ["Finding facts", "Retrieval over official text", "Facts must come from the source, with a citation."],
    ["Choosing what to look up, explaining, translating", "The LLM agent", "This is where language understanding adds value."],
    ["Checking the answer", "Guardrail (Python)", "Self-checking by the same LLM is weak; code checks are not."],
  ], [2600, 2400, CONTENT - 5000], { zebra: true }),

  H1("5. System Architecture"),
  ...Img(path.join(ROOT, "docs", "architecture.png"), 600, "Figure 1. SchemeSathi architecture: official source → knowledge (rules + retrieval) → one agent with five tools and a guardrail → app, audit log and evaluation."),
  P("There are **two paths** through the system. The **instant path** uses no AI. As the person edits their profile, the rule engine re-evaluates all 32 schemes in milliseconds and the app shows verdict cards, the yearly cash and the document list. The **agent path** is used only when the person asks a question. The agent receives the profile and the question, calls tools, drafts an answer with citations, and the guardrail approves or rejects it. Because most value comes from the instant path, the LLM is called far less often, which matters on a free tier with a daily token limit."),

  H1("6. Component Design"),
  H2("6.1 Data pipeline: the official source"),
  P("myScheme renders scheme pages in the browser, but its public API returns the content as JSON, and its robots.txt allows crawling. `scripts/fetch_schemes.py` fetches the 32 schemes listed in `data/scheme_list.yaml` at one request per second with an identifying user-agent. It keeps the **raw JSON** for traceability and writes a **clean Markdown file** per scheme with fixed sections: Details, Benefits, Eligibility, Exclusions, Application Process, Documents Required, FAQs and References. Some schemes store their document list only as a rich-text tree rather than Markdown. The first version silently lost the documents for 12 schemes, so a converter for that format was added, and the Markdown can be rebuilt offline from the saved JSON (`--rebuild`)."),
  Tbl(["Life area", "Schemes"], [
    ["Farmers", "PM-KISAN, PM Kisan Maandhan, Kisan Credit Card, PM Fasal Bima"],
    ["Health and insurance", "Health Minister's Discretionary Grant, Nikshay Poshan (TB), PM Jeevan Jyoti Bima, PM Suraksha Bima"],
    ["Housing and household", "PMAY-Urban, PMAY-Gramin, PM Ujjwala (LPG), PM Jan Dhan"],
    ["Entrepreneurs and workers", "MUDRA, PM SVANidhi, Stand-Up India, PMEGP, PM Vishwakarma, PM Shram Yogi Maan-dhan, MGNREGA"],
    ["Pensions", "Atal Pension Yojana, Old Age (IGNOAPS), Widow (IGNWPS) and Disability (IGNDPS) pensions"],
    ["Women and children", "PM Matru Vandana, Janani Shishu Suraksha Karyakram, Janani Suraksha Yojana"],
    ["Students and youth", "Central Sector Scholarship, PM YASASVI, Post-Matric (Disability), NAPS apprenticeships, PMKVY, Skill Loan"],
  ], [2500, CONTENT - 2500], { zebra: true }),
  Caption("Table 1. The 32 central schemes covered, by life area."),

  H2("6.2 Rule engine"),
  P("`schemesathi/rules.py` describes each scheme as a list of **checks**. Each check is a plain-language label, a test on the profile, and the official sentence it comes from. A check answers *True*, *False* or *unknown* (the person has not said, or only an office can verify it). The verdict logic is deliberately simple and explainable:"),
  Tbl(["Verdict", "When", "Shown to the person as"], [
    ["Eligible", "Every check passed", "Green card, all reasons ticked"],
    ["Likely", "Nothing failed, but something is unknown or must be confirmed at the office (for example SECC listing, not being a practising professional)", "Amber card with \"Confirm at the office\""],
    ["Not eligible", "At least one check failed", "Red card with the failed rule and its official quote"],
  ], [1700, 4300, CONTENT - 6000], { zebra: true }),
  P("Three refinements came out of testing with realistic people:"),
  B("**Goal-gated schemes.** A business loan is not \"failed\" just because the person does not want a loan; it is shown separately as not their goal."),
  B("**Life situations.** A maternity scheme is not \"likely\" for someone who simply did not mention a pregnancy. Schemes that depend on pregnancy, widowhood, disability, TB treatment or studying appear under \"only if this applies to you\" and are not counted in the totals."),
  B("**Official-text corrections.** PM Kisan Maandhan needs the farmer's name in the land records. PM-SYM covers unorganised workers, not homemakers."),
  P("Money is stated **only where the official text gives an amount** (for example ₹6,000 a year for PM-KISAN). The widow pension's amount is set by each state and is not on myScheme, so SchemeSathi says exactly that rather than invent a figure."),

  H2("6.3 Scheme library (RAG)"),
  P("`schemesathi/rag.py` splits each scheme file by section, then into passages of at most 900 characters with 150 characters of overlap. Long paragraphs are cut at sentence ends. Each passage is embedded with a short header (\"scheme name (short name) · section\") so that a passage like \"the loan is repaid in 12 months\" still carries which scheme and section it belongs to. Embeddings use **nomic-embed-text through Ollama on the laptop** (free, and the text never leaves the machine), stored in **ChromaDB** with cosine distance: 522 passages in total."),
  P("Search blends three signals: **0.9 × meaning similarity + 0.1 × keyword overlap + a 0.05 boost** when the passage's section matches the question's intent. Intent comes from simple patterns: \"documents\" → Documents Required, \"how do I apply\" → Application Process, \"who can\" → Eligibility, \"how much\" → Benefits. Every passage is returned with a citation tag such as **[PM-KISAN · Benefits]** and a link to the scheme's myScheme page. The same module merges document lists across schemes, so \"Aadhaar Card\", \"Copy of Aadhaar\" and \"Aadhar card\" become one item with a count of how many schemes need it."),

  H2("6.4 The agent and its tools"),
  P("`schemesathi/agent.py` builds one CrewAI agent with the role of a government-scheme guide. Its instructions set the order of work: check eligibility first; use the search tools for facts; cite every fact with a tag a tool returned; quote the computed cash total; and never invent offices, websites or documents. The agent decides how many tool calls to make (at most 8 iterations). Its five tools (`schemesathi/tools.py`) each return short JSON, are timed and logged, and never crash the run:"),
  Tbl(["Tool", "What it returns", "Backed by"], [
    ["check_eligibility", "Schemes that fit (with what to confirm), schemes not eligible (with the failed rule), \"only if\" and off-goal schemes, plus citation tags", "Rule engine"],
    ["benefit_estimate", "Yearly cash total and each fitting scheme's value in words", "Rule engine"],
    ["search_schemes", "Top 4 official passages for a question, optionally within one scheme", "RAG library"],
    ["scheme_section", "Exact text of one section (Benefits, Eligibility, Exclusions, Application Process, Documents Required)", "Scheme files"],
    ["document_checklist", "One merged document list across several schemes, with citation tags", "Scheme files"],
  ], [2100, 4700, CONTENT - 6800], { zebra: true }),

  H2("6.5 The guardrail"),
  P("CrewAI lets a task carry a guardrail function that sees the agent's final answer. If the function rejects the answer, its reason is sent back and the agent tries again (up to two retries). SchemeSathi's guardrail is ordinary Python, so it is fast, free and cannot be talked out of its rules:"),
  Tbl(["Check", "Catches"], [
    ["Every citation tag was returned by a tool in this run", "Made-up sources"],
    ["No sentence calls a scheme eligible when the rules say not eligible, or the reverse", "The LLM overruling the rule engine"],
    ["Every scheme-like acronym is in the library or in the text the tools returned", "Schemes outside the library (it once described NPS with a wrong age rule)"],
    ["Every web address appears in the retrieved official text, or is myscheme.gov.in", "Invented websites"],
    ["A question about documents or applying must have used the matching tool", "Answers from memory"],
    ["A stated yearly total equals benefit_estimate's figure", "LLM arithmetic (it once claimed ₹53,600 instead of ₹6,000)"],
  ], [5000, CONTENT - 5000], { zebra: true }),
  P("Before checking, the answer is **normalised**. The model often writes 【PM‑KISAN · Benefits】 with Chinese brackets and non-breaking hyphens, which looks correct to a person but failed exact matching in the first version. If the retries run out, SchemeSathi does not throw the answer away. It keeps the last draft, removes any unverified citation, marks the answer *\"not fully verified\"* in the app, and logs the event."),

  H2("6.6 Model choice and fallback"),
  P("The agent runs on **Groq's free API**, which serves open-weight models very fast. The chain is **gpt-oss-120b → gpt-oss-20b → Qwen3**. If a model hits its daily token limit or fails, the agent moves to the next one immediately (CrewAI's internal waiting is switched off). A one-off malformed tool call gets one retry on the same model. Groq is reached through CrewAI's native OpenAI-compatible client, because the default path sends a field Groq rejects. On gpt-oss-20b a typical answer takes **2 to 15 seconds**; answers that needed guardrail retries took up to about 90 seconds."),

  H2("6.7 The app"),
  P("`app/streamlit_app.py` uses a warm civic design: paper background, deep indigo text, saffron and leaf-green accents, serif headings, and Devanagari support. Twelve sample people can be loaded with one click. The five tabs are: *Your schemes* (verdict cards, a \"not eligible and why\" view and an \"only if\" view), *Ask SchemeSathi* (agent chat with clickable source chips, the tools used, model, time and guardrail retries), *Document checklist* (merged, downloadable), *Explore* (search and read the official text) and *Under the hood* (architecture, evaluation and the agent's activity from the log)."),
  ...Img(path.join(S, "home.png"), 560, "Figure 2. Home: the profile on the left, the instant verdict cards and totals on the right (sample person: Ramesh, small farmer)."),
  ...Img(path.join(S, "why_not.png"), 560, "Figure 3. \"Not eligible (and why)\": the failed rule in red with its official quote."),
  ...Img(path.join(S, "chat.png"), 560, "Figure 4. The agent's answer, with tools used, citations linking to myScheme, model, time and guardrail retries."),
  ...Img(path.join(S, "documents.png"), 560, "Figure 5. One merged document checklist for nine schemes (sample person: Fatima, street vendor)."),

  H2("6.8 Audit log"),
  P("`schemesathi/log.py` writes every run (question, language, model, status, seconds, retries, answer) and every event (tool calls with arguments and timing, model fallbacks, guardrail rejections with the rejected text) to SQLite. This is what an organisation using SchemeSathi would need for accountability, and it is how most of the problems in section 9 were found."),

  H1("7. The Agent in Action"),
  P("A real run from the audit log shows the loop and the guardrail at work. Profile: Ramesh, 42, small farmer in Uttar Pradesh, 1.2 ha in his own name. Question: *\"Which schemes should I apply for first, and what documents do I need?\"*"),
  Code("1  gpt-oss-120b          → daily token limit reached, fall back"),
  Code("2  gpt-oss-20b  thinks   → call check_eligibility(scope='all')"),
  Code("3                        ← fits: KCC, PMJJBY, PMSBY, MGNREGA (eligible); PM-KISAN, PMFBY (likely)"),
  Code("4  drafts answer         → GUARDRAIL: 'www.pradhanmantrijeevanjyotibima.gov.in' is not in the"),
  Code("                           official text you retrieved. Remove it."),
  Code("5  thinks again          → call check_eligibility, document_checklist('KCC,PM-KISAN,PMFBY,...')"),
  Code("6  drafts answer         → GUARDRAIL: same invented address. Remove it."),
  Code("7  calls tools again     → third draft: citations real, no invented links, verdicts match → ACCEPTED"),
  Code("   89.8 s · 2 guardrail retries · 6 official sources"),
  gap(),
  P("The invented website looks plausible, and a person could easily have trusted it. That kind of error is why the guardrail is written in code rather than left to the model's judgement. The final answer lists the six fitting schemes with their verdicts, the merged documents and the next steps, each fact tagged to its official section."),

  H1("8. Evaluation"),
  H2("8.1 Method"),
  P("`eval/run_eval.py` runs four measurements and writes `eval/results.json`, which the app also displays."),
  B("**Eligibility.** 12 realistic people (farmer, widow, student, street vendor, pregnant woman, retired person, carpenter, salaried professional, person with 85% disability, domestic worker in TB treatment, a Class 12 student without a bank account, a tenant farmer). For each, the set of schemes they should be shown was written by hand from the official eligibility text: 12 × 32 = 384 decisions."),
  B("**LLM-alone baseline.** The same model the agent uses (gpt-oss-20b) gets the same profile and the list of 32 schemes, with no tools, and picks the schemes the person qualifies for."),
  B("**Retrieval.** 24 questions a person might ask, each with the scheme and section where the answer is. Measured: Hit@1, Hit@3, mean reciprocal rank (MRR), and whether the top result is at least the right scheme."),
  B("**Agent end to end.** Four people ask \"Which schemes can I get, how much money a year, and what should I do first?\". Measured: time, guardrail retries, verified answers, and whether all fitting schemes and no non-fitting schemes are mentioned."),
  H2("8.2 Eligibility: rules versus an LLM alone"),
  ...Img(path.join(__dirname, "chart_eligibility.png"), 470, `Figure 6. Precision, recall and F1 on 384 person-scheme decisions.`),
  P(`The rule engine matched the hand labels exactly (precision, recall and F1 all ${pct(rules.f1)}). The LLM alone scored precision ${pct(base.precision)}, recall ${pct(base.recall)} and F1 ${pct(base.f1)}: ${bt[0]} correct, **${bt[1]} wrong suggestions** and **${bt[2]} missed schemes**. Its mistakes are the kind that hurt real people:`),
  Tbl(["Person", "LLM wrongly said yes to", "LLM missed"],
    base.rows.filter((r) => r.llm_fp || r.llm_fn).map((r) => [r.persona, r.llm_wrong.join(", ") || "—", r.llm_missed.join(", ") || "—"]),
    [1500, 3900, CONTENT - 5400], { zebra: true }),
  Caption("Table 2. Every error the LLM made working alone (gpt-oss-20b)."),
  P("Patterns: the LLM handed out the **old-age pension (IGNOAPS) to people aged 34 to 42**, offered **PM-KISAN and PM-KMY to a tenant farmer** without land in his name, and **missed MGNREGA for most rural adults** and the low-cost insurance schemes PMJJBY and PMSBY for many people. The rule engine's perfect score needs one honest caveat: the labels and the rules were both written by the author from the same official text. Two rule errors (PM-KMY land records and PM-SYM homemakers) were found and fixed *while* writing the personas. The test shows that the engine applies the official rules consistently; an independent audit by a scheme officer would be the next step."),
  H2("8.3 Retrieval"),
  ...Img(path.join(__dirname, "chart_retrieval.png"), 470, "Figure 7. Retrieval variants on 24 questions."),
  Tbl(["Variant", "Hit@1", "Hit@3", "MRR", "Right scheme at #1"],
    Object.keys(ret).filter((k) => k !== "n").map((k) => [k, pct(ret[k]["hit@1"]), pct(ret[k]["hit@3"]), ret[k].mrr.toFixed(2), pct(ret[k]["scheme_hit@1"])]),
    [3600, 1300, 1300, 1300, CONTENT - 7500], { zebra: true }),
  Caption("Table 3. Exact-section retrieval and scheme-level accuracy."),
  P(`Pure vector search puts the right *scheme* first for ${pct(vec["scheme_hit@1"])} of questions, but often returns the scheme's Details or FAQ passage rather than the exact section. Adding keywords helps find the scheme but on its own lowers exact-section accuracy. The **intent boost** gives the best Hit@3 (${pct(hyb["hit@3"])}) and MRR (${hyb.mrr.toFixed(2)}), so it is the default. In practice the agent also has scheme_section for exact lookups, which makes the agent less dependent on the top-1 result. The weights were tuned on these same 24 questions, so the numbers are optimistic; a separate held-out set would be needed for a fair estimate.`),
  H2("8.4 Agent end to end"),
  Tbl(["Person", "Model", "Seconds", "Guardrail retries", "Verified", "Citations", "Fitting schemes mentioned", "Wrong schemes mentioned"],
    ag.rows.map((r) => [r.persona, r.model, r.seconds, r.retries, r.verified ? "Yes" : "No", r.citations, r.fitting_mentioned, r.non_fitting_mentioned.join(", ") || "none"]),
    [1050, 1250, 950, 1050, 950, 1000, 1500, CONTENT - 7750], { zebra: true }),
  Caption("Table 4. Four end-to-end agent runs (after the fixes in section 9)."),
  P(`All four answers passed every guardrail check, mentioned every scheme the person fits, and mentioned no scheme they do not fit. The average time was ${ag.avg_seconds} seconds. One run took 52 seconds because the first model had reached its daily limit. Before the last guardrail fixes, one of four runs (Fatima) ended as \"not fully verified\" because the guardrail wrongly treated the housing categories EWS, LIG and MIG as unknown schemes. That false alarm led to the rule that any term appearing in the retrieved official text is allowed.`),

  H1("9. Problems Found and Fixed"),
  P("Building an agent that can be trusted was mostly a matter of finding failures and closing them. The log and the evaluation exposed these:"),
  Tbl(["Problem", "How it showed up", "Fix"], [
    ["Correct citations rejected", "Every answer failed; the model writes 【PM‑KISAN · Benefits】", "Normalise brackets and hyphens before checking"],
    ["Documents missing for 12 schemes", "Empty document lists for PM-KISAN, KCC, MGNREGA and others", "Converter for myScheme's rich-text format; offline rebuild"],
    ["Maternity and widow schemes \"likely\" for a 42-year-old man", "Rule-engine output for the farmer persona", "Life-situation logic; gender defaults"],
    ["Invented cash total (₹53,600 vs ₹6,000)", "Agent answer", "Guardrail check plus instruction to quote benefit_estimate"],
    ["Answers about schemes outside the library (NPS)", "Hindi test question", "Unknown-scheme guardrail"],
    ["False alarm on EWS / LIG / MIG", "Evaluation run marked unverified", "Allow terms seen in the retrieved official text"],
    ["Invented websites", "Screenshot run", "Web-address guardrail"],
    ["Documents answered from memory", "Screenshot run", "Require the document tool for document questions"],
    ["Very long paragraphs never split", "Unit test", "Sentence-aware chunking"],
    ["Keyword blending hurt exact-section retrieval", "Retrieval evaluation", "Question-intent boost; weights re-tuned"],
    ["Model daily token limit", "429 errors; slow retries", "Immediate fallback down the model chain"],
  ], [2700, 3000, CONTENT - 5700], { zebra: true }),
  P("All of these are covered by the **39 offline unit tests** in `tests/test_core.py`, which need neither an LLM nor the embedding server, so they run in about a second."),

  H1("10. Business Value and Automation Impact"),
  B("**From reading to deciding.** Screening a person against 32 schemes by hand means reading 32 sets of guidelines. SchemeSathi applies 95 rules in milliseconds and explains each result, so an operator can screen a visitor during a short counter conversation."),
  B("**Fewer wasted trips.** The merged checklist (for example 44 documents for 9 schemes, with the bank passbook and Aadhaar needed by the most schemes) means people bring the right papers the first time."),
  B("**Money made visible.** Showing \"₹6,000 a year\" or \"₹2 lakh cover for ₹20 a year\" turns an abstract scheme into a decision a family can make."),
  B("**Trust through sources.** Every claim links to the official page, and every \"no\" quotes the rule. That protects people from middlemen and lets field workers defend an answer at a bank or office."),
  B("**Near-zero running cost.** The deterministic path needs no AI at all. The agent runs on a free LLM tier, and embeddings run locally. A CSC or NGO could run it on one laptop."),
  B("**Accountability.** The audit log records what was asked, which tools ran, which model answered and every guardrail rejection, which is what a department or CSR funder would need."),
  B("**Reusable pattern.** \"Rules decide, retrieval informs, the agent explains, code verifies\" applies to any rule-heavy service: insurance claims, loan pre-screening, tax benefits and HR policy questions."),

  H1("11. Limitations and Ethics"),
  B("**Coverage.** Only 32 central schemes; most states run additional schemes. The design scales by adding scheme files and checks."),
  B("**\"Likely\" still needs an office.** Some conditions (SECC lists, land records, notified crops) can only be confirmed by an authority. SchemeSathi says so rather than hiding it."),
  B("**Rule maintenance.** Schemes change. The raw JSON is dated and the fetch script can be re-run, but the checks need a human to review changes."),
  B("**Remaining LLM risk.** The guardrail catches the errors it is designed for. A plausible but wrong *instruction* (for example naming a different office to visit) can still pass, which is why the app always shows the official links and labels itself a student project, not an official service."),
  B("**Labels written by the author.** The evaluation shows consistency with the official text, not independent ground truth."),
  B("**Privacy.** The profile stays in the browser session. Only the question and the profile summary go to the LLM provider, and the log stores questions and answers but no names. A deployment should add consent and retention rules."),
  B("**Respect for the source.** The data was collected at one request per second through a public API that robots.txt allows, with an identifying user-agent, and every answer credits myScheme."),

  H1("12. Future Work"),
  B("State schemes and more central schemes, with a change detector that re-fetches and flags rules to review."),
  B("Voice input and output in Hindi and other Indian languages for people who cannot read comfortably."),
  B("An independent evaluation with labels from scheme officers or CSC operators, and a held-out retrieval test set."),
  B("Bulk screening from a CSV for NGOs and self-help-group federations, with an aggregate \"most common blocking rule\" report."),
  B("A WhatsApp front end, the channel most people actually use."),

  H1("13. Conclusion"),
  P(`SchemeSathi shows that a single agent can be both useful and trustworthy when it is built around what LLMs are good at and kept away from what they are bad at. The LLM plans, looks up, explains and translates. Deterministic code decides eligibility, does the arithmetic and checks every answer. Against the same model working alone, which got about a third of eligibility decisions wrong (F1 ${pct(base.f1)}), the rules-grounded design matched the official criteria on every test person and produced answers in which every fact links to the Government's own text. The system is free to run, open source and ready for a Common Service Centre or NGO to try.`),

  H1("Appendix A. How to Run"),
  Code(`git clone ${REPO} && cd schemesathi`),
  Code("python3.11 -m venv .venv && source .venv/bin/activate"),
  Code("pip install -r requirements.txt"),
  Code("cp .env.example .env              # paste a free Groq API key"),
  Code("ollama pull nomic-embed-text"),
  Code("python -c \"from schemesathi import rag; print(rag.index())\""),
  Code("streamlit run app/streamlit_app.py"),
  Code("pytest -q                         # 39 offline tests"),
  Code("python eval/run_eval.py --baseline --agent 4"),
  gap(),
  H2("Repository structure"),
  Tbl(["Path", "Contents"], [
    ["schemesathi/rules.py", "Rule engine: 32 schemes, 95 checks with official quotes"],
    ["schemesathi/rag.py", "Chunking, embeddings, ChromaDB, hybrid search with intent boost, document merging"],
    ["schemesathi/tools.py", "The five agent tools"],
    ["schemesathi/agent.py", "Agent, prompt, guardrail, model fallback"],
    ["schemesathi/llm.py, config.py, log.py", "Groq models, settings, SQLite audit log"],
    ["schemesathi/personas.py", "12 sample people with hand-written expected schemes"],
    ["scripts/fetch_schemes.py", "Fetch from myScheme; rebuild Markdown offline"],
    ["app/", "Streamlit app and design system"],
    ["eval/", "Evaluation script, retrieval questions, results"],
    ["tests/test_core.py", "39 offline unit tests"],
    ["docs/", "Architecture diagram, screenshots, report"],
  ], [3600, CONTENT - 3600], { zebra: true }),

  H1("References"),
  P("1. myScheme, National Platform for Government Schemes, Government of India. https://www.myscheme.gov.in (scheme text fetched October 2026).", { align: AlignmentType.LEFT }),
  P("2. CrewAI documentation: agents, tasks, tools and task guardrails. https://docs.crewai.com", { align: AlignmentType.LEFT }),
  P("3. Yao, S. et al. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. ICLR 2023.", { align: AlignmentType.LEFT }),
  P("4. Lewis, P. et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS 2020.", { align: AlignmentType.LEFT }),
  P("5. Nussbaum, Z. et al. (2024). Nomic Embed: Training a Reproducible Long Context Text Embedder. (nomic-embed-text)", { align: AlignmentType.LEFT }),
  P("6. Groq API documentation (OpenAI-compatible endpoint, free-tier rate limits). https://console.groq.com/docs", { align: AlignmentType.LEFT }),
  P("7. ChromaDB documentation. https://docs.trychroma.com", { align: AlignmentType.LEFT }),
  P(`8. Project repository: ${REPO}`, { align: AlignmentType.LEFT }),
];

const doc = new Document({
  creator: "Mahaveer Soni", title: "SchemeSathi – AABA Individual Assignment",
  description: "Report on SchemeSathi, a single-agent rules-grounded AI assistant for Indian government schemes",
  styles: {
    default: { document: { run: { font: "Calibri", size: 22, color: "222222" } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 34, bold: true, font: "Cambria", color: INK },
        paragraph: { spacing: { before: 120, after: 220 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: SAFFRON, space: 6 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Cambria", color: SAFFRON },
        paragraph: { spacing: { before: 260, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
    { reference: "steps", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 340 } } } }] },
  ] },
  sections: [
    { properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: 1200, bottom: 1200, left: MARGIN, right: MARGIN } } },
      children: cover },
    { properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: 1300, bottom: 1300, left: MARGIN, right: MARGIN },
        pageNumbers: { start: 1 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "SchemeSathi · AABA Individual Assignment · Mahaveer Soni (065089)", size: 16, color: MUTED })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: MUTED })] })] }) },
      children: body },
  ],
});

const out = path.join(__dirname, "SchemeSathi_Report_Mahaveer_Soni_065089.docx");
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log("wrote", out); });
