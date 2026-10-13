#!/usr/bin/env python3
"""Consensus covariates -> compact models -> data-chosen stratification rule.

Reads the fold5 selection records written by 03. For each arm/task:
  consensus.csv   per-term agreement across methods (inference-kept rate and
                  ML-top5 rate), and the consensus set
  agreement.csv   Jaccard overlap of kept-term sets between inference methods
  compact_scoreboard.csv  1-, 2- and 3-term models on the consensus terms,
                  scored on the same test rows
stratify/<arm>/rule.txt  a one-term indicator rule where the RF partial
                  dependence of the leading numeric term bends (depth-1 tree
                  threshold), with the compact model's R2 gain from adding it
"""
from __future__ import annotations
import sys, os, warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
from pipeline.data import (load_raw, make_arm_frame, load_folds, attach_fold,
                           train_test_frames, Transform)
from pipeline import models as M
from pipeline import metrics as MET
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor


def consensus_and_agreement(task, arm):
    d = os.path.join(C.OUT, "runs", task, "fold5", arm)
    sel = pd.read_csv(os.path.join(d, "selection_long.csv"))
    terms = Transform(arm).raw_terms
    inf_methods = sel[sel.kind == "coef"].method.unique().tolist()
    kept = {m: set(sel[(sel.method == m) & (sel.kind == "coef") & (sel.kept == True)].term)
            for m in inf_methods}
    ml = sel[(sel.kind == "perm_importance") & (sel.get("top5") == True)]
    ml_methods = ml.method.unique().tolist()
    top5 = {m: set(ml[ml.method == m].term) for m in ml_methods}
    rows = []
    for t in terms:
        ik = np.mean([t in kept[m] for m in inf_methods]) if inf_methods else 0.0
        mk = np.mean([t in top5[m] for m in ml_methods]) if ml_methods else 0.0
        rows.append({"term": t, "inference_kept_rate": ik, "ml_top5_rate": mk,
                     "consensus": 0.5 * ik + 0.5 * mk})
    cons = pd.DataFrame(rows).sort_values("consensus", ascending=False)
    cons["in_consensus"] = cons.consensus >= C.CONSENSUS_FRACTION
    # agreement matrix (Jaccard) across inference methods
    agg = []
    for a in inf_methods:
        for b in inf_methods:
            u = kept[a] | kept[b]; i = kept[a] & kept[b]
            agg.append({"method_a": a, "method_b": b,
                        "jaccard": (len(i) / len(u)) if u else 1.0})
    return cons, pd.DataFrame(agg), inf_methods


def compact_models(task, arm, cons, mode):
    df, folds = load_raw(), load_folds()
    frame = attach_fold(make_arm_frame(df, arm), folds)
    tr, te = train_test_frames(frame, mode)
    ranked = cons.sort_values("consensus", ascending=False).term.tolist()
    y_te = te.y_cont.values if task == "continuous" else te.y_bin.values
    rows = []
    for k in (1, 2, 3):
        terms = ranked[:k]
        from pipeline.models import _fit_sm_subset
        tf, res, predict, coef = _fit_sm_subset(tr, arm, task, terms)
        pred = predict(te)
        if task == "continuous":
            m = MET.continuous_metrics(y_te, pred)
            rows.append({"n_terms": k, "terms": "+".join(terms), **m})
        else:
            from pipeline.metrics import youden_cutoff
            cut = youden_cutoff(tr.y_bin.values, predict(tr))
            m = MET.binary_metrics(y_te, pred, cut)
            rows.append({"n_terms": k, "terms": "+".join(terms), **m})
    return pd.DataFrame(rows), ranked, tr, te


