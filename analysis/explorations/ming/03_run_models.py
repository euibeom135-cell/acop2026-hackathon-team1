#!/usr/bin/env python3
"""Run every method for a task/scheme on the SAME test rows and score them.

Outputs per (task, scheme, arm):
  scoreboard.csv      one row/method: metrics (+ bootstrap CI for the fold5 arm)
  selection_long.csv  one row per (method, term): coef (inference) or test-row
                      permutation importance (ML), with rank and kept flag
repeat20 writes by_seed.csv for the compare step (continuous, cheap methods).
"""
from __future__ import annotations
import sys, os, argparse, json, warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
from pipeline.data import (load_raw, make_arm_frame, load_folds, attach_fold,
                           train_test_frames, Transform)
from pipeline import models as M
from pipeline import metrics as MET


def frames_for_scheme(df, folds, arm, scheme, mode):
    """Return a list of (tag, train_frame, test_frame)."""
    frame = attach_fold(make_arm_frame(df, arm), folds)
    if scheme == "fold5":
        tr, te = train_test_frames(frame, mode)
        return [("main", tr, te)]
    # sensitivity schemes operate on folds 2-5 only
    pool = frame[frame.fold != 1].reset_index(drop=True)
    if scheme in ("single80", "single75"):
        man = pd.read_csv(os.path.join(C.OUT, "splits", f"{scheme}.csv"))
        man = man[man.treatment_arm == arm]
        test_ids = set(man.loc[man.partition == "Test", "patient_id"])
        tr = pool[~pool.patient_id.isin(test_ids)].reset_index(drop=True)
        te = pool[pool.patient_id.isin(test_ids)].reset_index(drop=True)
        return [("main", tr, te)]
    if scheme == "repeat20":
        from sklearn.model_selection import train_test_split
        seeds = json.load(open(os.path.join(C.OUT, "splits", "repeat20_seeds.json")))["seeds"]
        out = []
        for s in seeds:
            lab = _strata(pool)
            tri, tei = train_test_split(pool.index, test_size=0.20, random_state=s, stratify=lab)
            out.append((f"seed{s}", pool.loc[tri].reset_index(drop=True),
                        pool.loc[tei].reset_index(drop=True)))
        return out
    raise ValueError(scheme)


def _strata(frame):
    out = frame["y_bin"].astype(str).values.astype(object)
    for lab in frame["y_bin"].unique():
        m = frame["y_bin"] == lab
        med = frame.loc[m, "y_cont"].median()
        hi = (frame["y_cont"] > med) & m
        out[hi.values] = f"{lab}_hi"; out[(~hi & m).values] = f"{lab}_lo"
    return out


def score_one(fm, te, task, with_boot, with_perm):
    y = te.y_cont.values if task == "continuous" else te.y_bin.values
    pred = fm.predict(te)
    row = {"method": fm.name, "tier": fm.tier}
    if task == "continuous":
        row.update(MET.continuous_metrics(y, pred))
        if with_boot:
            ci = MET.bootstrap_ci(y, pred, "continuous")
            for k, (lo, hi) in ci.items():
                row[f"{k}_lo"], row[f"{k}_hi"] = lo, hi
    else:
        row.update(MET.binary_metrics(y, pred, fm.cutoff or 0.5))
        if with_boot:
            ci = MET.bootstrap_ci(y, pred, "binary", cutoff=fm.cutoff or 0.5)
            for k, (lo, hi) in ci.items():
                row[f"{k}_lo"], row[f"{k}_hi"] = lo, hi
    sel = []
    if fm.kept_terms is not None:  # inference method: coefficients
        for t in fm.coef:
            sel.append({"method": fm.name, "term": t, "kind": "coef",
                        "value": fm.coef[t], "kept": t in fm.kept_terms})
    if with_perm:  # permutation importance for every method on the test rows
        arm = te.treatment_arm.iloc[0]
        terms = Transform(arm).raw_terms
        imp, base = MET.grouped_permutation_importance(
            fm.predict, te, y, terms, task, cutoff=fm.cutoff or 0.5)
        order = sorted(imp, key=lambda t: -imp[t])
        for rank, t in enumerate(order, 1):
            sel.append({"method": fm.name, "term": t, "kind": "perm_importance",
                        "value": imp[t], "rank": rank, "top5": rank <= C.TOP_K_IMPORTANCE})
    return row, sel


def run(task, scheme, mode):
    df, folds = load_raw(), load_folds()
    methods = M.INFERENCE + M.PREDICTION
    if scheme == "repeat20":
        methods = M.CHEAP
    for arm in C.ARMS:
        outdir = os.path.join(C.OUT, "runs", task, scheme, arm)
        os.makedirs(outdir, exist_ok=True)
        blocks = frames_for_scheme(df, folds, arm, scheme, mode)
        if scheme == "repeat20":
            recs = []
            for tag, tr, te in blocks:
                seed = int(tag.replace("seed", ""))
                for name in methods:
                    fm = M.BUILDERS[name](tr, arm, task)
                    row, _ = score_one(fm, te, task, with_boot=False, with_perm=False)
                    row["seed"] = seed
                    row["kept"] = ";".join(fm.kept_terms) if fm.kept_terms else ""
                    recs.append(row)
            pd.DataFrame(recs).to_csv(os.path.join(outdir, "by_seed.csv"), index=False)
            print(f"[repeat20] {task} {arm}: {len(recs)} rows")
            continue
        tag, tr, te = blocks[0]
        board, sel_all = [], []
        with_boot = (scheme == "fold5")
        with_perm = (scheme == "fold5")
        for name in methods:
            fm = M.BUILDERS[name](tr, arm, task)
            row, sel = score_one(fm, te, task, with_boot, with_perm)
            board.append(row); sel_all.extend(sel)
        pd.DataFrame(board).to_csv(os.path.join(outdir, "scoreboard.csv"), index=False)
        pd.DataFrame(sel_all).to_csv(os.path.join(outdir, "selection_long.csv"), index=False)
        hdr = board[0]
        key = "R2" if task == "continuous" else "ROC_AUC"
        best = max(board, key=lambda r: r.get(key, -9) if np.isfinite(r.get(key, np.nan)) else -9)
        print(f"[{scheme}] {task} {arm}: n_train={len(tr)} n_test={len(te)} "
              f"best {key}={best[key]:+.3f} ({best['method']})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=["continuous", "binary", "both"], default="both")
    ap.add_argument("--scheme", choices=C.SCHEMES, default="fold5")
    ap.add_argument("--mode", choices=["rehearsal", "final"], default=C.MODE)
    a = ap.parse_args()
    tasks = ["continuous", "binary"] if a.task == "both" else [a.task]
    if a.scheme == "repeat20":
        tasks = ["continuous"]  # split-sensitivity story is about test R2
    for task in tasks:
        run(task, a.scheme, a.mode)


if __name__ == "__main__":
    main()
