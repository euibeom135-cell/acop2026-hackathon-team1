"""Read-only loaders for pdf_pipeline/results. Nothing here recomputes a model; features_train_* (train rows only) are used for Step 1-4 descriptive statistics."""
from base import *

def r(name, **kw): return pd.read_csv(RES / name, **kw)
def train(arm): return r(f"features_train_{arm}.csv")
def fmap(arm): return r(f"feature_map_{arm}.csv")
def numcols(arm): return list(fmap(arm).query("numeric").feature)
def dummies(arm): return list(fmap(arm).query("not numeric").feature)
def split(): return pd.read_csv(RES.parents[1] / "results" / "split_seed42.csv")
cv = lambda: r("cv_scoreboard.csv")
prim = lambda: r("primary_selection.csv")
head = lambda: r("test_headlines.csv")
tsb = lambda: r("test_scoreboard.csv")
sig = lambda: r("signal_noise_summary.csv")
NICE = {"log_ctg": "log10 CTG repeats", "somatic_mosaicism_index": "Somatic mosaicism", "age_at_onset": "Age at onset", "disease_duration": "Disease duration",
        "myotonia_severity": "Myotonia severity", "muscle_strength": "Muscle strength", "pr_interval": "PR interval", "cognitive_function": "Cognitive function",
        "ck_level": "Creatine kinase", "insulin_resistance": "Insulin resistance", "albumin": "Albumin", "bmi": "BMI", "sex_Male": "Sex = Male", "cataracts_Yes": "Cataracts = Yes",
        "family_history_Yes": "Family history = Yes", "family_history_Unknown": "Family history = Unknown", "smoking_status_Former": "Smoking = Former",
        "smoking_status_Current": "Smoking = Current", "phenotype_adult_onset": "Phenotype = adult onset", "phenotype_juvenile_onset": "Phenotype = juvenile onset"}
nice = lambda c: NICE.get(c, c)
def lock_ok():
    return (RES / "TEST_SCORED.lock").exists()
