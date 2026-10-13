"""Load out-of-fold (CV) predictions from the R and sklearn sides into one long table: method, family, rep, row, pred."""
from scommon import *
COV_ML = lambda nm: "ML" if any(k in nm for k in ("Decision tree", "Random forest", "SVM", "KNN", "XGBoost", "MLP", "Logistic regression")) else "Covariate"
def load_cv(arm, task):
    r = pd.read_csv(ARES / f"r_{arm}_{task}_cv_preds.csv"); m = pd.read_csv(ARES / f"ml_{arm}_{task}_cv_preds.csv"); P = pd.concat([r, m], ignore_index=True)
    P["family"] = P.method.map(COV_ML); return P
def baseline_cv(ytr, fo, task):
    """Mean-only (reg) / prevalence-only (bin) out-of-fold predictions on the same folds."""
    rows = []
    for (rep, fold), g in fo.groupby(["rep", "fold"]):
        te = g.row.values; tr = np.setdiff1d(np.arange(len(ytr)), te); rows += [("Mean only" if task == "reg" else "Prevalence only", rep, i, float(ytr[tr].mean())) for i in te]
    return pd.DataFrame(rows, columns=["method", "rep", "row", "pred"]).assign(family="Baseline")
