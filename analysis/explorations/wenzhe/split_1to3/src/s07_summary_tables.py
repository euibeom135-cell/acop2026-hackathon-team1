"""S07a: derived summary tables: (1) best covariate vs best ML model chosen by TRAIN CV only, scored on test with paired bootstrap difference; (2) tuned-vs-untuned; (3) cutoff sensitivity;
(4) CV-vs-test agreement; (5) cross-check with main step 5. Outputs results/sum_*.csv"""
from scommon import *
from metrics import *
cv = pd.read_csv(ARES / "cv_scoreboard.csv"); ts = pd.read_csv(ARES / "test_scoreboard.csv"); tp = pd.read_csv(ARES / "test_predictions.csv")
rows = []
for arm in ARMS:
    for task, key, asc in (("reg", "RMSE", True), ("bin", "AUC", False)):
        c = cv[(cv.arm == arm) & (cv.task == task) & cv.family.isin(["Covariate", "ML"])].dropna(subset=[key]); pick = {}
        for fam in ("Covariate", "ML"): g = c[c.family == fam].sort_values(key, ascending=asc); pick[fam] = g.iloc[0]
        P = tp[(tp.arm == arm) & (tp.task == task)]; a = P[P.method == pick["Covariate"].method].sort_values("row"); b = P[P.method == pick["ML"].method].sort_values("row"); y = a.obs.values; n = len(y)
        if task == "reg":
            f = lambda i: np.sqrt(np.mean((y[i] - b.pred.values[i]) ** 2)) - np.sqrt(np.mean((y[i] - a.pred.values[i]) ** 2))      # >0: covariate better
        else:
            f = lambda i: roc_auc_score(y[i], a.pred.values[i]) - roc_auc_score(y[i], b.pred.values[i]) if 0 < y[i].sum() < len(i) else np.nan     # >0: covariate better
        lo, hi = boot_ci(f, n, 2000); pt = f(np.arange(n))
        tcov = ts[(ts.arm == arm) & (ts.task == task) & (ts.method == pick["Covariate"].method)].iloc[0]; tml = ts[(ts.arm == arm) & (ts.task == task) & (ts.method == pick["ML"].method)].iloc[0]
        rows.append(dict(arm=arm, task=task, metric=key, cov_method=pick["Covariate"].method, cov_cv=pick["Covariate"][key], cov_test=tcov[key], ml_method=pick["ML"].method, ml_cv=pick["ML"][key], ml_test=tml[key],
                         test_diff_cov_better=pt, diff_lo=lo, diff_hi=hi))
pd.DataFrame(rows).to_csv(ARES / "sum_cov_vs_ml.csv", index=False); print(pd.DataFrame(rows).round(3).to_string(index=False))
# tuned vs untuned
tu = []
for df_, nm in ((cv, "cv"), (ts, "test")):
    d = df_[df_.family == "ML"].copy(); d["tuned"] = d.method.str.contains(r"\(tuned"); d["base"] = d.method.str.replace(r" \((un)?tuned.*\)", "", regex=True)
    for (arm, task, base), g in d.groupby(["arm", "task", "base"]):
        key = "RMSE" if task == "reg" else "AUC"
        if g.tuned.nunique() == 2: tu.append(dict(set=nm, arm=arm, task=task, model=base, untuned=g[~g.tuned][key].iloc[0], tuned=g[g.tuned][key].iloc[0]))
T = pd.DataFrame(tu); T["tuned_better"] = np.where(T.task == "reg", T.tuned < T.untuned, T.tuned > T.untuned); T.to_csv(ARES / "sum_tuned_vs_untuned.csv", index=False)
print(T.groupby(["set", "task"]).tuned_better.agg(["mean", "size"]))
# cutoff sensitivity (bin): test metrics at 0.5 vs train-OOF Youden
cs = []
for (arm, m), g in tp[tp.task == "bin"].groupby(["arm", "method"]):
    g = g.sort_values("row"); yy = g.obs.values; r = ts[(ts.arm == arm) & (ts.task == "bin") & (ts.method == m)].iloc[0]
    if m == "Prevalence only": continue
    m5 = bin_metrics(yy, g.pred.values, 0.5); cs.append(dict(arm=arm, method=m, rec_youden=r.recall, prec_youden=r.precision, acc_youden=r.accuracy, rec_05=m5["recall"], prec_05=m5["precision"], acc_05=m5["accuracy"]))
pd.DataFrame(cs).to_csv(ARES / "sum_cutoff.csv", index=False)
# CV-vs-test agreement
ag = []
for arm in ARMS:
    for task, key in (("reg", "RMSE"), ("bin", "AUC")):
        m = cv[(cv.arm == arm) & (cv.task == task)][["method", key]].merge(ts[(ts.arm == arm) & (ts.task == task)][["method", key]], on="method", suffixes=("_cv", "_test")); from scipy.stats import spearmanr
        ag.append(dict(arm=arm, task=task, spearman=spearmanr(m[key + "_cv"], m[key + "_test"]).statistic, n_methods=len(m)))
pd.DataFrame(ag).to_csv(ARES / "sum_cv_test_agreement.csv", index=False); print(pd.DataFrame(ag).round(2))
