#!/usr/bin/env python3
"""Assemble scoreboards, stability, compare, compact and stratification into
outputs/report/results_report.html, slide_tables.md, and figures.

Defensive: each section renders only if its inputs exist, so the report can be
built after a partial run.
"""
from __future__ import annotations
import sys, os, glob, html, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C

REP = os.path.join(C.OUT, "report")
FIG = os.path.join(REP, "figures")
INK = "#1b2a4a"; ACCENT = {"Mexiletine": "#2f6f9f", "Oligonucleotide": "#1f8a70", "Tideglusib": "#b4654a"}
plt.rcParams.update({"figure.dpi": 110, "font.size": 10, "axes.edgecolor": "#99a"})


def _load(task, scheme, arm, name):
    p = os.path.join(C.OUT, "runs", task, scheme, arm, name)
    return pd.read_csv(p) if os.path.exists(p) else None


# --------------------------------------------------------------------------- figures
def fig_scoreboard(task, arm):
    sb = _load(task, "fold5", arm, "scoreboard.csv")
    if sb is None:
        return None
    key = "R2" if task == "continuous" else "ROC_AUC"
    sb = sb.sort_values(key)
    lo = sb.get(f"{key}_lo"); hi = sb.get(f"{key}_hi")
    y = np.arange(len(sb))
    fig, ax = plt.subplots(figsize=(6.2, 0.34 * len(sb) + 1))
    xerr = None
    if lo is not None and hi is not None:
        xerr = np.vstack([sb[key] - lo.values, hi.values - sb[key]])
        xerr = np.clip(xerr, 0, None)
    ax.errorbar(sb[key], y, xerr=xerr, fmt="o", color=ACCENT[arm], ecolor="#aab",
                capsize=2, lw=1, ms=4)
    ax.set_yticks(y); ax.set_yticklabels(sb.method, fontsize=8)
    ax.axvline(0 if task == "continuous" else 0.5, color="#bbb", lw=1, ls="--")
    ax.set_xlabel("test R²  (95% bootstrap CI)" if task == "continuous"
                  else "test ROC-AUC  (95% bootstrap CI)")
    ax.set_title(f"{arm} — {'continuous' if task=='continuous' else 'responder'} scoreboard",
                 color=INK, fontsize=10)
    fig.tight_layout()
    path = os.path.join(FIG, f"scoreboard_{task}_{arm}.png")
    fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return path


def fig_stability(task, arm):
    p = os.path.join(C.OUT, "stability", task, arm, "stability.csv")
    if not os.path.exists(p):
        return None
    st = pd.read_csv(p)
    fig, ax = plt.subplots(figsize=(6.2, 4))
    colors = {"real signal": "#1f8a70", "suggestive": "#d6a000", "noise": "#b0b0b0"}
    for _, r in st.iterrows():
        ax.scatter(r.stability_freq, r.rf_importance, s=36,
                   color=colors.get(r.verdict, "#999"), edgecolor="#334", lw=.4, zorder=3)
        if r.verdict != "noise":
            ax.annotate(r.term, (r.stability_freq, r.rf_importance), fontsize=7,
                        xytext=(3, 3), textcoords="offset points")
    ax.axhline(st.null_q95.iloc[0], color="#c33", lw=1, ls="--", label="null 95th pct")
    ax.axvline(C.STABILITY_THRESHOLD, color="#36c", lw=1, ls=":", label="stability 0.6")
    ax.set_xlabel("stability-selection frequency"); ax.set_ylabel("RF grouped importance")
    ax.set_title(f"{arm} — signal vs noise ({task})", color=INK, fontsize=10)
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    path = os.path.join(FIG, f"stability_{task}_{arm}.png")
    fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return path


