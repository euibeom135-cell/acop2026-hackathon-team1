"""S05: choose each arm's PRIMARY covariate model and PRIMARY ML model by TRAIN CV ONLY (reg: lowest CV RMSE; bin: highest CV ROC-AUC; Baselines excluded, ML pool = tuned + untuned rows).
Writes results/primary_selection.csv (selection + the CV metric that drove it + baseline CV metric) and results/covariate_use_<arm>_<task>.csv (CV selection frequency of each covariate by method).
The test set is not read here and no test result exists yet."""
from pcommon import *
from io_preds import ML_KEYS
S = pd.read_csv(ARES / "cv_scoreboard.csv"); rows = []
for arm in ARMS:
    for task, key, asc in (("reg", "RMSE", True), ("bin", "AUC", False)):
        t = S[(S.arm == arm) & (S.task == task)]; base = t[t.family == "Baseline"].iloc[0]
        for fam in ("Covariate", "ML"):
            g = t[t.family == fam].dropna(subset=[key]).sort_values(key, ascending=asc); b = g.iloc[0]; second = g.iloc[1]
            rows.append(dict(arm=arm, task=task, track=fam, primary_method=b.method, rule=f"{'lowest' if asc else 'highest'} repeated-5x3 CV {key} on TRAIN", cv_metric=key, cv_value=b[key], cv_sd=b[key + "_sd"],
                             runner_up=second.method, runner_up_value=second[key], baseline_method=base.method, baseline_cv_value=base[key], beats_baseline_in_cv=bool(b[key] < base[key] if asc else b[key] > base[key]),
                             cv_R2=b.get("R2", np.nan) if task == "reg" else np.nan))
pd.DataFrame(rows).to_csv(ARES / "primary_selection.csv", index=False); print(pd.DataFrame(rows)[["arm", "task", "track", "primary_method", "cv_metric", "cv_value", "baseline_cv_value", "beats_baseline_in_cv"]].round(3).to_string(index=False))
# covariate-use tables: fraction of the 15 CV fits (3 reps x 5 folds) in which a covariate is retained (R methods: nonzero / in model / GAM p<.05) + mean |held-out permutation importance| (ML, rep 0)
for arm in ARMS:
    for task in ("reg", "bin"):
        T = pd.read_csv(ARES / f"r_{arm}_{task}_cv_terms.csv"); T = T[~T.term.str.startswith("PC")]; nfit = T.groupby("method").fit.nunique()
        U = T.assign(_c=lambda x: x.term.str.replace("`", "")).groupby(["_c", "method"]).fit.nunique().unstack(fill_value=0)
        U = (U / 15).rename_axis("covariate"); I = pd.read_csv(ARES / f"ml_{arm}_{task}_cv_importance.csv"); I = I[I.method.str.contains("tuned") & ~I.method.str.contains("untuned")]
        Im = I.groupby(["term", "method"]).importance.mean().unstack().add_prefix("permimp: ").rename_axis("covariate"); out = U.join(Im, how="outer"); out.to_csv(ARES / f"covariate_use_{arm}_{task}.csv")
