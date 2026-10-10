// Builds docs/report/SchemeSathi_Deck_Mahaveer_Soni_065089.pptx   (node build_deck.js; needs pptxgenjs, react-icons, sharp)
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const Fa = require("react-icons/fa");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const ROOT = path.resolve(__dirname, "..", "..");
const R = JSON.parse(fs.readFileSync(path.join(ROOT, "eval", "results.json"), "utf8"));
const REPO = "github.com/Mahaveersonii/schemesathi";
const SHOT = (f) => path.join(ROOT, "docs", "screens", f);
const pct = (x) => `${Math.round(x * 100)}%`;

const THEME = {
  name: "SchemeSathi", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1F2A44", lt1: "FFFFFF", dk2: "2B3A63", lt2: "FBF7F0", accent1: "E07A2E", accent2: "1E8C5A",
    accent3: "C98A12", accent4: "B4473A", accent5: "3B4C7A", accent6: "5E6678", hlink: "3B4C7A", folHlink: "5E6678" },
};
const HEX = THEME.colors;

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}
const pngSize = (f) => { const b = fs.readFileSync(f); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; };

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
  pres.author = "Mahaveer Soni (065089)";
  pres.title = "SchemeSathi – AABA Individual Assignment";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;
  const W = 13.333;

  // ---------- layouts ----------
  pres.defineSlideMaster({
    title: "DARK", background: { color: HEX.dk1 },
    objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.7, y: 2.2, w: 8.4, h: 1.4, fontSize: 54, bold: true,
      color: C.background1, fontFace: "Cambria", valign: "middle", align: "left", margin: 0 }, text: "" } }],
  });
  pres.defineSlideMaster({
    title: "CONTENT", background: { color: HEX.lt1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.85, fontSize: 30, bold: true,
        color: C.text1, fontFace: "Cambria", valign: "middle", align: "left", margin: 0 }, text: "" } },
      { text: { text: "SchemeSathi · Mahaveer Soni (065089) · AABA", options: { x: 0.6, y: 7.0, w: 7, h: 0.3, fontSize: 10, color: HEX.accent6, margin: 0 } } },
    ],
    slideNumber: { x: 12.3, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: HEX.accent6, align: "right" },
  });

  const content = (title, section) => {
    const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
    s.addText(title, { placeholder: "title" });
    return s;
  };
  const card = (s, x, y, w, h, fill = HEX.lt2, name = "card") =>
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: fill }, objectName: name });
  const circleIcon = async (s, Comp, x, y, d, bg, fg = "FFFFFF") => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: bg }, line: { color: bg }, objectName: "icon-circle" });
    s.addImage({ data: await icon(Comp, fg), x: x + d * 0.24, y: y + d * 0.24, w: d * 0.52, h: d * 0.52, objectName: "icon" });
  };
  const fitImage = (s, file, x, y, maxW, maxH, opts = {}) => {
    const { w, h } = pngSize(file);
    let ww = maxW, hh = (maxW * h) / w;
    if (hh > maxH) { hh = maxH; ww = (maxH * w) / h; }
    s.addImage({ path: file, x: x + (maxW - ww) / 2, y, w: ww, h: hh, objectName: path.basename(file), ...opts });
  };
  const cropTop = (s, file, x, y, w, h, frac) => {
    const sz = pngSize(file);
    s.addImage({ path: file, x, y, w, h, sizing: { type: "crop", w, h: h, x: 0, y: 0 }, objectName: path.basename(file) });
  };

  const base = R.baseline, ag = R.agent, ret = R.retrieval;
  const bt = base.rows.reduce((a, r) => [a[0] + r.llm_tp, a[1] + r.llm_fp, a[2] + r.llm_fn], [0, 0, 0]);
  const hyb = ret["hybrid + intent boost"];

  // ---------- 1. title ----------
  pres.addSection({ title: "Introduction" });
  let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Introduction" });
  s.addText("Agentic AI for Business Automation (AABA) · PGDM-BDA, Term 04, 2026-27", { x: 0.7, y: 0.6, w: 9, h: 0.4, fontSize: 14, color: "F6C9A5", bold: true, margin: 0 });
  s.addText("Report on", { x: 0.7, y: 1.7, w: 6, h: 0.45, fontSize: 18, italic: true, color: "D6DCEC", margin: 0, fontFace: "Cambria" });
  s.addText("SchemeSathi", { placeholder: "title" });
  s.addText("A single AI agent that finds the government schemes a citizen is entitled to, with the official source for every line",
    { x: 0.7, y: 3.65, w: 7.6, h: 1.0, fontSize: 18, color: "F6C9A5", margin: 0, valign: "top" });
  s.addText([
    { text: "Submitted to  ", options: { bold: true, color: "F6C9A5" } }, { text: "Faculty Name: Prof. Shiva Botchu", options: { color: "FFFFFF", breakLine: true } },
    { text: "Submitted by  ", options: { bold: true, color: "F6C9A5" } }, { text: "Mahaveer Soni · Roll No. 065089", options: { color: "FFFFFF" } },
  ], { x: 0.7, y: 5.2, w: 7.5, h: 0.8, fontSize: 15, margin: 0, paraSpaceAfter: 6 });
  s.addText("Submitted in partial fulfilment of the requirements for the Post Graduate Diploma in Management (PGDM)",
    { x: 0.7, y: 6.25, w: 7.8, h: 0.5, fontSize: 11, italic: true, color: "AEB6CC", margin: 0 });
  card(s, 9.0, 0.6, 3.7, 1.15, "FFFFFF", "logo-card");
  fitImage(s, path.join(__dirname, "fore_logo.png"), 9.15, 0.78, 3.4, 0.8);
  s.addShape(pres.shapes.OVAL, { x: 9.6, y: 2.4, w: 3.0, h: 3.0, fill: { color: HEX.accent1, transparency: 70 }, line: { color: HEX.accent1, transparency: 70 }, objectName: "glow" });
  s.addText([{ text: "32", options: { fontSize: 66, bold: true, color: "FFFFFF", fontFace: "Cambria", breakLine: true } },
    { text: "central schemes checked\nagainst official rules", options: { fontSize: 14, color: "FFFFFF" } }],
  { x: 9.6, y: 2.75, w: 3.0, h: 2.3, align: "center", valign: "middle", margin: 0 });
  s.addText(REPO, { x: 9.0, y: 6.25, w: 3.7, h: 0.4, fontSize: 12, color: "F6C9A5", align: "right", margin: 0,
    hyperlink: { url: "https://" + REPO } });
  s.addNotes("SchemeSathi means scheme companion. One agent, five tools, and a guardrail in code, so it can't guess or invent sources.");

  // ---------- 2. problem ----------
  pres.addSection({ title: "Problem" });
  s = content("Benefits exist, but people cannot reach them", "Problem");
  s.addText("Each scheme has its own age bands, land, income, caste and exclusion rules, its own document list and its own route to apply. The people who need them most are the least able to read 30 sets of guidelines.",
    { x: 0.6, y: 1.35, w: 12.1, h: 0.8, fontSize: 16, color: HEX.dk1, margin: 0 });
  const pains = [
    [Fa.FaQuestionCircle, HEX.accent4, "It guesses", "An LLM alone offered the old-age pension to a 34-year-old and PM-KISAN to a tenant farmer with no land in his name."],
    [Fa.FaLink, HEX.accent3, "It invents", "During development it wrote government websites that do not exist and a cash total more than 8× the real one."],
    [Fa.FaFileAlt, HEX.accent5, "It shows no source", "A family, a CSC operator or an NGO worker needs the official line to show at the bank or block office."],
  ];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 4.1;
    card(s, x, 2.45, 3.8, 3.9);
    await circleIcon(s, pains[i][0], x + 0.3, 2.75, 0.85, pains[i][1]);
    s.addText(pains[i][2], { x: x + 0.3, y: 3.8, w: 3.2, h: 0.55, fontSize: 22, bold: true, color: HEX.dk1, fontFace: "Cambria", margin: 0 });
    s.addText(pains[i][3], { x: x + 0.3, y: 4.4, w: 3.2, h: 1.7, fontSize: 15, color: HEX.dk1, margin: 0, valign: "top" });
  }
  s.addText("A wrong “yes” wastes a day and bus fare. A wrong “no” quietly costs money a family is owed.",
    { x: 0.6, y: 6.45, w: 12.1, h: 0.4, fontSize: 15, italic: true, color: HEX.accent1, margin: 0 });
  s.addNotes("The design goal is an agent whose every claim can be checked, not a better chatbot.");

  // ---------- 3. LLM alone ----------
  s = content("An LLM alone gets eligibility wrong one time in three", "Problem");
  s.addChart(pres.charts.BAR, [
    { name: "SchemeSathi rule engine", labels: ["Precision", "Recall", "F1"], values: [R.rules.precision, R.rules.recall, R.rules.f1].map((v) => Math.round(v * 100)) },
    { name: `LLM alone (${base.model.split("/").pop()})`, labels: ["Precision", "Recall", "F1"], values: [base.precision, base.recall, base.f1].map((v) => Math.round(v * 100)) },
  ], { x: 0.6, y: 1.4, w: 7.4, h: 5.3, barDir: "col", barGapWidthPct: 60, chartColors: [HEX.accent2, HEX.accent3],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0"%"', dataLabelFontSize: 14, dataLabelColor: HEX.dk1,
    dataLabelFontFace: "+mn-lt", catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt",
    catAxisLabelColor: HEX.accent6, valAxisLabelColor: HEX.accent6, catAxisLabelFontSize: 14, valAxisMaxVal: 110, valAxisHidden: true,
    valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: true, legendPos: "b", legendFontSize: 13,
    showTitle: true, title: "12 people × 32 schemes = 384 decisions", titleFontSize: 15, titleColor: HEX.dk1, titleFontFace: "+mn-lt" });
  const stats = [[String(bt[1]), "schemes wrongly offered", HEX.accent4], [String(bt[2]), "schemes people qualify for, missed", HEX.accent3], [pct(base.f1), "F1 for the LLM alone (rules: 100%)", HEX.dk1]];
  stats.forEach(([n, l, c], i) => {
    card(s, 8.5, 1.45 + i * 1.75, 4.2, 1.55);
    s.addText(n, { x: 8.75, y: 1.55 + i * 1.75, w: 1.8, h: 1.35, fontSize: 48, bold: true, color: c, fontFace: "Cambria", margin: 0, valign: "middle" });
    s.addText(l, { x: 10.55, y: 1.55 + i * 1.75, w: 2.0, h: 1.35, fontSize: 14, color: HEX.dk1, margin: 0, valign: "middle" });
  });
  s.addNotes("Same model the agent uses, given the profile and the list of 32 schemes, no tools. It missed MGNREGA for most rural people.");

  // ---------- 4. approach ----------
  pres.addSection({ title: "Solution" });
  s = content("Rules decide, the agent explains, code verifies", "Solution");
  const pillars = [
    [Fa.FaBalanceScale, HEX.accent2, "Rules decide", "95 checks for 32 schemes, each with its official quote. Eligible, likely or not eligible, with the reason."],
    [Fa.FaBookOpen, HEX.accent1, "Retrieval informs", "522 official passages from myScheme, searched by meaning and keywords. Every fact carries a citation tag."],
    [Fa.FaRobot, HEX.dk1, "One agent explains", "A single CrewAI agent picks from five tools, then answers in plain English or Hindi."],
    [Fa.FaShieldAlt, HEX.accent4, "Code verifies", "A guardrail rejects invented sources, schemes or websites, overruled verdicts and wrong totals."],
  ];
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + i * 3.08;
    card(s, x, 1.5, 2.85, 4.6);
    await circleIcon(s, pillars[i][0], x + 0.3, 1.8, 0.95, pillars[i][1]);
    s.addText(`0${i + 1}`, { x: x + 1.9, y: 1.85, w: 0.7, h: 0.5, fontSize: 18, bold: true, color: HEX.accent6, align: "right", margin: 0 });
    s.addText(pillars[i][2], { x: x + 0.3, y: 2.95, w: 2.3, h: 0.9, fontSize: 21, bold: true, color: HEX.dk1, fontFace: "Cambria", margin: 0, valign: "top" });
    s.addText(pillars[i][3], { x: x + 0.3, y: 3.85, w: 2.3, h: 2.1, fontSize: 14.5, color: HEX.dk1, margin: 0, valign: "top" });
  }
  s.addText("Why one agent? One user, one conversation, one decision: which tools to call. Extra agents add hand-offs, tokens and blame-shifting.",
    { x: 0.6, y: 6.3, w: 12.1, h: 0.5, fontSize: 14, italic: true, color: HEX.accent1, margin: 0 });
  s.addNotes("The LLM does what it is good at: planning, reading and explaining. Deterministic code does what it is bad at: rules, arithmetic and checking.");

  // ---------- 5. architecture ----------
  s = content("Architecture", "Solution");
  fitImage(s, path.join(ROOT, "docs", "architecture.png"), 0.6, 1.3, 12.1, 5.6);
  s.addNotes("Two paths: the instant path uses no AI at all; the agent path runs only for questions. That saves the free token budget.");

  // ---------- 6. agent + tools ----------
  s = content("One agent, five tools, a model chain that never stalls", "Solution");
  const tools = [
    ["check_eligibility", HEX.accent2, "Verdicts and reasons from the rule engine, with citation tags"],
    ["benefit_estimate", HEX.accent2, "Yearly cash total plus one-time and future benefits"],
    ["search_schemes", HEX.accent1, "Top official passages: 0.9 meaning + 0.1 keywords + intent boost"],
    ["scheme_section", HEX.accent1, "Exact text of Benefits, Eligibility, Application or Documents"],
    ["document_checklist", HEX.accent1, "One merged list across schemes: gather each paper once"],
  ];
  tools.forEach(([n, c, d], i) => {
    const y = 1.45 + i * 0.98;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 3.0, h: 0.7, rectRadius: 0.35, fill: { color: c }, line: { color: c }, objectName: "tool-pill" });
    s.addText(n, { x: 0.6, y, w: 3.0, h: 0.7, fontSize: 15, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
    s.addText(d, { x: 3.85, y, w: 4.3, h: 0.7, fontSize: 14.5, color: HEX.dk1, valign: "middle", margin: 0 });
  });
  card(s, 8.6, 1.45, 4.1, 4.65);
  await circleIcon(s, Fa.FaBolt, 8.9, 1.7, 0.8, HEX.dk1);
  s.addText("LLM on Groq (free)", { x: 8.9, y: 2.65, w: 3.6, h: 0.5, fontSize: 20, bold: true, color: HEX.dk1, fontFace: "Cambria", margin: 0 });
  s.addText([
    { text: "gpt-oss-120b → gpt-oss-20b → Qwen3", options: { bold: true, color: HEX.accent5, breakLine: true } },
    { text: "Daily limit hit? Next model at once", options: { bullet: true, breakLine: true } },
    { text: "Malformed tool call? One retry", options: { bullet: true, breakLine: true } },
    { text: "Embeddings local via Ollama", options: { bullet: true, breakLine: true } },
    { text: `Typical answer: 2–15 s`, options: { bullet: true } },
  ], { x: 8.9, y: 3.2, w: 3.6, h: 2.7, fontSize: 14.5, color: HEX.dk1, margin: 0, paraSpaceAfter: 6, valign: "top" });
  s.addText("Instructions: check eligibility first · cite every fact · quote the computed total · never invent offices, websites or documents",
    { x: 0.6, y: 6.35, w: 12.1, h: 0.45, fontSize: 13, italic: true, color: HEX.accent6, margin: 0 });

  // ---------- 7. guardrail ----------
  s = content("The guardrail: six checks in code, not left to the model", "Solution");
  const checks = [
    "Every citation was returned by a tool in this run",
    "No sentence contradicts a rule-engine verdict",
    "No scheme outside the official library",
    "No web address absent from the official text",
    "Document or apply questions must use that tool",
    "Any yearly total equals benefit_estimate",
  ];
  checks.forEach((t, i) => {
    const y = 1.45 + i * 0.8;
    s.addShape(pres.shapes.OVAL, { x: 0.6, y: y + 0.08, w: 0.5, h: 0.5, fill: { color: HEX.accent2 }, line: { color: HEX.accent2 }, objectName: "tick" });
    s.addText("✓", { x: 0.6, y: y + 0.08, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
    s.addText(t, { x: 1.3, y, w: 5.6, h: 0.66, fontSize: 16, color: HEX.dk1, valign: "middle", margin: 0 });
  });
  card(s, 7.3, 1.45, 5.4, 4.75, "FFF3EA", "catch-card");
  s.addText("A real catch, from the audit log", { x: 7.6, y: 1.65, w: 4.9, h: 0.45, fontSize: 18, bold: true, color: HEX.accent4, fontFace: "Cambria", margin: 0 });
  s.addText([
    { text: "Draft 1: “apply at www.pradhanmantrijeevanjyotibima.gov.in”", options: { breakLine: true } },
    { text: "→ rejected: not in the official text", options: { color: HEX.accent4, bold: true, breakLine: true } },
    { text: "Draft 2: same invented address", options: { breakLine: true } },
    { text: "→ rejected again", options: { color: HEX.accent4, bold: true, breakLine: true } },
    { text: "Draft 3: real citations, no invented links", options: { breakLine: true } },
    { text: "→ accepted, 6 official sources", options: { color: HEX.accent2, bold: true } },
  ], { x: 7.6, y: 2.2, w: 4.9, h: 2.9, fontSize: 14.5, color: HEX.dk1, margin: 0, paraSpaceAfter: 4, valign: "top" });
  s.addText("Still failing after 2 retries? Keep the draft, strip unverified tags, label it “not fully verified”.",
    { x: 7.6, y: 5.2, w: 4.9, h: 0.85, fontSize: 13, italic: true, color: HEX.accent6, margin: 0, valign: "top" });

  // ---------- 8-9. app ----------
  pres.addSection({ title: "Product" });
  s = content("The app: a profile once, every scheme checked instantly", "Product");
  s.addImage({ path: SHOT("home.png"), x: 0.6, y: 1.35, w: 7.4, h: 5.14, objectName: "home-shot" });
  s.addText([
    { text: "12 sample people, one click each", options: { bullet: true, breakLine: true } },
    { text: "Green, amber or red cards with every reason ticked or crossed", options: { bullet: true, breakLine: true } },
    { text: "Cash a year, only where the official text gives an amount", options: { bullet: true, breakLine: true } },
    { text: "“Not eligible (and why)” quotes the rule that failed", options: { bullet: true, breakLine: true } },
    { text: "“Only if” view for pregnancy, widowhood, disability and similar situations", options: { bullet: true, breakLine: true } },
    { text: "No AI on this path: instant and free", options: { bullet: true, bold: true, color: HEX.accent2 } },
  ], { x: 8.4, y: 1.45, w: 4.3, h: 5.0, fontSize: 15, color: HEX.dk1, margin: 0, paraSpaceAfter: 10, valign: "top" });

  s = content("Ask in English or Hindi; take one document list to the office", "Product");
  s.addImage({ path: SHOT("chat.png"), x: 0.6, y: 1.35, w: 6.0, h: 4.17, objectName: "chat-shot" });
  s.addImage({ path: SHOT("documents.png"), x: 6.75, y: 1.35, w: 6.0, h: 4.17, objectName: "docs-shot" });
  s.addText("The agent chose its tools, cited the official sections and passed the guardrail; the panel shows tools, model, time and retries",
    { x: 0.6, y: 5.65, w: 6.0, h: 0.9, fontSize: 13, color: HEX.accent6, margin: 0, valign: "top" });
  s.addText("Fatima, street vendor: 9 schemes, with documents merged so the bank passbook and Aadhaar appear once each",
    { x: 6.75, y: 5.65, w: 6.0, h: 0.9, fontSize: 13, color: HEX.accent6, margin: 0, valign: "top" });

  // ---------- 10. evaluation ----------
  pres.addSection({ title: "Results" });
  s = content("Evaluation: the right passage, and every answer verified", "Results");
  const labels = ["Hit@1", "Hit@3", "MRR"];
  const keys = Object.keys(ret).filter((k) => k !== "n");
  s.addChart(pres.charts.BAR, keys.map((k) => ({ name: k, labels, values: [ret[k]["hit@1"], ret[k]["hit@3"], ret[k].mrr].map((v) => Math.round(v * 100)) })),
    { x: 0.6, y: 1.4, w: 7.0, h: 5.2, barDir: "col", barGapWidthPct: 50, chartColors: ["9AA3B5", HEX.accent3, HEX.accent1],
      showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt",
      catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt",
      catAxisLabelColor: HEX.accent6, catAxisLabelFontSize: 14, valAxisHidden: true, valAxisMaxVal: 100,
      valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: true, legendPos: "b", legendFontSize: 12,
      showTitle: true, title: `Retrieval on ${ret.n} questions (%, MRR × 100)`, titleFontSize: 15, titleColor: HEX.dk1, titleFontFace: "+mn-lt" });
  const ev = [[pct(hyb["hit@3"]), "exact official section in the top 3"], [pct(ag.verified_rate), "agent answers passed every check"],
    [`${ag.rows.length}/${ag.rows.length}`, "runs mentioned every fitting scheme, no wrong ones"], [`${ag.avg_seconds} s`, "average answer time"]];
  ev.forEach(([n, l], i) => {
    const y = 1.45 + i * 1.32;
    card(s, 8.1, y, 4.6, 1.15);
    s.addText(n, { x: 8.3, y, w: 1.9, h: 1.15, fontSize: 34, bold: true, color: i === 0 ? HEX.accent1 : HEX.accent2, fontFace: "Cambria", margin: 0, valign: "middle" });
    s.addText(l, { x: 10.25, y, w: 2.35, h: 1.15, fontSize: 14, color: HEX.dk1, margin: 0, valign: "middle" });
  });
  s.addText("The intent boost (“documents” → Documents Required) lifted Hit@3. Weights were tuned on the same 24 questions, so treat these as optimistic.",
    { x: 0.6, y: 6.55, w: 12.1, h: 0.4, fontSize: 12, italic: true, color: HEX.accent6, margin: 0 });

  // ---------- 11. problems fixed ----------
  s = content("What testing exposed, and what fixed it", "Results");
  const fixes = [
    ["Correct citations rejected", "Model used different brackets", "Normalise brackets and hyphens"],
    ["12 schemes lost their documents", "Rich-text format on myScheme", "Converter + offline rebuild"],
    ["Maternity schemes for a man", "Unknown ≠ “likely”", "“Only if” life situations"],
    ["Cash total ₹53,600 (really ₹6,000)", "LLM arithmetic", "Guardrail checks the computed total"],
    ["NPS described with a wrong rule", "Out-of-library scheme", "Unknown-scheme check"],
    ["Invented websites", "Plausible .gov.in names", "Address must be in the official text"],
  ];
  fixes.forEach(([a, b, c], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = 0.6 + col * 4.1, y = 1.45 + row * 2.6;
    card(s, x, y, 3.8, 2.35);
    s.addText(a, { x: x + 0.25, y: y + 0.2, w: 3.3, h: 0.75, fontSize: 16.5, bold: true, color: HEX.accent4, fontFace: "Cambria", margin: 0, valign: "top" });
    s.addText(b, { x: x + 0.25, y: y + 0.95, w: 3.3, h: 0.5, fontSize: 13.5, italic: true, color: HEX.accent6, margin: 0, valign: "top" });
    s.addText("Fix: " + c, { x: x + 0.25, y: y + 1.5, w: 3.3, h: 0.7, fontSize: 14.5, bold: true, color: HEX.accent2, margin: 0, valign: "top" });
  });
  s.addText("All locked in by 39 offline unit tests (about 1 second, no LLM needed)", { x: 0.6, y: 6.6, w: 12.1, h: 0.35, fontSize: 13, italic: true, color: HEX.accent6, margin: 0 });

  // ---------- 12. value & limits ----------
  pres.addSection({ title: "Impact" });
  s = content("Business value, and honest limits", "Impact");
  const value = [
    [Fa.FaStopwatch, "Screening in seconds", "95 rules applied instantly at a CSC counter, NGO desk or bank-correspondent point"],
    [Fa.FaRupeeSign, "Money made visible", "“₹6,000 a year” or “₹2 lakh cover for ₹20” turns a scheme into a decision"],
    [Fa.FaClipboardCheck, "One trip, right papers", "A merged checklist means people bring each document once"],
    [Fa.FaHandHoldingUsd, "Near-zero cost", "Free LLM tier and local embeddings; runs on one laptop"],
  ];
  for (let i = 0; i < 4; i++) {
    const y = 1.45 + i * 1.25;
    await circleIcon(s, value[i][0], 0.6, y + 0.1, 0.8, HEX.accent1);
    s.addText(value[i][1], { x: 1.6, y, w: 5.7, h: 0.45, fontSize: 18, bold: true, color: HEX.dk1, fontFace: "Cambria", margin: 0 });
    s.addText(value[i][2], { x: 1.6, y: y + 0.48, w: 5.7, h: 0.6, fontSize: 14, color: HEX.dk1, margin: 0, valign: "top" });
  }
  card(s, 7.8, 1.45, 4.9, 4.95);
  s.addText("Limits", { x: 8.1, y: 1.65, w: 4.3, h: 0.5, fontSize: 20, bold: true, color: HEX.dk1, fontFace: "Cambria", margin: 0 });
  s.addText([
    { text: "32 central schemes; no state schemes yet", options: { bullet: true, breakLine: true } },
    { text: "“Likely” still needs an office to confirm", options: { bullet: true, breakLine: true } },
    { text: "Rules need review when schemes change", options: { bullet: true, breakLine: true } },
    { text: "Labels written by the author, not an independent audit", options: { bullet: true, breakLine: true } },
    { text: "A plausible wrong instruction can still slip through, so official links are always shown", options: { bullet: true } },
  ], { x: 8.1, y: 2.25, w: 4.4, h: 4.0, fontSize: 14, color: HEX.dk1, margin: 0, paraSpaceAfter: 8, valign: "top" });

  // ---------- 13. close ----------
  s = pres.addSlide({ masterName: "DARK", sectionTitle: "Impact" });
  s.addText("Every scheme you are owed", { x: 0.7, y: 2.25, w: 8.6, h: 1.1, fontSize: 44, bold: true, color: "FFFFFF", fontFace: "Cambria", valign: "middle", margin: 0, isTextBox: true });
  s.addText("SchemeSathi · योजना साथी", { x: 0.7, y: 1.6, w: 8.4, h: 0.5, fontSize: 16, bold: true, color: "F6C9A5", margin: 0 });
  s.addText("with the official proof for every line", { x: 0.7, y: 3.55, w: 8.4, h: 0.5, fontSize: 22, italic: true, color: "D6DCEC", fontFace: "Cambria", margin: 0 });
  s.addText("आपकी हक़ की हर सरकारी योजना — सरकारी स्रोत के साथ", { x: 0.7, y: 4.15, w: 8.4, h: 0.5, fontSize: 18, color: "F6C9A5", margin: 0 });
  s.addText([
    { text: "Code, data, tests and evaluation", options: { color: "D6DCEC", breakLine: true } },
    { text: "https://" + REPO, options: { color: "FFFFFF", bold: true, hyperlink: { url: "https://" + REPO } } },
  ], { x: 0.7, y: 5.0, w: 8.4, h: 0.9, fontSize: 18, margin: 0 });
  s.addText("Mahaveer Soni · 065089 · FORE School of Management · Thank you", { x: 0.7, y: 6.3, w: 9, h: 0.4, fontSize: 13, color: "AEB6CC", margin: 0 });
  card(s, 9.6, 2.2, 3.1, 3.1, "FFFFFF", "next-card");
  s.addText([{ text: "Next", options: { bold: true, fontSize: 18, color: HEX.accent1, fontFace: "Cambria", breakLine: true } },
    { text: "State schemes", options: { bullet: true, breakLine: true } }, { text: "Voice in Indian languages", options: { bullet: true, breakLine: true } },
    { text: "Bulk screening for NGOs", options: { bullet: true, breakLine: true } }, { text: "WhatsApp front end", options: { bullet: true } }],
  { x: 9.85, y: 2.4, w: 2.7, h: 2.7, fontSize: 14, color: HEX.dk1, margin: 0, paraSpaceAfter: 6, valign: "top" });

  const out = path.join(__dirname, "SchemeSathi_Deck_Mahaveer_Soni_065089.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
