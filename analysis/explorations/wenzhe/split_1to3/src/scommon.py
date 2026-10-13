"""Shared setup for the 1:3-split, covariate-re-randomised replication of the all-methods analysis. Self-contained split + TRAIN-only preprocessing.
Reads the main project's feature builder (read-only); writes only inside split_1to3/. TEST data returned only when test=True (s06)."""
import sys, json
from pathlib import Path
AROOT = Path(__file__).resolve().parents[1]; MAIN = AROOT.parent
sys.path.insert(0, str(MAIN / "src"))
ARES = AROOT / "results"; AREP = AROOT / "reports"; ANOTES = AROOT / "notes"
import numpy as np, pandas as pd
from common import ARMS, load, NUMERIC, CATEGORICAL
from features import build_features
from sklearn.model_selection import RepeatedStratifiedKFold

TEST_FRAC = 0.25                                     # 1:3 test:train
N_REP, N_FOLD, SEED = 3, 5, 42
rname = lambda c: c.replace("=", "_")
SGN = {"Mexiletine": -1, "Oligonucleotide": 1, "Tideglusib": 1}
N_BINS = 4                                           # outcome quantile bins used as split strata (PDF: bin a continuous outcome)

def split_table():
    return pd.read_csv(ARES / "split_1to3.csv")

def features_all():
    """Baseline feature matrix for all 500 patients (no fitted parameters: log10 CTG, dummies; age omitted because age = onset + duration)."""
    df = load().set_index("patient_id", drop=False); X, parent = build_features(df, "raw"); return df, X

def get_arm(arm, test=False, split=None):
    """-> dict(Ztr, ytr, ltr, base_tr, [Zte, yte, lte, rte]). Z standardised with TRAIN mean/sd (zero-variance columns dropped); labels 1 = Responder; R-safe names."""
    df, X = features_all(); sp = split_table() if split is None else split; sp = sp[sp.arm == arm]; tr_ids = sp[sp.set == "train"].patient_id; te_ids = sp[sp.set == "test"].patient_id
    Xtr = X.loc[tr_ids]; keep = Xtr.columns[Xtr.std() > 0]; Xtr = Xtr[keep]; mu, sd = Xtr.mean(), Xtr.std(ddof=0); Z = lambda M: ((M[keep] - mu) / sd).rename(columns=rname)
    lab = ARMS[arm]["label"]; y = ARMS[arm]["y"]
    d = dict(Ztr=Z(Xtr), ytr=df.loc[tr_ids, y], ltr=(df.loc[tr_ids, lab] == "Responder").astype(int), base_tr=df.loc[tr_ids, "myotonia_severity"], ids_tr=tr_ids)
    if test: d.update(Zte=Z(X.loc[te_ids]), yte=df.loc[te_ids, y], lte=(df.loc[te_ids, lab] == "Responder").astype(int), rte=df.loc[te_ids], ids_te=te_ids)
    return d

def folds(arm, ltr):
    """Repeated stratified 5-fold ids on TRAIN (stratified by responder label); same folds for every method and both outcome types."""
    rk = RepeatedStratifiedKFold(n_splits=N_FOLD, n_repeats=N_REP, random_state=SEED); out = []
    for i, (a, b) in enumerate(rk.split(np.zeros(len(ltr)), ltr.values)): out += [(i // N_FOLD, i % N_FOLD, r) for r in b]
    return pd.DataFrame(out, columns=["rep", "fold", "row"]).sort_values(["rep", "row"]).reset_index(drop=True)
