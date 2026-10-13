"""S06a: random-forest held-out permutation importance (observed) vs a shuffled-outcome NULL, TRAIN rows only, for the signal-vs-noise rule (criteria c and d).
Statistic: 5-fold CV; in each fold fit RF(100 trees, min_samples_leaf=5) on the fold's training rows, permutation importance on the held-out rows (2 repeats; reg: RMSE increase, bin: AUC drop); mean over folds.
Null: B=100 permutations of the outcome, same statistic; per-covariate 95th percentile. usage: python s06a_rf_null.py  -> results/signal_rf_<arm>_<task>.csv"""
import warnings; warnings.filterwarnings("ignore")
from joblib import Parallel, delayed
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.inspection import permutation_importance
from pcommon import *
BNULL = 100
def stat(X, y, task, seed):
    cv = KFold(5, shuffle=True, random_state=seed) if task == "reg" else StratifiedKFold(5, shuffle=True, random_state=seed); F = []
    for a, b in cv.split(X, y):
        m = (RandomForestRegressor if task == "reg" else RandomForestClassifier)(100, min_samples_leaf=5, random_state=seed, n_jobs=1).fit(X.iloc[a], y[a])
        F.append(permutation_importance(m, X.iloc[b], y[b], n_repeats=2, scoring="neg_root_mean_squared_error" if task == "reg" else "roc_auc", random_state=seed).importances_mean)
    return np.array(F)                                   # folds x features
for arm in ARMS:
    d = get_arm(arm); X = d["Xtr"].reset_index(drop=True)
    for task in ("reg", "bin"):
        y = (d["ytr"] if task == "reg" else d["ltr"]).values; obs = stat(X, y, task, 0)
        nul = Parallel(n_jobs=-1)(delayed(lambda i: stat(X, np.random.default_rng(1000 + i).permutation(y), task, 1 + i).mean(0))(i) for i in range(BNULL)); nul = np.array(nul)
        pd.DataFrame(dict(covariate=X.columns, rf_imp_mean=obs.mean(0), rf_imp_folds_pos=(obs > 0).sum(0), rf_null95=np.percentile(nul, 95, axis=0))).to_csv(ARES / f"signal_rf_{arm}_{task}.csv", index=False); print("done", arm, task, flush=True)
