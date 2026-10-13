"""Train-only descriptive traits shared by Step 1 and Step 4 (correlation pairs, VIF). Pure descriptive statistics of covariates; no outcome used."""
from data import *

def design(arm):
    d = train(arm); cols = numcols(arm) + dummies(arm); return d, cols

def corr(arm, numeric_only=True):
    d, cols = design(arm); c = numcols(arm) if numeric_only else cols
    return d[c].corr()

def pairs(arm, thr=0.5, numeric_only=False):
    c = corr(arm, numeric_only); out = []
    for i, a in enumerate(c.columns):
        for b in c.columns[i + 1:]:
            if abs(c.loc[a, b]) >= thr: out.append((a, b, c.loc[a, b]))
    return pd.DataFrame(out, columns=["a", "b", "r"]).sort_values("r", key=abs, ascending=False)

def vif(arm):
    """VIF_j = diag of inverse correlation matrix of the full design (numeric + dummy columns), TRAIN rows."""
    c = corr(arm, numeric_only=False).values; return pd.Series(np.diag(np.linalg.inv(c)), index=corr(arm, False).columns)
