"""S06: score EVERY method ONCE on the locked seed-42 test set (per arm; regression and classification) + SHAP (on TRAIN rows).
Everything is fitted on TRAIN only (tuning by inner CV). Classification cutoff = Youden's J on the TRAIN out-of-fold scores (fixed before seeing test).
Guard: refuses to run again unless --force. NOTE (disclosure): the main project's step 5 already scored a subset of the continuous models on this test set; the numbers here
are a wider, pre-planned scoreboard, nothing was tuned or removed after seeing test results.
Run: python s06_test_scoring.py"""
import sys, subprocess, pickle, warnings; warnings.filterwarnings("ignore")
from joblib import Parallel, delayed
import shap
from scommon import *
from metrics import *
from io_preds import *
from ml_models import variants, predict
if (ARES / "test_scoreboard.csv").exists() and "--force" not in sys.argv: sys.exit("Test set already scored (results/test_scoreboard.csv). Pass --force only for a documented re-run.")
NB = 2000; rng_seed = 0

def fit_pred(vi, Ztr, y, Zte, task):
    nm, build, tuned, r = variants(task)[vi]; m = build().fit(Ztr, y); return nm, predict(m, Zte, task), (m.best_params_ if tuned else None), m

def oof_cutoffs(P):
    """Youden cutoff of each method from TRAIN out-of-fold scores averaged over the CV repeats."""
    return P  # placeholder (replaced below)

rows, preds_all, terms_all, shap_pack, cmp_rows = [], [], [], {}, []
for arm in ARMS:
    d = get_arm(arm, test=True); Ztr, Zte = d["Ztr"].reset_index(drop=True), d["Zte"].reset_index(drop=True); fo = folds(arm, d["ltr"]); base = d["rte"].myotonia_severity.values
    T = Zte.copy(); T.insert(0, "y", d["yte"].values); T.insert(1, "label", d["lte"].values); T.to_csv(ARES / f"test_{arm}.csv", index=False)
    for task in ("reg", "bin"):
        r = subprocess.run(["Rscript", "r_covariate.R", arm, task, "test"], capture_output=True, text=True, cwd=Path(__file__).parent); print(r.stdout.strip(), r.stderr[-300:] if r.returncode else "", flush=True)
    (ARES / f"test_{arm}.csv").unlink()                                               # test matrix is not kept on disk
    for task in ("reg", "bin"):
        ytr = (d["ytr"] if task == "reg" else d["ltr"]).values; yte = (d["yte"] if task == "reg" else d["lte"]).values; n = len(yte)
        V = variants(task); out = Parallel(n_jobs=-1)(delayed(fit_pred)(vi, Ztr, ytr, Zte, task) for vi in range(len(V)))
        Pt = {nm: (p, "ML", bp) for nm, p, bp, m in out}
        Rp = pd.read_csv(ARES / f"r_{arm}_{task}_test_preds.csv")
        for nm, g in Rp.groupby("method"): Pt[nm] = (g.sort_values("row").pred.values, "Covariate", None)
        Pt["Mean only" if task == "reg" else "Prevalence only"] = (np.full(n, ytr.mean()), "Baseline", None)
        terms_all.append(pd.read_csv(ARES / f"r_{arm}_{task}_test_terms.csv").assign(arm=arm, task=task))
        if task == "bin":      # train OOF cutoffs
            cvP = pd.concat([load_cv(arm, "bin")], ignore_index=True); oof = cvP.groupby(["method", "row"]).pred.mean().reset_index()
            cut = {m: youden_cutoff(ytr[g.sort_values("row").row.values], g.sort_values("row").pred.values) for m, g in oof.groupby("method")}; cut["Prevalence only"] = 1.0
        for nm, (p, fam, bp) in Pt.items():
            if np.isnan(p).any(): rows.append(dict(arm=arm, task=task, method=nm, family=fam, note="NA predictions")); continue
            preds_all.append(pd.DataFrame(dict(arm=arm, task=task, method=nm, row=np.arange(n), obs=yte, pred=p)))
            if task == "reg":
                m_ = reg_metrics(yte, p); m0 = Pt["Mean only"][0]; lo, hi = boot_ci(lambda i: reg_metrics(yte[i], p[i])["RMSE"], n, NB)
                dl, dh = boot_ci(lambda i: np.sqrt(np.mean((yte[i] - m0[i]) ** 2)) - np.sqrt(np.mean((yte[i] - p[i]) ** 2)), n, NB)
                sc = np.nan_to_num((-p / np.where(base == 0, np.nan, base)) if arm == "Mexiletine" else p, nan=0.0); lab = d["lte"].values
                auc = float(roc_auc_score(lab, sc)) if nm != "Mean only" and sc.std() > 0 else 0.5
                rows.append(dict(arm=arm, task=task, method=nm, family=fam, **m_, RMSE_lo=lo, RMSE_hi=hi, R2_vs_trainmean=1 - np.sum((yte - p) ** 2) / np.sum((yte - ytr.mean()) ** 2),
                                 dRMSE_vs_mean=np.sqrt(np.mean((yte - m0) ** 2)) - m_["RMSE"], dRMSE_lo=dl, dRMSE_hi=dh, AUC_derived=auc, best_params=str(bp) if bp else ""))
            else:
                c = cut.get(nm, 0.5); m_ = bin_metrics(yte, p, c); lo, hi = boot_ci(lambda i: bin_metrics(yte[i], p[i], c)["AUC"], n, NB)
                rows.append(dict(arm=arm, task=task, method=nm, family=fam, **m_, AUC_lo=lo, AUC_hi=hi, cutoff=c, n_test=n, n_resp=int(yte.sum()), best_params=str(bp) if bp else ""))
        # SHAP (tree models, tuned) on TRAIN rows -> mean |SHAP| + raw values for beeswarm
        for vi, (nm, p, bp, m) in enumerate(out):
            if "(tuned" in nm and any(k in nm for k in ("Random forest", "XGBoost", "Decision tree")):
                mm = m.best_estimator_; ex = shap.TreeExplainer(mm); sv = ex.shap_values(Ztr)
                if isinstance(sv, list): sv = sv[1]
                sv = np.asarray(sv); sv = sv[..., 1] if sv.ndim == 3 else sv
                shap_pack[(arm, task, nm)] = (sv, Ztr.copy())
        print("scored", arm, task, flush=True)
S = pd.DataFrame(rows); S.to_csv(ARES / "test_scoreboard.csv", index=False); pd.concat(preds_all).to_csv(ARES / "test_predictions.csv", index=False); pd.concat(terms_all).to_csv(ARES / "r_test_terms_all.csv", index=False)
pickle.dump(shap_pack, open(ARES / "shap_pack.pkl", "wb")); print(S.groupby(["arm", "task"]).size())
