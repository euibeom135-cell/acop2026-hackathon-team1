"""Shared setup for the PDF-faithful six-step DM1 analysis. Uses the main project's REAL locked 80/20 split (results/split_seed42.csv, read-only) and its feature builder (read-only).
Writes only inside pdf_pipeline/. Standardisation: ONLY the numeric covariates are z-scored (never 0/1 dummies); the scaler is re-fitted on each CV fold's training rows (inside the sklearn / R fit),
and on the full TRAIN set for the final test scoring. TEST data are returned only when test=True (called by s07 only)."""
import sys
from pathlib import Path
AROOT = Path(__file__).resolve().parents[1]; MAIN = AROOT.parent
sys.path.insert(0, str(MAIN / "src"))
ARES = AROOT / "results"; ANOTES = AROOT / "notes"; ARES.mkdir(exist_ok=True)
import numpy as np, pandas as pd
from common import ARMS, load
from features import build_features, DOMAIN
from sklearn.model_selection import RepeatedStratifiedKFold

SPLIT_CSV = MAIN / "results" / "split_seed42.csv"      # the genuine locked split (per-arm train/test = Mex 128/33, Oligo 136/34, Tide 135/34)
import os
DRYRUN = os.environ.get("DM1_DRYRUN") == "1"
N_REP, N_FOLD, SEED = 3, 5, 42
rname = lambda c: c.replace("=", "_")
SGN = {"Mexiletine": -1, "Oligonucleotide": 1, "Tideglusib": 1}          # +1: higher outcome = better; Mex: more negative change = better
NUM_FEATS = ["log_ctg", "somatic_mosaicism_index", "age_at_onset", "disease_duration", "myotonia_severity", "muscle_strength", "pr_interval",
             "cognitive_function", "ck_level", "insulin_resistance", "albumin", "bmi"]     # the 13 numeric covariates minus age (age = age_at_onset + disease_duration exactly; log10 applied to ctg_repeats)

def split_table():
    return pd.read_csv(SPLIT_CSV)

def features_all():
    """Baseline feature matrix for all 500 patients (outcome-free: log10 CTG, raw numerics, 0/1 dummies)."""
    df = load().set_index("patient_id", drop=False); X, parent = build_features(df, "raw")
    return df, X.rename(columns=rname), {rname(k): rname(v) for k, v in parent.items()}

def get_arm(arm, test=False):
    """-> dict(Xtr, ytr, ltr, ids_tr, num, [Xte, yte, lte, ids_te]). X are UNSCALED (scaling happens inside each fit); zero-variance train columns dropped; label 1 = Responder."""
    df, X, parent = features_all(); sp = split_table(); sp = sp[sp.arm == arm]; tr = sp[sp.set == "train"].patient_id; te = sp[sp.set == "test"].patient_id
    Xtr = X.loc[tr]; keep = list(Xtr.columns[Xtr.std() > 0]); lab = ARMS[arm]["label"]; y = ARMS[arm]["y"]
    d = dict(Xtr=Xtr[keep], ytr=df.loc[tr, y], ltr=(df.loc[tr, lab] == "Responder").astype(int), ids_tr=tr, num=[c for c in keep if c in NUM_FEATS], parent=parent)
    if test and DRYRUN: te = tr[:30]                       # code-debug mode ONLY (env DM1_DRYRUN=1): the "test" is 30 TRAIN rows, so the real test set is never read while debugging s07
    if test: d.update(Xte=X.loc[te, keep], yte=df.loc[te, y], lte=(df.loc[te, lab] == "Responder").astype(int), ids_te=te)
    return d

def folds(arm, ltr):
    """Repeated stratified 5-fold ids on TRAIN (stratified by responder label); same folds for every method and both outcome types."""
    rk = RepeatedStratifiedKFold(n_splits=N_FOLD, n_repeats=N_REP, random_state=SEED); out = []
    for i, (a, b) in enumerate(rk.split(np.zeros(len(ltr)), ltr.values)): out += [(i // N_FOLD, i % N_FOLD, r) for r in b]
    return pd.DataFrame(out, columns=["rep", "fold", "row"]).sort_values(["rep", "row"]).reset_index(drop=True)
