"""Data loading, endpoint orientation, folds, and the raw->design transform.

The transform standardizes numerics using TRAIN statistics only and one-hot
encodes categoricals against fixed level orders (drop-first reference), so a
categorical variable is one *term* (a block of dummy columns). Grouped
permutation importance permutes the raw column and re-transforms, which keeps
the block coherent. GAM uses the same path with spline-expanded numerics.
"""
from __future__ import annotations
import sys, os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(C.INPUT_CSV)
    assert df.shape == (500, 26) and df.patient_id.is_unique
    assert (df.age - df.age_at_onset == df.disease_duration).all()
    return df


def make_arm_frame(df: pd.DataFrame, arm: str) -> pd.DataFrame:
    """Arm subset with oriented continuous target `y_cont` and binary `y_bin`."""
    g = df[df.treatment_arm == arm].copy()
    endpoint = g[C.ENDPOINTS[arm]].astype(float)
    if arm == "Mexiletine" and C.MEX_RELATIVE_TARGET:
        base = g["myotonia_severity"].astype(float)
        # relative improvement = -change / baseline; baseline 0 -> no change -> 0
        rel = np.where(base > 0, -endpoint / base.where(base > 0, 1.0), 0.0)
        g["y_cont"] = rel
    else:
        g["y_cont"] = C.SIGN[arm] * endpoint
    g["y_bin"] = (g[C.RESPONDER[arm]] == "Responder").astype(int)
    keep = ["patient_id", "treatment_arm", "y_cont", "y_bin"] + C.NUMERIC_ALL + C.CATEGORICAL
    return g[keep].reset_index(drop=True)


# --------------------------------------------------------------------------
# Folds
# --------------------------------------------------------------------------
def load_folds() -> pd.DataFrame:
    path = os.path.join(C.DATA_DIR, "folds_5fold_seed2026.csv")
    return pd.read_csv(path)


def attach_fold(frame: pd.DataFrame, folds: pd.DataFrame) -> pd.DataFrame:
    m = dict(zip(folds.patient_id, folds.fold))
    out = frame.copy()
    out["fold"] = out.patient_id.map(m)
    assert out.fold.notna().all(), "patient missing a fold assignment"
    out["fold"] = out.fold.astype(int)
    return out


def train_test_frames(frame_with_fold: pd.DataFrame, mode: str):
    """mode 'rehearsal': train folds 2-4, test fold 5 (fold 1 untouched).
    mode 'final': train folds 2-5, test fold 1 (the locked test)."""
    f = frame_with_fold
    if mode == "rehearsal":
        tr = f[f.fold.isin([2, 3, 4])].copy()
        te = f[f.fold == 5].copy()
    elif mode == "final":
        tr = f[f.fold.isin([2, 3, 4, 5])].copy()
        te = f[f.fold == 1].copy()
    else:
        raise ValueError(mode)
    return tr.reset_index(drop=True), te.reset_index(drop=True)


# --------------------------------------------------------------------------
# Raw -> design transform
# --------------------------------------------------------------------------
from sklearn.preprocessing import SplineTransformer


class Transform:
    """Fit numeric z-scaling and categorical dummy layout on a training frame.

    kind='linear' : standardized numerics + drop-first dummies (OLS/GLM/penalized)
    kind='tree'   : identical columns (trees ignore scaling; keeps names aligned)
    kind='spline' : each numeric -> cubic B-spline basis (GAM), dummies as linear
    """

    def __init__(self, arm: str, kind: str = "linear", n_knots: int = 5):
        self.arm = arm
        self.kind = kind
        self.n_knots = n_knots
        self.numeric = C.numeric_covariates(arm)
        self.categorical = list(C.CATEGORICAL)
        self.raw_terms = self.numeric + self.categorical

    def fit(self, train: pd.DataFrame):
        self.mean_ = {c: float(train[c].mean()) for c in self.numeric}
        self.sd_ = {c: (float(train[c].std(ddof=0)) or 1.0) for c in self.numeric}
        # fixed, data-independent dummy columns (reference = first level)
        self.cat_cols_ = {}
        for c in self.categorical:
            levels = C.LEVELS[c]
            self.cat_cols_[c] = levels[1:]  # drop first as reference
        if self.kind == "spline":
            self.splines_ = {}
            for c in self.numeric:
                st = SplineTransformer(n_knots=self.n_knots, degree=3,
                                       include_bias=False)
                z = ((train[c].astype(float) - self.mean_[c]) / self.sd_[c]).values.reshape(-1, 1)
                st.fit(z)
                self.splines_[c] = st
        self._build_names()
        return self

    def _build_names(self):
        names, term_cols = [], {}
        j = 0
        for c in self.numeric:
            if self.kind == "spline":
                k = self.splines_[c].transform(np.zeros((1, 1))).shape[1]
                cols = list(range(j, j + k)); j += k
                names += [f"{c}_s{i}" for i in range(k)]
            else:
                cols = [j]; names.append(c); j += 1
            term_cols[c] = cols
        for c in self.categorical:
            cols = []
            for lv in self.cat_cols_[c]:
                names.append(f"{c}={lv}"); cols.append(j); j += 1
            term_cols[c] = cols
        self.feature_names_ = names
        self.term_cols_ = term_cols

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        blocks = []
        for c in self.numeric:
            z = ((frame[c].astype(float) - self.mean_[c]) / self.sd_[c]).values.reshape(-1, 1)
            blocks.append(self.splines_[c].transform(z) if self.kind == "spline" else z)
        for c in self.categorical:
            for lv in self.cat_cols_[c]:
                blocks.append((frame[c].values == lv).astype(float).reshape(-1, 1))
        return np.hstack(blocks) if blocks else np.empty((len(frame), 0))
