"""Shared helpers for the clean PDF-pipeline report pages: paths, page template with stepper banner, tables, figures, 'PDF requirements' table.
Read-only on results/. Writes only reports/steps/*.html, reports/steps/figs/*.png and reports/summary.html."""
import io, html
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]            # .../pdf_pipeline
RES = ROOT / "results"; REP = ROOT / "reports"; OUT = REP / "steps"; FIGDIR = OUT / "figs"
OUT.mkdir(parents=True, exist_ok=True); FIGDIR.mkdir(parents=True, exist_ok=True)

PUR, GRN, PBG, GBG = "#6c5ce7", "#4d9a6e", "#f0eefe", "#eef6f2"
STEPS = [("1", "Understand", "step1_understand.html", "Explore structure, distributions, correlations (train only)"),
         ("2", "Split / Cross-validation", "step2_split_cv.html", "Hold out a locked test set per arm; repeated CV inside train"),
         ("3", "Preprocess", "step3_preprocess.html", "Encode and scale only what each method needs; fit on train only"),
         ("4", "Select", "step4_select.html", "Let data traits drive the choice of methods"),
         ("5", "Train", "step5_train.html", "Fit and tune on the training set only; CV scoreboard"),
         ("6", "Evaluate", "step6_evaluate.html", "Score the locked test set once; covariate vs ML; signal vs noise")]
ARMS = ["Mexiletine", "Oligonucleotide", "Tideglusib"]
ARMC = {"Mexiletine": "#d95f02", "Oligonucleotide": "#7570b3", "Tideglusib": "#1b9e77"}
FC = {"Covariate": "#1f77b4", "ML": "#d95f02", "Baseline": "#777777"}
VCOL = {"SIGNAL": "#bfe3c8", "BORDERLINE": "#fbe7a6", "NOISE": "#eeeeee"}
TASKN = {"reg": "continuous outcome", "bin": "responder label"}
OUTCOME = {"Mexiletine": ("myotonia_change_12wk", "lower (more negative) = better"), "Oligonucleotide": ("qmt_change_26wk", "higher = better"),
           "Tideglusib": ("tideglusib_composite", "higher = better")}

def esc(s): return html.escape(str(s))

def tbl(t, dec=3, cap=None, cls="t", index=False, fmt=None):
    """DataFrame -> html table. NaN -> empty string; floats to `dec` decimals."""
    f = lambda v: f"{v:.{dec}f}"
    h = t.to_html(classes=cls, border=0, index=index, float_format=f, na_rep="n/a", escape=False)
    return (f"<p class=cap>{cap}</p>" if cap else "") + h

def fig_html(fig, name, prefix="", dpi=105):
    """Save fig to reports/steps/figs/<name>.png and return a relative <img> (prefix='' from steps pages, 'steps/' from summary)."""
    p = FIGDIR / f"{name}.png"; fig.savefig(p, dpi=dpi, bbox_inches="tight"); plt.close(fig)
    return f'<img src="{prefix}figs/{name}.png" alt="{esc(name)}" style="max-width:100%">'

def note(t): return f'<p class="note">{t}</p>'
def box(t): return f'<div class="box">{t}</div>'
def warn(t): return f'<div class="warn">{t}</div>'

def nav(i):
    prev = f'<a href="{STEPS[i-1][2]}">&larr; Step {STEPS[i-1][0]}: {STEPS[i-1][1]}</a>' if i > 0 else "<span></span>"
    nxt = f'<a href="{STEPS[i+1][2]}">Step {STEPS[i+1][0]}: {STEPS[i+1][1]} &rarr;</a>' if i < len(STEPS) - 1 else "<span></span>"
    return f'<div class="nav">{prev}<span><a href="index.html">Index</a> &middot; <a href="../summary.html">Summary</a></span>{nxt}</div>'