def stratify_rule(task, arm, ranked, tr, te):
    """Depth-1 threshold on the leading NUMERIC consensus term; report R2 gain."""
    if task != "continuous":
        return None
    numeric = C.numeric_covariates(arm)
    lead = next((t for t in ranked if t in numeric), None)
    if lead is None:
        return None
    x = tr[lead].values.reshape(-1, 1); y = tr.y_cont.values
    stump = DecisionTreeRegressor(max_depth=1, random_state=C.SEED).fit(x, y)
    thr = float(stump.tree_.threshold[0])
    left_mean = y[x.ravel() <= thr].mean(); right_mean = y[x.ravel() > thr].mean()
    better = "<=" if left_mean > right_mean else ">"
    # RF partial dependence curve for the figure
    tf = Transform(arm, kind="tree").fit(tr)
    rf = RandomForestRegressor(n_estimators=400, random_state=C.SEED, n_jobs=C.N_JOBS)
    rf.fit(tf.transform(tr), y)
    grid = np.linspace(tr[lead].min(), tr[lead].max(), 40)
    pd_vals = []
    for g in grid:
        f = tr.copy(); f[lead] = g
        pd_vals.append(float(rf.predict(tf.transform(f)).mean()))
    pdc = pd.DataFrame({"grid": grid, "pd": pd_vals})
    d = os.path.join(C.OUT, "stratify", arm); os.makedirs(d, exist_ok=True)
    pdc.to_csv(os.path.join(d, "partial_dependence.csv"), index=False)
    # compact linear term vs indicator on the test rows
    from pipeline.models import _fit_sm_subset
    y_te = te.y_cont.values
    _, _, pred_lin, _ = _fit_sm_subset(tr, arm, task, [lead])
    r2_lin = MET.continuous_metrics(y_te, pred_lin(te))["R2"]
    ind_name = f"1[{lead} {better} {thr:.3g}]"
    tr2 = tr.copy(); te2 = te.copy()
    ind_tr = (tr[lead].values <= thr) if better == "<=" else (tr[lead].values > thr)
    ind_te = (te[lead].values <= thr) if better == "<=" else (te[lead].values > thr)
    import statsmodels.api as sm
    Xtr = sm.add_constant(ind_tr.astype(float)); res = sm.OLS(y, Xtr).fit()
    pred_ind = res.params[0] + res.params[1] * ind_te.astype(float)
    r2_ind = MET.continuous_metrics(y_te, pred_ind)["R2"]
    enrich_hi = y[ind_tr].mean(); enrich_lo = y[~ind_tr].mean()
    txt = (f"arm: {arm}\n"
           f"leading numeric consensus term: {lead}\n"
           f"data-chosen threshold (depth-1 tree): {lead} {better} {thr:.4g}\n"
           f"enriched subgroup mean improvement: {enrich_hi:.3f}  "
           f"(other subgroup: {enrich_lo:.3f})\n"
           f"subgroup size in training: {int(ind_tr.sum())}/{len(ind_tr)}\n"
           f"test R2, single linear term ({lead}): {r2_lin:+.3f}\n"
           f"test R2, single indicator {ind_name}: {r2_ind:+.3f}\n")
    open(os.path.join(d, "rule.txt"), "w").write(txt)
    return {"arm": arm, "lead": lead, "rule": ind_name, "r2_linear": r2_lin,
            "r2_indicator": r2_ind, "enrich_hi": enrich_hi, "enrich_lo": enrich_lo}


def run(task, mode):
    strat_rows = []
    for arm in C.ARMS:
        cons, agg, _ = consensus_and_agreement(task, arm)
        d = os.path.join(C.OUT, "stratify", arm); os.makedirs(d, exist_ok=True)
        cons.to_csv(os.path.join(C.OUT, "runs", task, "fold5", arm, "consensus.csv"), index=False)
        agg.to_csv(os.path.join(C.OUT, "runs", task, "fold5", arm, "agreement.csv"), index=False)
        board, ranked, tr, te = compact_models(task, arm, cons, mode)
        board.to_csv(os.path.join(C.OUT, "runs", task, "fold5", arm, "compact_scoreboard.csv"), index=False)
        top = cons.head(4).term.tolist()
        print(f"[compact] {task} {arm}: consensus top = {top}")
        s = stratify_rule(task, arm, ranked, tr, te)
        if s:
            strat_rows.append(s)
            print(f"[stratify] {arm}: {s['rule']}  R2 lin={s['r2_linear']:+.3f} ind={s['r2_indicator']:+.3f}")
    if strat_rows:
        pd.DataFrame(strat_rows).to_csv(os.path.join(C.OUT, "stratify", f"summary_{task}.csv"), index=False)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=["continuous", "binary", "both"], default="both")
    ap.add_argument("--mode", choices=["rehearsal", "final"], default=C.MODE)
    a = ap.parse_args()
    for task in (["continuous", "binary"] if a.task == "both" else [a.task]):
        run(task, a.mode)


if __name__ == "__main__":
    main()
