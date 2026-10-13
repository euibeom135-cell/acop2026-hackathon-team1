"""S02: repeated 5-fold CV on TRAIN for every ML method (untuned + tuned with inner GridSearchCV); scaler re-fitted inside every fold (pipeline). Also held-out permutation importance (rep 0).
usage: python s02_ml_cv.py <reg|bin>. Output results/ml_<arm>_<task>_cv_preds.csv, _cv_importance.csv, _cv_params.csv. TEST NOT TOUCHED."""
import sys, warnings; warnings.filterwarnings("ignore")
from joblib import Parallel, delayed
from sklearn.inspection import permutation_importance
from pcommon import *
from ml_models import variants, predict
task = sys.argv[1]; arms = sys.argv[2:] or list(ARMS)

def one(vi, rep, fold, tr_rows, te_rows, X, y, task, num):
    nm, build, tuned, r = variants(task, num, list(X.columns))[vi]; m = build().fit(X.iloc[tr_rows], y[tr_rows]); p = predict(m, X.iloc[te_rows], task); imp = None
    if rep == 0: imp = dict(zip(X.columns, permutation_importance(m, X.iloc[te_rows], y[te_rows], n_repeats=5, scoring=r["scoring"], random_state=0).importances_mean))
    return nm, rep, fold, te_rows, p, (m.best_params_ if tuned else None), imp

for arm in arms:
    d = get_arm(arm); X = d["Xtr"].reset_index(drop=True); y = (d["ytr"] if task == "reg" else d["ltr"]).values; fo = folds(arm, d["ltr"]); V = variants(task, d["num"], list(X.columns)); jobs = []
    for vi in range(len(V)):
        for (rep, fold), g in fo.groupby(["rep", "fold"]):
            te = g.row.values; tr = np.setdiff1d(np.arange(len(y)), te); jobs.append((vi, rep, fold, tr, te, X, y, task, d["num"]))
    out = Parallel(n_jobs=-1, verbose=0)(delayed(one)(*j) for j in jobs)
    P = pd.DataFrame([dict(method=nm, rep=rep, row=r_, pred=p_) for nm, rep, f, te, p, bp, imp in out for r_, p_ in zip(te, p)])
    I = pd.DataFrame([dict(method=nm, fold=f, term=k, importance=v) for nm, rep, f, te, p, bp, imp in out if imp for k, v in imp.items()])
    BP = pd.DataFrame([dict(method=nm, rep=rep, fold=f, params=str(bp)) for nm, rep, f, te, p, bp, imp in out if bp])
    P.to_csv(ARES / f"ml_{arm}_{task}_cv_preds.csv", index=False); I.to_csv(ARES / f"ml_{arm}_{task}_cv_importance.csv", index=False); BP.to_csv(ARES / f"ml_{arm}_{task}_cv_params.csv", index=False)
    print("done", arm, task, len(P), flush=True)
