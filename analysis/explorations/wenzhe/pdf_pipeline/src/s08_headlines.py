"""S08: headline tables built from the already-written scoreboards (no new fitting, no new test scoring).
results/test_headlines.csv: per arm x task: best test covariate model, best test ML model, the CV-selected primary of each track with its test metric, baseline, and whether ML beat the covariate model (primary vs primary and best vs best).
results/test_scoreboard_compact.csv: the same scoreboard sorted for reading."""
from pcommon import *
S = pd.read_csv(ARES / "test_scoreboard.csv"); rows = []
for arm in ARMS:
    for task, key, asc in (("reg", "RMSE", True), ("bin", "AUC", False)):
        t = S[(S.arm == arm) & (S.task == task)].dropna(subset=[key]); b = t[t.family == "Baseline"].iloc[0]; rec = dict(arm=arm, task=task, metric=key, baseline=b.method, baseline_value=b[key])
        for fam in ("Covariate", "ML"):
            g = t[t.family == fam].sort_values(key, ascending=asc); pr = g[g.is_primary]
            rec.update({f"best_{fam}": g.iloc[0].method, f"best_{fam}_value": g.iloc[0][key], f"primary_{fam}": pr.iloc[0].method, f"primary_{fam}_value": pr.iloc[0][key]})
            if task == "reg": rec.update({f"best_{fam}_R2": g.iloc[0].R2, f"primary_{fam}_R2": pr.iloc[0].R2, f"primary_{fam}_CI": f"{pr.iloc[0].RMSE_lo:.3f}-{pr.iloc[0].RMSE_hi:.3f}"})
            else: rec.update({f"primary_{fam}_CI": f"{pr.iloc[0].AUC_lo:.3f}-{pr.iloc[0].AUC_hi:.3f}"})
        better = (lambda a, c: a < c) if asc else (lambda a, c: a > c)
        rec["ML_beats_covariate_primary_vs_primary"] = bool(better(rec["primary_ML_value"], rec["primary_Covariate_value"])); rec["ML_beats_covariate_best_vs_best"] = bool(better(rec["best_ML_value"], rec["best_Covariate_value"]))
        rec["best_covariate_beats_baseline"] = bool(better(rec["best_Covariate_value"], rec["baseline_value"])); rec["best_ML_beats_baseline"] = bool(better(rec["best_ML_value"], rec["baseline_value"]))
        rows.append(rec)
H = pd.DataFrame(rows); H.to_csv(ARES / "test_headlines.csv", index=False)
S.sort_values(["arm", "task", "family", "RMSE", "AUC"], ascending=[True, True, True, True, False]).to_csv(ARES / "test_scoreboard_compact.csv", index=False)
pd.set_option("display.width", 250); print(H.T.to_string())
