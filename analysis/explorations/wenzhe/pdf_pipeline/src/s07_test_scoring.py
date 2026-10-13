"""S07: THE SINGLE TEST PASS. Scores the full PDF-scope method set ONCE on the locked seed-42 80/20 test set (per arm; regression and classification), plus permutation importance and SHAP computed ON THE TEST SET
(as the kickoff guide shows) for the ML models, using the very models fitted here (nothing is refitted or re-scored later).
Everything is fitted on the full TRAIN rows only (tuning by inner CV; scaler fitted on full TRAIN, numeric columns only, applied to test). The classification cutoff of every method is its Youden-J cutoff on the TRAIN out-of-fold scores
(mean over the CV repeats), fixed before any test row is read. The primary covariate / ML model per arm were chosen in s05 by TRAIN CV only and are only FLAGGED here.
Guard: writes results/TEST_SCORED.lock and refuses to run again unless --force. Run: python s07_test_scoring.py"""
import sys, json, hashlib, subprocess, pickle, datetime, warnings; warnings.filterwarnings("ignore")
from joblib import Parallel, delayed
import shap
from sklearn.inspection import permutation_importance
from pcommon import *
from metrics import *
from metrics_extra import confusion
from io_preds import *
from ml_models import variants, predict
LOCK = ARES / ("DRYRUN.lock" if DRYRUN else "TEST_SCORED.lock")
if LOCK.exists() and "--force" not in sys.argv: sys.exit(f"Test set already scored ({LOCK.name}). Pass --force only for a documented re-run.")
SEL = ARES / "primary_selection.csv"
if not SEL.exists(): sys.exit("primary_selection.csv missing: selection by TRAIN CV (s05) must precede the test pass.")
NB, NPERM = 2000, 10; sel = pd.read_csv(SEL); primary = {(r.arm, r.task, r.primary_method): r.track for r in sel.itertuples()}
LOCK.write_text(json.dumps(dict(started=datetime.datetime.now().isoformat(timespec="seconds"), selection_sha256=hashlib.sha256(SEL.read_bytes()).hexdigest(), split=str(SPLIT_CSV))))

def fit_one(vi, X, y, task, num):
    nm, build, tuned, r = variants(task, num, list(X.columns))[vi]; m = build().fit(X, y); return nm, m, (m.best_params_ if tuned else None), r["scoring"]