def fig_partial_dependence(arm):
    p = os.path.join(C.OUT, "stratify", arm, "partial_dependence.csv")
    rp = os.path.join(C.OUT, "stratify", arm, "rule.txt")
    if not os.path.exists(p):
        return None
    pdc = pd.read_csv(p)
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.plot(pdc.grid, pdc.pd, color=ACCENT[arm], lw=2)
    lead = thr = None
    if os.path.exists(rp):
        for line in open(rp):
            if line.startswith("data-chosen threshold"):
                seg = line.split(":")[1].strip()
                lead = seg.split()[0]
                try:
                    thr = float(seg.split()[-1])
                except Exception:
                    thr = None
    if thr is not None:
        ax.axvline(thr, color="#c33", lw=1.2, ls="--", label=f"threshold {thr:.3g}")
        ax.legend(fontsize=8)
    ax.set_xlabel(C.LABELS.get(lead, lead or "leading term"))
    ax.set_ylabel("RF partial dependence (improvement)")
    ax.set_title(f"{arm} — where the forest bends", color=INK, fontsize=10)
    fig.tight_layout()
    path = os.path.join(FIG, f"pd_{arm}.png")
    fig.savefig(path, bbox_inches="tight"); plt.close(fig)
    return path


# --------------------------------------------------------------------------- tables
def scoreboard_table(task, arm):
    sb = _load(task, "fold5", arm, "scoreboard.csv")
    if sb is None:
        return ""
    key = "R2" if task == "continuous" else "ROC_AUC"
    sb = sb.sort_values(key, ascending=False)
    cols = (["method", "tier", "R2", "RMSE", "MAE"] if task == "continuous"
            else ["method", "tier", "ROC_AUC", "Recall", "Precision", "Accuracy", "cutoff"])
    cols = [c for c in cols if c in sb.columns]
    disp = sb[cols].copy()
    for c in disp.columns:
        if disp[c].dtype.kind == "f":
            disp[c] = disp[c].map(lambda v: f"{v:+.3f}" if c in ("R2",) else f"{v:.3f}")
    return disp.to_html(index=False, border=0, classes="tbl")


def md_tables():
    L = ["# Slide tables (numbers traced to pipeline outputs)",
         f"\n*mode: {C.MODE} — rehearsal scores fold 5; final scores the locked fold 1.*\n"]
    # compact scoreboards (the headline story)
    L.append("## Compact models (consensus covariates, scored on held-out test)\n")
    for task in ["continuous", "binary"]:
        L.append(f"\n### {task}\n")
        for arm in C.ARMS:
            cm = _load(task, "fold5", arm, "compact_scoreboard.csv")
            if cm is not None:
                L.append(f"\n**{arm}**\n")
                L.append(cm.to_markdown(index=False))
    # full scoreboards
    L.append("\n\n## Full scoreboards\n")
    for task in ["continuous", "binary"]:
        for arm in C.ARMS:
            sb = _load(task, "fold5", arm, "scoreboard.csv")
            if sb is None:
                continue
            key = "R2" if task == "continuous" else "ROC_AUC"
            keep = [c for c in [key, f"{key}_lo", f"{key}_hi"] if c in sb.columns]
            t = sb.sort_values(key, ascending=False)[["method", "tier"] + keep]
            L.append(f"\n**{arm} — {task}**\n")
            L.append(t.round(3).to_markdown(index=False))
    # stability
    L.append("\n\n## Real signal vs noise (stability selection + shuffled null)\n")
    for task in ["continuous", "binary"]:
        for arm in C.ARMS:
            p = os.path.join(C.OUT, "stability", task, arm, "stability.csv")
            if os.path.exists(p):
                st = pd.read_csv(p)
                real = st[st.verdict == "real signal"].term.tolist()
                sug = st[st.verdict == "suggestive"].term.tolist()
                L.append(f"- **{arm} / {task}**: real = {real or '—'}; suggestive = {sug or '—'}")
    # Cross-seed override note (not auto-computed): a term can clear the per-fold
    # real-signal bar yet fail cross-seed replication, so it must not be claimed.
    L.append(
        "\n> **Cross-seed override (not auto-computed):** a covariate can clear the "
        "per-fold real-signal bar above yet fail cross-seed replication. "
        "Oligonucleotide `insulin_resistance` (continuous) is such a case "
        "(17% cross-seed, non-consensus 0.42 < 0.5, q = 0.075 under FDR) and is "
        "**downgraded, not claimed** — the claimed Oligo/continuous signal is "
        "`ctg_repeats` only (`docs/interpretation_Oligonucleotide.md` §4). "
        "The locked fold-1 run re-evaluates every verdict."
    )
    # stratification
    L.append("\n\n## Stratification rules\n")
    for arm in C.ARMS:
        rp = os.path.join(C.OUT, "stratify", arm, "rule.txt")
        if os.path.exists(rp):
            L.append(f"\n**{arm}**\n\n```\n{open(rp).read().strip()}\n```")
    # split sensitivity
    vp = os.path.join(C.OUT, "compare", "verdict.md")
    if os.path.exists(vp):
        L.append("\n\n## Split sensitivity\n")
        L.append(open(vp).read())
    open(os.path.join(C.OUT, "report", "slide_tables.md"), "w").write("\n".join(L) + "\n")