def strip(i, base=""):
    cells = "".join(f'<a href="{base}{f}" class="cell {"on" if k == i else ""}" style="--c:{PUR if k % 2 == 0 else GRN};--bg:{PBG if k % 2 == 0 else GBG}"><span class="n">{n}</span><b>{t}</b></a>'
                    for k, (n, t, f, d) in enumerate(STEPS))
    return f'<div class="strip">{cells}</div>'

CSS = """<style>body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:1180px;margin:1.2em auto;line-height:1.5;padding:0 1em;color:#222}
.t{border-collapse:collapse;font-size:12.5px;margin:.4em 0}.t td,.t th{border:1px solid #ccc;padding:3px 8px;text-align:left;vertical-align:top}.t th{background:#f3f5f8}
.box{background:#f4f7fb;border-left:4px solid #3a6ea5;padding:.4em 1em;margin:1em 0}.warn{background:#fff8e1;border-left:4px solid #e0a800;padding:.4em 1em;margin:1em 0}
.note{color:#555;font-size:13px}.cap{font-weight:600;margin:.9em 0 0}h2{border-bottom:2px solid var(--c);padding-bottom:2px;margin-top:1.6em}h3{margin-bottom:.2em}
.strip{display:flex;gap:8px;margin:.5em 0 1em;flex-wrap:wrap}.cell{flex:1;min-width:140px;text-decoration:none;color:#222;background:var(--bg);border-radius:10px;padding:8px 10px;border:2px solid transparent;font-size:12px}
.cell.on{border-color:var(--c)}.cell .n{display:inline-block;background:var(--c);color:#fff;border-radius:50%;width:22px;height:22px;text-align:center;line-height:22px;margin-right:6px}
.nav{display:flex;justify-content:space-between;margin:.8em 0}.nav a{color:#3a6ea5;text-decoration:none}details{margin:.5em 0}summary{cursor:pointer;color:#3a6ea5}
.foot{color:#555;font-size:12px;border-top:1px solid #ddd;margin-top:2em;padding-top:.6em}.sig{background:#bfe3c8}.bor{background:#fbe7a6}.noi{color:#777}.req td:first-child{width:32%}</style>"""

FOOTER = ("AI tool disclosure (kickoff checklist): Claude Code (Anthropic) was used to write the analysis code (R and Python), to generate these pages, and to draft the text; "
          "every number on these pages is read from results/*.csv produced by the scripts in pdf_pipeline/src. Data are simulated; results do not describe real patients or approved therapies.")

def page(i, title, intro, body):
    n, t, f, d = STEPS[i]; c = PUR if i % 2 == 0 else GRN
    h = (f"<!doctype html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>DM1 Step {n}: {t}</title>{CSS}</head>"
         f"<body style='--c:{c}'>{strip(i)}{nav(i)}<h1 style='color:{c}'>Step {n} &middot; {title}</h1>{box(intro)}{body}{nav(i)}<p class=foot>{FOOTER}</p></body></html>")
    (OUT / f).write_text(h); return f

def req(rows):
    """rows: (kickoff says, what we did, where on this page). Only requirements the PDF actually states."""
    return "<h2>PDF requirements for this step</h2>" + tbl(pd.DataFrame(rows, columns=["Kickoff says", "What we did", "Where"]), cls="t req")

SHORT = {"Best subset (leaps, BIC, nvmax=10)": "Best subset (BIC)", "Elastic net (glmnet, alpha=.5)": "Elastic net", "GAM (mgcv, s(k=5), REML, select)": "GAM",
         "LASSO (glmnet, lambda.min)": "LASSO", "PCR (prcomp, k by 5-fold CV)": "PCR", "Ridge (glmnet)": "Ridge", "Stepwise both (BIC)": "Stepwise (BIC)",
         "lm / glm (all covariates)": "lm / glm (all)", "Mean only": "Mean only", "Prevalence only": "Prevalence only"}
def short(m):
    if m in SHORT: return SHORT[m]
    return m.replace(", GridSearchCV", "")
