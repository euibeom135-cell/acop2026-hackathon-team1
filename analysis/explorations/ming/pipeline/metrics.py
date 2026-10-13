"""Scoring, bootstrap intervals, OOF cutoff selection, grouped permutation."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.metrics import (r2_score, mean_squared_error, mean_absolute_error,
                             roc_auc_score, recall_score, precision_score,
                             accuracy_score)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C


def continuous_metrics(y, yhat) -> dict:
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    return {
        "R2": float(r2_score(y, yhat)),
        "RMSE": float(np.sqrt(mean_squared_error(y, yhat))),
        "MAE": float(mean_absolute_error(y, yhat)),
    }


def youden_cutoff(y, proba) -> float:
    """Cutoff that maximizes Youden's J on (OOF) predictions."""
    y = np.asarray(y, int); proba = np.asarray(proba, float)
    if len(np.unique(y)) < 2:
        return 0.5
    thr = np.unique(proba)
    best, best_j = 0.5, -np.inf
    P, N = (y == 1).sum(), (y == 0).sum()
    for t in thr:
        pred = (proba >= t).astype(int)
        tpr = ((pred == 1) & (y == 1)).sum() / P if P else 0
        fpr = ((pred == 1) & (y == 0)).sum() / N if N else 0
        j = tpr - fpr
        if j > best_j:
            best_j, best = j, float(t)
    return best


def binary_metrics(y, proba, cutoff) -> dict:
    y = np.asarray(y, int); proba = np.asarray(proba, float)
    pred = (proba >= cutoff).astype(int)
    out = {"cutoff": float(cutoff)}
    out["ROC_AUC"] = float(roc_auc_score(y, proba)) if len(np.unique(y)) > 1 else float("nan")
    out["Recall"] = float(recall_score(y, pred, zero_division=0))
    out["Precision"] = float(precision_score(y, pred, zero_division=0))
    out["Accuracy"] = float(accuracy_score(y, pred))
    return out


def bootstrap_ci(y, pred, kind, cutoff=None, B=None, seed=C.SEED):
    """Percentile bootstrap over test rows for each metric."""
    B = B or C.BOOTSTRAP
    rng = np.random.default_rng(seed)
    y = np.asarray(y); pred = np.asarray(pred); n = len(y)
    acc = {}
    for _ in range(B):
        ix = rng.integers(0, n, n)
        yb, pb = y[ix], pred[ix]
        if kind == "continuous":
            if np.ptp(yb) == 0:
                continue
            m = continuous_metrics(yb, pb)
        else:
            if len(np.unique(yb)) < 2:
                continue
            m = binary_metrics(yb, pb, cutoff)
            m.pop("cutoff", None)
        for k, v in m.items():
            acc.setdefault(k, []).append(v)
    ci = {}
    for k, vals in acc.items():
        vals = np.asarray(vals, float)
        vals = vals[np.isfinite(vals)]
        if len(vals):
            ci[k] = (float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975)))
    return ci


def grouped_permutation_importance(predict_fn, test_frame, y, raw_terms, kind,
                                   cutoff=None, repeats=None, seed=C.SEED):
    """Permute each raw term (categoricals as a block) in the test frame and
    measure the drop in the headline metric (R2 for continuous, ROC-AUC for
    binary). Returns {term: mean_importance}."""
    repeats = repeats or C.PERM_IMPORTANCE_REPEATS
    rng = np.random.default_rng(seed)
    base_pred = predict_fn(test_frame)
    if kind == "continuous":
        base = continuous_metrics(y, base_pred)["R2"]
        metric = lambda p: continuous_metrics(y, p)["R2"]
    else:
        base = binary_metrics(y, base_pred, cutoff)["ROC_AUC"]
        metric = lambda p: binary_metrics(y, p, cutoff)["ROC_AUC"]
    imp = {}
    for term in raw_terms:
        drops = []
        for _ in range(repeats):
            fp = test_frame.copy()
            fp[term] = rng.permutation(fp[term].values)
            drops.append(base - metric(predict_fn(fp)))
        imp[term] = float(np.mean(drops))
    return imp, float(base)
