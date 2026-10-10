"""Charts for the report and slides, drawn from eval/results.json.   python docs/make_charts.py"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
R = json.loads((ROOT / "eval" / "results.json").read_text())
OUT = ROOT / "docs" / "report"
INK, SAFFRON, GREEN, AMBER, RED, PAPER = "#1F2A44", "#E07A2E", "#1E8C5A", "#C98A12", "#B4473A", "#FBF7F0"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 12, "axes.edgecolor": "#C9BBA6", "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False})

# 1. rules vs LLM alone
fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=PAPER)
ax.set_facecolor(PAPER)
metrics = ["precision", "recall", "f1"]
x = range(len(metrics))
rules = [R["rules"][m] * 100 for m in metrics]
llm = [R["baseline"][m] * 100 for m in metrics]
b1 = ax.bar([i - 0.2 for i in x], rules, 0.38, color=GREEN, label="SchemeSathi rule engine")
b2 = ax.bar([i + 0.2 for i in x], llm, 0.38, color=AMBER, label=f"LLM alone ({R['baseline']['model'].split('/')[-1]}, no tools)")
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5, f"{b.get_height():.0f}%", ha="center", fontweight="bold", color=INK)
ax.set_xticks(list(x), ["Precision", "Recall", "F1"])
ax.set_ylim(0, 112); ax.set_ylabel("%")
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
ax.set_title("Who qualifies for what: 12 people × 32 schemes", color=INK, fontweight="bold", loc="left")
fig.tight_layout(); fig.savefig(OUT / "chart_eligibility.png", dpi=220); plt.close(fig)

# 2. retrieval variants
fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=PAPER)
ax.set_facecolor(PAPER)
names = [k for k in R["retrieval"] if k != "n"]
cols = ["hit@1", "hit@3", "mrr", "scheme_hit@1"]
labels = ["Hit@1", "Hit@3", "MRR", "Right scheme @1"]
colors = ["#9AA3B5", AMBER, SAFFRON]
w = 0.26
for j, n in enumerate(names):
    vals = [R["retrieval"][n][c] * 100 for c in cols]
    bars = ax.bar([i + (j - 1) * w for i in range(len(cols))], vals, w, color=colors[j], label=n)
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.2, f"{b.get_height():.0f}", ha="center", fontsize=9.5, color=INK)
ax.set_xticks(range(len(cols)), labels); ax.set_ylim(0, 110)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=10)
ax.set_title(f"Finding the right official passage ({R['retrieval']['n']} questions)", color=INK, fontweight="bold", loc="left")
fig.tight_layout(); fig.savefig(OUT / "chart_retrieval.png", dpi=220); plt.close(fig)
print("charts saved")