def build_html():
    os.makedirs(FIG, exist_ok=True)
    parts = [f"""<!doctype html><meta charset=utf-8><title>DM1 results report</title>
<style>
body{{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;color:{INK};max-width:980px;margin:2rem auto;padding:0 1rem}}
h1{{border-bottom:3px solid {INK};padding-bottom:.3rem}} h2{{margin-top:2rem;color:{INK}}}
table.tbl{{border-collapse:collapse;font-size:12px;margin:.4rem 0}} .tbl td,.tbl th{{border:1px solid #d4d9e4;padding:3px 8px;text-align:right}}
.tbl th{{background:#eef2f8;text-align:center}} img{{max-width:100%;margin:.5rem 0}}
.cap{{color:#667;font-size:12px}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
code{{background:#f3f5fa;padding:1px 4px;border-radius:3px}}
</style>
<h1>DM1 covariate analysis — results report</h1>
<p class=cap>mode: <b>{C.MODE}</b> &nbsp;·&nbsp; rehearsal scores fold 5 (pseudo-test); the locked fold 1 is scored only at the final run (G3).
Primary endpoint: continuous improvement per arm (mexiletine = relative myotonia change). Secondary: responder label.
Gradient boosting uses scikit-learn HistGradientBoosting (XGBoost's role; no OpenMP runtime in this environment).</p>
"""]
    for task, label in [("continuous", "Continuous outcome (R², RMSE, MAE)"),
                        ("binary", "Responder label (ROC-AUC, recall, precision, accuracy)")]:
        parts.append(f"<h2>{label}</h2>")
        for arm in C.ARMS:
            fs = fig_scoreboard(task, arm)
            parts.append(f"<h3 style='color:{ACCENT[arm]}'>{arm}</h3>")
            if fs:
                parts.append(f"<img src='figures/{os.path.basename(fs)}'>")
            parts.append(scoreboard_table(task, arm))
            cm = _load(task, "fold5", arm, "compact_scoreboard.csv")
            if cm is not None:
                parts.append("<p class=cap>Compact models on consensus covariates:</p>")
                parts.append(cm.round(3).to_html(index=False, border=0, classes="tbl"))

    parts.append("<h2>Real signal vs noise</h2><div class=grid>")
    for task in ["continuous", "binary"]:
        for arm in C.ARMS:
            f = fig_stability(task, arm)
            if f:
                parts.append(f"<div><img src='figures/{os.path.basename(f)}'></div>")
    parts.append("</div>")

    parts.append("<h2>Stratification — where the forest bends</h2><div class=grid>")
    for arm in C.ARMS:
        f = fig_partial_dependence(arm)
        rp = os.path.join(C.OUT, "stratify", arm, "rule.txt")
        if f:
            parts.append(f"<div><img src='figures/{os.path.basename(f)}'>")
            if os.path.exists(rp):
                parts.append(f"<pre class=cap>{html.escape(open(rp).read())}</pre>")
            parts.append("</div>")
    parts.append("</div>")

    vp = os.path.join(C.OUT, "compare", "verdict.md")
    if os.path.exists(vp):
        import re
        txt = html.escape(open(vp).read())
        parts.append("<h2>Split sensitivity</h2><pre>" + txt + "</pre>")

    open(os.path.join(REP, "results_report.html"), "w").write("\n".join(parts))


def main():
    os.makedirs(FIG, exist_ok=True)
    build_html()
    md_tables()
    print("report ->", os.path.join(REP, "results_report.html"))
    print("tables ->", os.path.join(REP, "slide_tables.md"))


if __name__ == "__main__":
    main()
