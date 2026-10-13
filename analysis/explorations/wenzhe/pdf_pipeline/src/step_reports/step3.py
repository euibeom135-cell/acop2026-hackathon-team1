"""Step 3 page: Preprocess only what each method needs; leakage rule (split first / fit on train / apply to test)."""
from data import *

def design_dims():
    sp = split(); rows = []
    for a in ARMS:
        d = train(a); n_te = int((sp[sp.arm == a].set == "test").sum()); nn, nd = len(numcols(a)), len(dummies(a))
        rows.append({"Arm": a, "Train matrix": f"{len(d)} x {nn + nd}", "Test matrix (same columns)": f"{n_te} x {nn + nd}", "z-scored numeric": nn, "0/1 dummies (not scaled)": nd,
                     "Missing values (train)": int(d[numcols(a) + dummies(a)].isna().sum().sum()), "Dropped": "age (= onset + duration), albumin (constant in train)" if a == "Mexiletine" else "age (= onset + duration)"})
    return pd.DataFrame(rows)

def scaler_stats(arm):
    d = train(arm); c = numcols(arm)
    return pd.DataFrame({"Column": [nice(x) for x in c], "Train mean": [d[x].mean() for x in c], "Train SD (ddof=0)": [d[x].std(ddof=0) for x in c]})

def method_needs():
    return pd.DataFrame([
        ("lm / glm, stepwise-BIC, best subset", "yes (dummies)", "not required (only changes coefficient units); done so every method sees one matrix"),
        ("Ridge, LASSO, elastic net", "yes", "required: the penalty depends on column scale; glmnet is called with standardize=FALSE on the z-scored matrix, so dummies keep their 0/1 scale"),
        ("GAM (s(k=5), REML)", "yes", "numeric columns enter as smooths on the z-scored matrix; dummies linear"),
        ("PCA / PCR", "yes", "required: components follow variance; PCA on the z-scored numeric and 0/1 columns as built"),
        ("Logistic regression, SVM (RBF), KNN, MLP", "yes", "required: distance- or gradient-based"),
        ("Decision tree, random forest, XGBoost", "yes", "not needed (split-based, invariant to per-column rescaling); they are given the same z-scored matrix for comparability")],
        columns=["Methods", "Dummy coding", "Scaling"])

def build():
    D = design_dims(); N = method_needs()
    T = pd.DataFrame([("CTG repeat count", "log10 transform", "Repeat counts are multiplicative in scale; a scale choice made before fitting, not fitted to the outcome."),
        ("age", "dropped", "age = age_at_onset + disease_duration exactly (max abs difference 0): perfectly collinear."),
        ("albumin (Mexiletine only)", "dropped", "Single constant value in the Mexiletine train rows (zero variance); kept in the other two arms."),
        ("sex, cataracts, family history, smoking, phenotype", "0/1 dummies", "Family history has a separate 'Unknown' level. Dummies are NOT standardised."),
        ("12 numeric columns (11 in Mexiletine)", "z-score: (x - train mean) / train SD", "Re-fitted on the training part of every CV fold (a scaler inside each sklearn Pipeline / each R fit, also inside the inner grid-search folds); fitted once on the full TRAIN set for the single test scoring."),
        ("Missing values / outliers", "none to treat / none removed", "No missing values in the feature matrices; extreme values are plausible clinical values and are kept.")], columns=["Item", "Transformation", "Why / how"])
    R = req([("Preprocess only what the chosen method needs", "Table 3.2: what each method family needs; trees/forests/XGBoost need no scaling but get the same matrix so all methods see identical inputs", "3.2"),
             ("Leakage rule 1: split first, before any preprocessing", "The split (Step 2) exists before any scaling or encoding is fitted", "3.1"),
             ("Leakage rule 2: fit on train only", "Means/SDs come from training rows only; inside CV from each fold's training part", "3.1"),
             ("Leakage rule 3: apply to test, never refit on test", "For the single test scoring the scaler fitted on full TRAIN is applied unchanged to test rows", "3.1, 3.4")])
    body = f"""{R}<h2>3.1 What was done</h2>{tbl(T)}
<h2>3.2 Which methods need which preprocessing</h2>{tbl(N)}
{note("Trees, random forests and XGBoost are invariant to per-column affine rescaling, so scaling is not needed for them; they simply receive the same z-scored matrix so that all methods are compared on identical inputs. This is stated, not tuned.")}
<h2>3.3 Final design matrix per arm</h2>{tbl(D)}
<details><summary>Stored scaler statistics (full-train mean and SD per numeric column)</summary>{''.join(tbl(scaler_stats(a), cap=a) for a in ARMS)}</details>
<h2>3.4 Leakage check</h2>
<p>Leakage is prevented by construction: the scaler lives inside each model pipeline (sklearn) or inside each fit (R), so it is re-estimated on the training part of every fold and never sees validation or test rows. A numerical check of test covariates scaled with the train scaler is <b>not part of results/</b> and was not computed here, because producing it would mean opening the test covariates before Step 6.</p>"""
    return page(2, "Preprocess only what each method needs", "Split first, fit preprocessing on train only, apply the fitted steps to test. Only numeric columns are z-scored; 0/1 dummies are left as they are.", body)
