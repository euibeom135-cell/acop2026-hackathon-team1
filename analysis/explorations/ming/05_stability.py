#!/usr/bin/env python3
"""Separate real signal from noise, per arm/task.

(1) Stability selection: 100 half-subsamples of the training set, LASSO
    (continuous) / L1-logistic (binary) at a FIXED penalty (chosen once by CV
    on the full training set); selection frequency per term.
(2) Shuffled-outcome null: random-forest grouped permutation importance on the
    training set, versus the pooled importance when the outcome is shuffled
    (50 permutations). A term beats noise if its observed importance exceeds the
    95th percentile of the null.
Verdict combines the two: "real" if stable (freq>=0.6) AND beats the null.
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
from sklearn.linear_model import Lasso, LassoCV, LogisticRegression, LogisticRegressionCV
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier


def _terms_from_coef(tf, coef_vec):
    return {t for t, cols in tf.term_cols_.items() if np.any(np.abs(coef_vec[cols]) > 1e-8)}


def stability_selection(train, arm, task, rng):
    tf = Transform(arm, kind="linear").fit(train)
    X = tf.transform(train)
    y = train.y_cont.values if task == "continuous" else train.y_bin.values
    # fixed penalty from one CV fit on the full training set
    if task == "continuous":
        alpha = LassoCV(cv=5, random_state=C.SEED, max_iter=50000).fit(X, y).alpha_
        make = lambda: Lasso(alpha=alpha, max_iter=50000)
    else:
        Cbest = LogisticRegressionCV(Cs=np.logspace(-3, 3, 15), cv=5, penalty="l1",
                                     solver="liblinear", scoring="roc_auc",
                                     max_iter=5000).fit(X, y).C_[0]
        make = lambda: LogisticRegression(C=Cbest, penalty="l1", solver="liblinear", max_iter=5000)
    counts = {t: 0 for t in tf.raw_terms}
    n = len(train); half = n // 2
    for _ in range(C.STABILITY_SUBSAMPLES):
        idx = rng.choice(n, half, replace=False)
        if task == "binary" and len(np.unique(y[idx])) < 2:
            continue
        est = make().fit(X[idx], y[idx])
        coef = est.coef_.ravel()
        for t in _terms_from_coef(tf, coef):
            counts[t] += 1
    freq = {t: counts[t] / C.STABILITY_SUBSAMPLES for t in counts}
    return freq


def rf_grouped_importance(est, tf, frame, y, task, rng, repeats=10):
    X = tf.transform(frame)
    base = est.score(X, y) if task == "continuous" else _auc(est, X, y)
    imp = {}
    for t in tf.raw_terms:
        drops = []
        for _ in range(repeats):
            fp = frame.copy()
            fp[t] = rng.permutation(fp[t].values)
            Xp = tf.transform(fp)
            s = est.score(Xp, y) if task == "continuous" else _auc(est, Xp, y)
            drops.append(base - s)
        imp[t] = float(np.mean(drops))
    return imp


def _auc(est, X, y):
    from sklearn.metrics import roc_auc_score
    p = est.predict_proba(X)[:, 1]
    return roc_auc_score(y, p) if len(np.unique(y)) > 1 else np.nan


def shuffled_null(train, arm, task, rng):
    tf = Transform(arm, kind="tree").fit(train)
    X = tf.transform(train)
    y = train.y_cont.values if task == "continuous" else train.y_bin.values
    RF = RandomForestRegressor if task == "continuous" else RandomForestClassifier
    est = RF(n_estimators=400, random_state=C.SEED, n_jobs=C.N_JOBS).fit(X, y)
    obs = rf_grouped_importance(est, tf, train, y, task, rng, repeats=10)
    null_pool = []
    for _ in range(C.NULL_PERMUTATIONS):
        ys = rng.permutation(y)
        e = RF(n_estimators=200, random_state=C.SEED, n_jobs=C.N_JOBS).fit(X, ys)
        imp = rf_grouped_importance(e, tf, train, ys, task, rng, repeats=4)
        null_pool.extend(imp.values())
    q95 = float(np.quantile(null_pool, C.NULL_QUANTILE))
    return obs, q95


def run(task, mode):
    df, folds = load_raw(), load_folds()
    rng = np.random.default_rng(C.SEED)
    for arm in C.ARMS:
        frame = attach_fold(make_arm_frame(df, arm), folds)
        tr, _ = train_test_frames(frame, mode)
        freq = stability_selection(tr, arm, task, rng)
        obs, q95 = shuffled_null(tr, arm, task, rng)
        rows = []
        for t in Transform(arm).raw_terms:
            stable = freq[t] >= C.STABILITY_THRESHOLD
            beats = obs[t] > q95
            rows.append({"term": t, "stability_freq": freq[t], "stable": stable,
                         "rf_importance": obs[t], "null_q95": q95, "beats_null": beats,
                         "verdict": "real signal" if (stable and beats) else
                                    ("suggestive" if (stable or beats) else "noise")})
        out = pd.DataFrame(rows).sort_values("stability_freq", ascending=False)
        d = os.path.join(C.OUT, "stability", task, arm)
        os.makedirs(d, exist_ok=True)
        out.to_csv(os.path.join(d, "stability.csv"), index=False)
        real = out[out.verdict == "real signal"].term.tolist()
        print(f"[stability] {task} {arm}: real signal = {real}")


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
