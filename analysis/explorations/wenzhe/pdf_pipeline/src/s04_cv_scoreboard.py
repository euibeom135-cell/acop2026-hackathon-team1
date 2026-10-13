"""S04: repeated-CV scoreboard on TRAIN for ALL methods (covariate + ML), per arm and task, identical folds. TEST NOT TOUCHED.
Reg: RMSE/MAE/R2 (mean over the 3 repeats of pooled out-of-fold metrics; sd across repeats). Bin: ROC-AUC + recall/precision/accuracy at the Youden cutoff of the pooled OOF scores (mean, sd across repeats)."""
from pcommon import *
from metrics import *
from io_preds import *
rows = []
for arm in ARMS:
    d = get_arm(arm); fo = folds(arm, d["ltr"])
    for task in ("reg", "bin"):
        y = (d["ytr"] if task == "reg" else d["ltr"]).values; P = pd.concat([load_cv(arm, task), baseline_cv(y, fo, task)], ignore_index=True)
        for (nm, fam), g in P.groupby(["method", "family"]):
            per = []
            for rep, gg in g.groupby("rep"):
                gg = gg.sort_values("row"); yy = y[gg.row.values]; s = gg.pred.values
                if np.isnan(s).any(): per.append(None); continue
                per.append(reg_metrics(yy, s) if task == "reg" else (bin_metrics(yy, s, youden_cutoff(yy, s)) if s.std() > 0 else dict(AUC=0.5, recall=0, precision=np.nan, accuracy=float((yy == 0).mean()), n_pred_pos=0)))
            if any(p is None for p in per): rows.append(dict(arm=arm, task=task, method=nm, family=fam, note="NA predictions")); continue
            T = pd.DataFrame(per); rows.append(dict(arm=arm, task=task, method=nm, family=fam, n_train=len(y), **T.mean().to_dict(), **{k + "_sd": v for k, v in T.std(ddof=1).items()}))
S = pd.DataFrame(rows); S.to_csv(ARES / "cv_scoreboard.csv", index=False)
pd.set_option("display.width", 220)
for arm in ARMS:
    for task, key in (("reg", "RMSE"), ("bin", "AUC")):
        t = S[(S.arm == arm) & (S.task == task)].sort_values(key, ascending=(task == "reg")); print(f"\n== {arm} {task}"); print(t[["method", "family"] + [c for c in ("RMSE", "RMSE_sd", "MAE", "R2", "AUC", "AUC_sd", "recall", "precision") if c in t]].round(3).to_string(index=False))
