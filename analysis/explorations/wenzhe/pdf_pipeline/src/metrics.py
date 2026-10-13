"""Metrics + bootstrap helpers (PDF: RMSE/MAE/R2 for continuous; ROC-AUC/recall/precision/accuracy for binary)."""
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve

def reg_metrics(y, p):
    """R2 follows the PDF: relative to predicting the mean of the EVALUATION set (can be negative)."""
    e = y - p; return dict(RMSE=float(np.sqrt(np.mean(e ** 2))), MAE=float(np.mean(np.abs(e))), R2=float(1 - np.sum(e ** 2) / np.sum((y - y.mean()) ** 2)))

def youden_cutoff(y, s):
    f, t, th = roc_curve(y, s); return float(th[np.argmax(t - f)])

def bin_metrics(y, s, cut):
    pred = s >= cut; tp = int((pred & (y == 1)).sum()); fp = int((pred & (y == 0)).sum()); fn = int((~pred & (y == 1)).sum())
    return dict(AUC=float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else np.nan, recall=tp / max(tp + fn, 1), precision=tp / max(tp + fp, 1) if tp + fp else np.nan, accuracy=float((pred == (y == 1)).mean()), n_pred_pos=int(pred.sum()))

def boot_ci(fn, n, B=2000, seed=0):
    """Percentile 95% CI of fn(index_array) over B bootstrap resamples of n patients. NaN draws are dropped."""
    rng = np.random.default_rng(seed); v = np.array([fn(rng.integers(0, n, n)) for _ in range(B)], float); v = v[~np.isnan(v)]
    return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) else (np.nan, np.nan)