rows, preds_all, terms_all, imp_rows, shap_pack = [], [], [], [], {}
for arm in ARMS:
    d = get_arm(arm, test=True); Xtr, Xte = d["Xtr"].reset_index(drop=True), d["Xte"].reset_index(drop=True); fo = folds(arm, d["ltr"])
    T = Xte.copy(); T.insert(0, "y", d["yte"].values); T.insert(1, "label", d["lte"].values); T.to_csv(ARES / f"features_test_{arm}.csv", index=False)
    for task in ("reg", "bin"):
        r = subprocess.run(["Rscript", str(Path(__file__).parent / "r_covariate.R"), arm, task, "test"], capture_output=True, text=True); print(r.stdout.strip(), r.stderr[-300:] if r.returncode else "", flush=True)
    for task in ("reg", "bin"):
        ytr = (d["ytr"] if task == "reg" else d["ltr"]).values; yte = (d["yte"] if task == "reg" else d["lte"]).values; n = len(yte)
        out = Parallel(n_jobs=-1)(delayed(fit_one)(vi, Xtr, ytr, task, d["num"]) for vi in range(len(variants(task, d["num"], list(Xtr.columns)))))
        Pt = {nm: (predict(m, Xte, task), "ML", bp) for nm, m, bp, sc in out}
        Rp = pd.read_csv(ARES / f"r_{arm}_{task}_test_preds.csv")
        for nm, g in Rp.groupby("method"): Pt[nm] = (g.sort_values("row").pred.values, "Covariate", None)
        base_nm = "Mean only" if task == "reg" else "Prevalence only"; Pt[base_nm] = (np.full(n, ytr.mean()), "Baseline", None)
        terms_all.append(pd.read_csv(ARES / f"r_{arm}_{task}_test_terms.csv").assign(arm=arm, task=task))
        if task == "bin":      # cutoffs from TRAIN out-of-fold scores
            oof = load_cv(arm, "bin").groupby(["method", "row"]).pred.mean().reset_index(); cut = {m: youden_cutoff(ytr[g.sort_values("row").row.values], g.sort_values("row").pred.values) for m, g in oof.groupby("method")}; cut[base_nm] = 1.0
        for nm, (p, fam, bp) in Pt.items():
            pri = primary.get((arm, task, nm)); base = dict(arm=arm, task=task, method=nm, family=fam, is_primary=pri is not None, primary_track=pri or "", n_test=n, best_params=str(bp) if bp else "")
            if np.isnan(p).any(): rows.append(dict(**base, note="NA predictions")); continue
            preds_all.append(pd.DataFrame(dict(arm=arm, task=task, method=nm, row=np.arange(n), obs=yte, pred=p)))
            if task == "reg":
                m_ = reg_metrics(yte, p); m0 = Pt[base_nm][0]; lo, hi = boot_ci(lambda i: reg_metrics(yte[i], p[i])["RMSE"], n, NB); rm = lambda i: np.sqrt(np.mean((yte[i] - m0[i]) ** 2)) - np.sqrt(np.mean((yte[i] - p[i]) ** 2)); dl, dh = boot_ci(rm, n, NB)
                rows.append(dict(**base, outcome_direction="lower = better (more negative change)" if arm == "Mexiletine" else "higher = better", **m_, RMSE_lo=lo, RMSE_hi=hi, R2_vs_trainmean=1 - np.sum((yte - p) ** 2) / np.sum((yte - ytr.mean()) ** 2),
                                 dRMSE_vs_mean=float(np.sqrt(np.mean((yte - m0) ** 2)) - m_["RMSE"]), dRMSE_lo=dl, dRMSE_hi=dh))
            else:
                c = cut.get(nm, 0.5); m_ = bin_metrics(yte, p, c); lo, hi = boot_ci(lambda i: bin_metrics(yte[i], p[i], c)["AUC"], n, NB)
                rows.append(dict(**base, **m_, AUC_lo=lo, AUC_hi=hi, **confusion(yte, p, c), cutoff=c, cutoff_rule="Youden J on TRAIN out-of-fold scores", n_resp=int(yte.sum())))
        # test-set permutation importance (all ML models) and SHAP (tree models), on the models fitted above
        for nm, m, bp, sc in out:
            pi = permutation_importance(m, Xte, yte, n_repeats=NPERM, scoring=sc, random_state=0); est = m.best_estimator_ if hasattr(m, "best_estimator_") else m; sv = None
            if any(k in nm for k in ("Random forest", "XGBoost", "Decision tree")):
                Xt = est.named_steps["pre"].transform(Xte); sv = shap.TreeExplainer(est.named_steps["est"]).shap_values(Xt)
                if isinstance(sv, list): sv = sv[1]
                sv = np.asarray(sv); sv = sv[..., 1] if sv.ndim == 3 else sv; shap_pack[(arm, task, nm)] = (sv, Xte.copy(), Xt)
            for j, c_ in enumerate(Xte.columns): imp_rows.append(dict(arm=arm, task=task, method=nm, term=c_, perm_mean=pi.importances_mean[j], perm_sd=pi.importances_std[j], shap_mean_abs=float(np.abs(sv[:, j]).mean()) if sv is not None else np.nan))
        print("scored", arm, task, flush=True)
S = pd.DataFrame(rows); S.to_csv(ARES / "test_scoreboard.csv", index=False); pd.concat(preds_all).to_csv(ARES / "test_predictions.csv", index=False); pd.concat(terms_all).to_csv(ARES / "r_test_terms_all.csv", index=False)
pd.DataFrame(imp_rows).to_csv(ARES / "test_importance.csv", index=False); pickle.dump(shap_pack, open(ARES / "test_shap.pkl", "wb"))
LOCK.write_text(LOCK.read_text()[:-1] + f', "finished": "{datetime.datetime.now().isoformat(timespec="seconds")}", "rows": {len(S)}' + "}"); print(S.groupby(["arm", "task"]).size())
