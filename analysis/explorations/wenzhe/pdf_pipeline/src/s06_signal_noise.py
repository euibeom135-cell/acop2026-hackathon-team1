"""S06: assemble the SINGLE pre-stated signal-vs-noise verdict per arm x outcome (TRAIN evidence only; test untouched). Inputs: results/signal_r_*.csv (r_signal.R) and results/signal_rf_*.csv (s06a_rf_null.py).
VERDICT RULE (stated once, applied unchanged; no second/relaxed rule). A covariate scores one point for each criterion it meets:
  (a) bootstrap selection frequency >= 0.6, pooled over the three selectors LASSO(lambda.min), elastic net(alpha=.5), stepwise-BIC(both) in B=200 bootstrap resamples;
  (b) the sign of its lm/glm coefficient equals the full-train sign in >= 4 of 5 train subsamples (80% each);
  (c) used by >= 2 of 3 families on full train: penalised (LASSO or EN nonzero), stepwise-BIC retained, nonlinear/ML (GAM term p<0.05 under REML select=TRUE, OR RF held-out permutation importance > 0 in >= 4/5 folds);
  (d) lm/glm |t| (|z|) exceeds the 95th percentile of its shuffled-outcome null (500 permutations) OR RF held-out permutation importance exceeds the 95th percentile of the RF shuffled-outcome null (100 permutations).
SIGNAL = 4/4; NOISE = 0 or 1 of 4; BORDERLINE = 2 or 3 of 4.   Plausible-but-noise = NOISE covariates ranked by clinical plausibility (listed in the sheet as plausible-looking noise, else prior strength); top 3 distinct parents flagged."""
from pcommon import *
from priors import *
def one(arm, task):
    R = pd.read_csv(ARES / f"signal_r_{arm}_{task}.csv"); F = pd.read_csv(ARES / f"signal_rf_{arm}_{task}.csv"); fm = pd.read_csv(ARES / f"feature_map_{arm}.csv"); D = R.merge(F, on="covariate", how="left").merge(fm.rename(columns={"feature": "covariate"}), on="covariate", how="left")
    D["selfreq_pooled"] = D[["selfreq_lasso", "selfreq_enet", "selfreq_step_bic"]].mean(axis=1); D["crit_a"] = D.selfreq_pooled >= 0.6; D["crit_b"] = D.sign_same_k_of_5 >= 4
    D["fam_penalised"] = D.sel_full_lasso | D.sel_full_enet; D["fam_stepwise"] = D.sel_full_step_bic; D["fam_nonlinear_ml"] = (D.gam_p < 0.05) | ((D.rf_imp_mean > 0) & (D.rf_imp_folds_pos >= 4))
    D["n_families"] = D[["fam_penalised", "fam_stepwise", "fam_nonlinear_ml"]].sum(axis=1); D["crit_c"] = D.n_families >= 2
    D["t_above_null"] = D.tstat.abs() > D.abs_t_null95; D["rf_above_null"] = D.rf_imp_mean > D.rf_null95; D["crit_d"] = D.t_above_null | D.rf_above_null
    D["n_criteria"] = D[["crit_a", "crit_b", "crit_c", "crit_d"]].sum(axis=1); D["verdict"] = np.select([D.n_criteria == 4, D.n_criteria >= 2], ["SIGNAL", "BORDERLINE"], "NOISE")
    D["effect_on_outcome"] = np.where(D.coef_std > 0, "+", "-"); ben = np.sign(D.coef_std) * (SGN[arm] if task == "reg" else 1)
    D["effect_on_benefit"] = np.where(ben > 0, "higher/present = better response", "higher/present = worse response")
    pr = D.covariate.map(PRIOR[arm]); D["prior_strength"] = pr.map(lambda p: p[0] if isinstance(p, tuple) else "unspecified"); psign = pr.map(lambda p: p[1] if isinstance(p, tuple) else 0)
    D["prior_sign_on_benefit"] = psign.map({1: "+", -1: "-", 0: "open"}); D["prior_sign_on_outcome"] = (psign * (SGN[arm] if task == "reg" else 1)).map({1: "+", -1: "-", 0: "open"})
    D["sign_agrees_with_prior"] = np.where(psign == 0, "n/a (prior open)", np.where(np.sign(D.coef_std) * (SGN[arm] if task == "reg" else 1) == psign, "agree", "DISAGREE"))
    D["plausible_score"] = D.covariate.map(lambda c: 4 if c in PLAUSIBLE_NOISE[arm] else 0) + D.prior_strength.map(STRENGTH_SCORE)
    D["plausible_but_noise"] = False; D["plausible_noise_reason"] = ""
    cand = D[(D.verdict == "NOISE") & (D.plausible_score > 0)].sort_values(["plausible_score", "n_criteria", "selfreq_pooled"], ascending=[False, True, True]); seen = set()
    for i, r in cand.iterrows():
        if r.parent in seen or len(seen) >= 3: continue
        seen.add(r.parent); D.loc[i, "plausible_but_noise"] = True
        D.loc[i, "plausible_noise_reason"] = (f"{WHY_PLAUSIBLE.get(r.covariate, r.covariate)}; but selected in only {r.selfreq_pooled:.0%} of bootstraps, |t|={abs(r.tstat):.2f} (null 95th pct {r.abs_t_null95:.2f}), "
                                              f"RF perm. importance {r.rf_imp_mean:.3g} (null 95th pct {r.rf_null95:.3g}), {int(r.n_criteria)}/4 criteria" + (" - sheet lists it as plausible-looking noise" if r.covariate in PLAUSIBLE_NOISE[arm] else ""))
    D = D.sort_values(["n_criteria", "selfreq_pooled", "tstat"], key=lambda s: s.abs() if s.name == "tstat" else s, ascending=False).reset_index(drop=True); D.insert(0, "rank", D.index + 1); D.insert(1, "arm", arm); D.insert(2, "task", task)
    cols = ["rank", "arm", "task", "covariate", "parent", "domain", "effect_on_outcome", "effect_on_benefit", "coef_std", "tstat", "p_value", "selfreq_pooled", "selfreq_lasso", "selfreq_enet", "selfreq_step_bic", "crit_a", "sign_same_k_of_5", "crit_b",
            "fam_penalised", "fam_stepwise", "fam_nonlinear_ml", "n_families", "gam_edf", "gam_p", "crit_c", "abs_t_null95", "t_above_null", "rf_imp_mean", "rf_imp_folds_pos", "rf_null95", "rf_above_null", "crit_d", "n_criteria", "verdict",
            "prior_strength", "prior_sign_on_outcome", "prior_sign_on_benefit", "sign_agrees_with_prior", "plausible_but_noise", "plausible_noise_reason"]
    return D[cols]
allr = []; head = []
for arm in ARMS:
    for task in ("reg", "bin"):
        D = one(arm, task); D.to_csv(ARES / f"signal_noise_{arm}_{task}.csv", index=False); allr.append(D)
        join = lambda m: "; ".join(D[m].covariate) or "none"; dis = D[(D.verdict != "NOISE") & (D.sign_agrees_with_prior == "DISAGREE")]
        head.append(dict(arm=arm, task=task, signal=join(D.verdict == "SIGNAL"), borderline=join(D.verdict == "BORDERLINE"), plausible_but_noise=join(D.plausible_but_noise), sign_disagreements_among_signal_borderline="; ".join(dis.covariate) or "none"))
pd.concat(allr).to_csv(ARES / "signal_noise_summary.csv", index=False); H = pd.DataFrame(head); H.to_csv(ARES / "signal_noise_headline.csv", index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 120); print(H.to_string(index=False))
