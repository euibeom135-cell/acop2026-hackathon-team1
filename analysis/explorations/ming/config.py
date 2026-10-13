"""DM1 covariate pipeline — single source of truth (frozen at G2).

Every script imports from here. The orchestrator flips MODE at G3 only.
Decisions encoded below are the G1 "six data decisions"; see docs/LOG.md.
"""
from __future__ import annotations
import os

# ----------------------------------------------------------------------------
# MODE: 'rehearsal' trains on folds 2-4 and scores fold 5 (pseudo-test); it
# NEVER opens fold 1. 'final' trains on folds 2-5 and scores fold 1 (the locked
# test), once, at G3. Override with env DM1_MODE for a one-off run.
# ----------------------------------------------------------------------------
MODE = os.environ.get("DM1_MODE", "rehearsal")
assert MODE in ("rehearsal", "final"), f"bad MODE {MODE!r}"

SEED = 2026
OCT11_SEED = 20261011  # the seed that produced the locked Oct 11 partition

ARMS = ["Mexiletine", "Oligonucleotide", "Tideglusib"]

# All 18 baseline covariates as supplied.
NUMERIC_ALL = [
    "ctg_repeats", "somatic_mosaicism_index", "age", "age_at_onset",
    "disease_duration", "myotonia_severity", "muscle_strength", "pr_interval",
    "cognitive_function", "ck_level", "insulin_resistance", "albumin", "bmi",
]
CATEGORICAL = ["phenotype", "sex", "family_history", "cataracts", "smoking_status"]

# G1 decision #2 (collinear axis): disease_duration = age - age_at_onset exactly
# in all 500 rows, so the three linear terms cannot be jointly estimated. Drop
# the derived sum (age); keep age_at_onset and disease_duration, the two
# mechanistically primary DM1 axes.
DROP_GLOBAL = ["age"]

# G1 decision #1: albumin is constant (4.18) for every Mexiletine patient.
DROP_PER_ARM = {"Mexiletine": ["albumin"]}

def numeric_covariates(arm: str) -> list[str]:
    drop = set(DROP_GLOBAL) | set(DROP_PER_ARM.get(arm, []))
    return [c for c in NUMERIC_ALL if c not in drop]

def covariates(arm: str) -> list[str]:
    """Model covariates for an arm: numerics (standardized) + categoricals (block)."""
    return numeric_covariates(arm) + CATEGORICAL

ENDPOINTS = {
    "Mexiletine": "myotonia_change_12wk",
    "Oligonucleotide": "qmt_change_26wk",
    "Tideglusib": "tideglusib_composite",
}
RESPONDER = {
    "Mexiletine": "responder_phenotype_mex",
    "Oligonucleotide": "responder_phenotype_oligo",
    "Tideglusib": "responder_phenotype_tidge",
}
# Orientation so that higher improvement_score always means more improvement.
SIGN = {"Mexiletine": -1, "Oligonucleotide": 1, "Tideglusib": 1}

# G1 decision #4: Mexiletine's continuous target is RELATIVE myotonia
# improvement (-change / baseline myotonia), because the 45% responder rule is
# built on the relative scale and absolute change is mechanically explained by
# baseline severity. Verified: the 0.45 cutoff reproduces the responder label
# exactly (TP=47, FP=0, FN=0). Other arms use the oriented absolute endpoint.
MEX_RELATIVE_TARGET = True

LEVELS = {
    "phenotype": ["juvenile_onset", "adult_onset", "late_onset"],
    "sex": ["Female", "Male"],
    "family_history": ["No", "Unknown", "Yes"],   # Unknown kept as its own level
    "cataracts": ["No", "Yes"],
    "smoking_status": ["Never", "Former", "Current"],
}

LABELS = {
    "ctg_repeats": "CTG repeats", "somatic_mosaicism_index": "Somatic mosaicism",
    "age": "Age", "age_at_onset": "Age at onset", "disease_duration": "Disease duration",
    "myotonia_severity": "Myotonia severity", "muscle_strength": "Muscle strength",
    "pr_interval": "PR interval", "cognitive_function": "Cognition",
    "ck_level": "CK", "insulin_resistance": "Insulin resistance (HOMA-IR)",
    "albumin": "Albumin", "bmi": "BMI", "phenotype": "Phenotype", "sex": "Sex",
    "family_history": "Family history", "cataracts": "Cataracts",
    "smoking_status": "Smoking status",
}

# ----------------------------------------------------------------------------
# Compute knobs. Rehearsal trims the expensive loops so the whole pipeline
# finishes fast enough to iterate; final restores full counts. Any reduction is
# recorded in docs/LOG.md and the report.
# ----------------------------------------------------------------------------
BOOTSTRAP = 1000          # test-metric bootstrap resamples
CV_SPLITS = 5             # inner CV folds for tuning / OOF cutoff
CV_REPEATS = 3 if MODE == "final" else 2
STABILITY_SUBSAMPLES = 100
NULL_PERMUTATIONS = 50
REPEAT_SEEDS = 20         # repeat20 sensitivity scheme
PERM_IMPORTANCE_REPEATS = 20
TOP_K_IMPORTANCE = 5
N_JOBS = 4

# Consensus / stability thresholds
CONSENSUS_FRACTION = 0.5          # selected by >=50% of inference methods -> consensus
STABILITY_THRESHOLD = 0.6         # stability-selection frequency for a "stable" term
NULL_QUANTILE = 0.95              # importance must beat this quantile of the null

SCHEMES = ["fold5", "single80", "single75", "repeat20"]

# Paths
ROOT = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(ROOT, "inputs", "dm1_clinical_trial_dataset.csv")
DATA_DIR = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "outputs")
DOCS = os.path.join(ROOT, "docs")
