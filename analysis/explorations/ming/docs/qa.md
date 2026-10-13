# Anticipated judge questions — DM1 covariate analysis

*All answers are rehearsal (fold 5); the locked fold 1 is not opened. Each answer cites arm · metric · file. Primary source of record: `outputs/report/slide_tables.md`.*

---

**Q1. R² around 0.2–0.5 is low — how can you act on it?**
We don't act on the magnitude R²; we act on the **covariate axis and the enrichment rule**. For **Tideglusib** the decision object is the step: `1[cognition ≤ −0.505]` lifts single-term test R² to **+0.377** and splits mean composite improvement **8.28 vs 3.46** (`outputs/stratify/Tideglusib/rule.txt`). Where magnitude genuinely fails — **Oligonucleotide** continuous **R² 0.057, CI [−0.29, +0.25]** (`outputs/runs/continuous/fold5/Oligonucleotide/scoreboard.csv`) — we explicitly refuse a per-patient claim and use CTG only to stratify.

**Q2. You call rankings "ties," yet Tideglusib's random forest is your hero — isn't that a contradiction?**
On a single fold it *is* a tie: RF R² **0.255, CI −0.399 to 0.606** (`slide_tables.md`, Tideglusib continuous). The non-tie evidence is twofold: the **20-seed mean R² 0.491 vs 0.33–0.36** for linear models (`outputs/compare/repeat20_r2.csv`), and a one-term step beating the linear term **out-of-sample by +0.144** (+0.377 vs +0.233, `rule.txt`). The claim is the **nonlinearity/threshold**, not a leaderboard position.

**Q3. Why should we trust fold 5 if the real test is fold 1?**
We don't present fold 5 as final — it's **pre-registered rehearsal**. Fold 1 (**sha256 `8b3fb2cb…`, n = 101, seed 2026**, `outputs/splits/summary.json`) opens **once** at G3 (`CLAUDE.md`). Critically, our headline — *split moves scores, not covariates* — rests on **20 seeds**, not fold 5 alone (`outputs/compare/verdict.md`), so it does not depend on the one split you might distrust.

**Q4. The Oligonucleotide direction is opposite your hypothesis — did you make an error?**
It's a **flagged surprise, not an error, and not hidden**. Prior: higher repeat burden → *less* improvement (splicing-correction ceiling, −). Data: **`ctg_repeats` ρ = +0.42, q = 6e-6** on `qmt_change_26wk` (`results/tables/outcome_associations.csv`) — positive. Best explanation is a **room-to-improve / floor effect** in this simulation. We **pre-specify the sign** for the locked run rather than assume it (`docs/interpretation_Oligonucleotide.md` §2, §7).

**Q5. Gradient boosting underperformed — did you misconfigure it?**
We ran scikit-learn **HistGradientBoosting** in XGBoost's role (no OpenMP runtime; `docs/LOG.md`). It behaves as expected: on **Tideglusib** it's **second on 20-seed mean (0.372)** behind RF (`repeat20_r2.csv`), consistent with the forest; on small arms its single-fold CIs are the **widest** (e.g. Mexiletine untuned **R² −0.047, CI −0.678 to 0.277**, `slide_tables.md`) — normal for a high-variance learner on ~33 test patients.

**Q6. Why is Mexiletine's responder label predictable but its magnitude isn't?**
The continuous target is **relative** change, `−myotonia_change / baseline severity`, which divides severity — the dominant driver — back out, leaving a weak residual magnitude (best **R² ≈ 0.19, CI through 0**). The **label** (relative > 0.45) stays cleanly separable: one-term myotonia logistic **AUC 0.782**, stepwise **0.773 (CI 0.587–0.928)** (`outputs/runs/binary/fold5/Mexiletine/`, `docs/interpretation_Mexiletine.md` §2, §5).

**Q7. Isn't the Tideglusib −0.505 cut just overfitting to one threshold?**
The cut is chosen by a depth-1 tree **on training** and scored on **held-out** patients: indicator test **R² +0.377 > linear +0.233** (`rule.txt`). Cognition is selected **100% across 20 seeds** (`outputs/compare/selection_frequency.csv`), and the pre-registered guess was **z ≈ −0.5** (`docs/hypothesis_sheet.md`) — the data returned **−0.505**. It is still rehearsal; fold 1 re-estimates the cut.

