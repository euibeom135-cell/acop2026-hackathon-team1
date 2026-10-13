#!/usr/bin/env python3
"""Does the split matter? Aggregate the sensitivity schemes.

repeat20 -> per-method mean/SD/min/max of test R2 across 20 seeds, and the
            cross-seed selection frequency of each term (inference methods).
single80 / single75 / fold5 -> the leading R2 under each scheme, side by side.
Writes outputs/compare/{repeat20_r2.csv, selection_frequency.csv,
r2_by_scheme.csv, verdict.md}. Continuous task (the sensitivity story is about
test R2); covariate stability is reported as cross-seed selection frequency.
"""
from __future__ import annotations
import sys, os, glob
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C


def repeat20_tables():
    r2_rows, freq_rows = [], []
    for arm in C.ARMS:
        p = os.path.join(C.OUT, "runs", "continuous", "repeat20", arm, "by_seed.csv")
        if not os.path.exists(p):
            continue
        bs = pd.read_csv(p)
        for method, g in bs.groupby("method"):
            r2_rows.append({"arm": arm, "method": method, "n_seeds": len(g),
                            "R2_mean": g.R2.mean(), "R2_sd": g.R2.std(),
                            "R2_min": g.R2.min(), "R2_max": g.R2.max()})
        # cross-seed selection frequency (inference methods have a 'kept' string)
        kept = bs[bs.kept.fillna("") != ""]
        term_counts = {}
        n_fits = len(kept)
        for _, row in kept.iterrows():
            for t in str(row.kept).split(";"):
                if t:
                    term_counts[t] = term_counts.get(t, 0) + 1
        for t, c in sorted(term_counts.items(), key=lambda kv: -kv[1]):
            freq_rows.append({"arm": arm, "term": t, "selected_fits": c,
                              "n_fits": n_fits, "frequency": c / n_fits if n_fits else 0})
    return pd.DataFrame(r2_rows), pd.DataFrame(freq_rows)


def r2_by_scheme():
    rows = []
    for arm in C.ARMS:
        for scheme in ["fold5", "single80", "single75"]:
            p = os.path.join(C.OUT, "runs", "continuous", scheme, arm, "scoreboard.csv")
            if not os.path.exists(p):
                continue
            sb = pd.read_csv(p)
            best = sb.loc[sb.R2.idxmax()]
            rows.append({"arm": arm, "scheme": scheme, "best_method": best.method,
                         "best_R2": float(best.R2),
                         "median_R2": float(sb.R2.median())})
    return pd.DataFrame(rows)


def main():
    os.makedirs(C.OUT + "/compare", exist_ok=True)
    r2, freq = repeat20_tables()
    scheme = r2_by_scheme()
    if not r2.empty:
        r2.to_csv(C.OUT + "/compare/repeat20_r2.csv", index=False)
    if not freq.empty:
        freq.to_csv(C.OUT + "/compare/selection_frequency.csv", index=False)
    if not scheme.empty:
        scheme.to_csv(C.OUT + "/compare/r2_by_scheme.csv", index=False)

    lines = ["# Split-sensitivity verdict", ""]
    if not r2.empty:
        med_sd = r2.R2_sd.median()
        lines.append(f"- Across 20 seeds, the median per-method SD of test R² is "
                     f"**{med_sd:.3f}** — rankings inside this band are ties.")
        for arm in C.ARMS:
            g = r2[r2.arm == arm]
            if not g.empty:
                worst = g.loc[g.R2_sd.idxmax()]
                lines.append(f"  - {arm}: R² SD ranges {g.R2_sd.min():.3f}–{g.R2_sd.max():.3f} "
                             f"(widest: {worst.method}).")
    if not freq.empty:
        lines.append("")
        lines.append("- Cross-seed selection frequency (covariate stability):")
        for arm in C.ARMS:
            g = freq[freq.arm == arm].head(5)
            if not g.empty:
                top = ", ".join(f"{r.term} {r.frequency:.0%}" for _, r in g.iterrows())
                lines.append(f"  - {arm}: {top}")
    if not scheme.empty:
        lines.append("")
        lines.append("- Leading R² by scheme (same arm, different split):")
        for arm in C.ARMS:
            g = scheme[scheme.arm == arm]
            if not g.empty:
                parts = ", ".join(f"{r.scheme} {r.best_R2:+.2f}" for _, r in g.iterrows())
                lines.append(f"  - {arm}: {parts}")
    open(C.OUT + "/compare/verdict.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
