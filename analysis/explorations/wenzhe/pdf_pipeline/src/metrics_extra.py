"""Confusion counts at a stated cutoff (adds TP/FP/FN/TN to metrics.bin_metrics)."""
import numpy as np
def confusion(y, s, cut):
    pred = s >= cut; return dict(TP=int((pred & (y == 1)).sum()), FP=int((pred & (y == 0)).sum()), FN=int((~pred & (y == 1)).sum()), TN=int((~pred & (y == 0)).sum()))