**Q8. Why fourteen methods instead of just the best one?**
To **demonstrate** two things: the ranking is a tie (median per-method R² SD **0.131**, `verdict.md`), and the covariate signal is **not method-dependent**. When 14 very different methods converge on the same covariate — **cognition 100%, CTG 90%** cross-seed — that is robustness no single model can show (`docs/hypothesis_sheet.md`, Methods / bridge).

**Q9. How do we know this isn't data-dredging / p-hacking?**
Everything decision-relevant was **pre-registered before scoring**: endpoints, the 14 methods, the real-signal rule (**stable ≥0.6 AND beats the shuffled null**), consensus and stratification rules (`docs/hypothesis_sheet.md`; deviations logged in `docs/LOG.md`). The **shuffled-outcome null is the dredging control** — e.g., Mexiletine's severity trio is stable yet inside the null, so we **decline to claim it** (`slide_tables.md`, real-signal section).

**Q10. How much would the Tideglusib rule actually save a trial?**
Illustratively: mean response **3.46 → 8.28 (2.4×)** keeping **~47%** of candidates (`rule.txt`). Required N scales with ~1/effect², so even partial carry-over cuts enrollment; a fully preserved 2.4× effect is a ceiling of **~5–6× fewer patients** (`docs/interpretation_Tideglusib.md` §7). Hedged on three fronts: **no placebo arm** (this is on-treatment response), ~33 test patients, and **fold 1 not yet opened**.

**Q11. You listed Oligo `insulin_resistance` as "real signal" — are you claiming it?**
**No.** It beats the RF null on the continuous task (rf_imp **0.262 > 0.172**) but is kept in only **17% (10/60)** of cross-seed splits, is **not** a consensus term (0.42 < 0.5), and its marginal washes out under FDR (**q = 0.075**) (`docs/interpretation_Oligonucleotide.md` §4). We read it as a **one-fold nonlinear quirk** — reported for transparency, not claimed as a driver.

**Q12. Why are the confidence intervals so wide?**
Only **~32–34 held-out patients per arm** on fold 5, so bootstrap CIs run **≈ ±0.2 R²** and the per-split SD is **≈ 0.131** (`outputs/compare/verdict.md`). That width is exactly *why* we lead with **cross-seed stability** instead of point estimates, and *why* fold 1 is a **single sealed test** rather than repeated peeking.

**Q13. The Tideglusib result — baseline cognition predicting a cognition-weighted improvement composite — is it predictive, or just regression-to-the-mean / head-room?**
Fair, and it is the first question we'd ask too. **Conceded:** the composite is cognition-weighted (`work/dictionary.json`), so patients who start below average on cognition have the most **head-room** to improve — baseline and change are mechanically coupled, which is a classic **regression-to-the-mean / floor** setup, and the marginal (rho **−0.647**) is partly that coupling. **But it is more than an artifact:** the effect is a **step, not a smooth slope** — a hard indicator `1[cognition ≤ −0.505]` scores held-out **R² +0.377 > +0.233** for the linear term *and* beats the spline GAM (0.119) (`outputs/stratify/Tideglusib/rule.txt`); the random-forest partial dependence shows a discrete ~4-point cliff, not a gradient; and cognition is selected in **100% of 20 seeds** (`outputs/compare/selection_frequency.csv`). Pure RTM on a coupled scale would give a smooth gradient, not a reproducible threshold. **Honest bottom line:** with **no placebo arm** this is **on-treatment response**, i.e. **prognostic** (who improves), **not** a demonstrated predictive effect-modifier (who improves *more on drug than on control*). The pre-specified next steps are (1) re-estimate the −0.505 cut on the **locked fold 1**, and (2) ultimately confirm the enrichment **against a control arm** before it can modify a Tideglusib design (`docs/interpretation_Tideglusib.md` §7).
