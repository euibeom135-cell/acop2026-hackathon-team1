# Mexiletine — covariate interpretation (DM1 hackathon)

*Rehearsal scoring. All numbers below are on **fold 5** (pseudo-test, n = 32); the
locked **fold 1** (n = 33, sha256 `8b3fb2cb…`) is **not** opened
(`outputs/splits/summary.json`). Bootstrap CIs on 32 patients are wide (~±0.2 R²;
per-split R² SD ≈ 0.13, `outputs/compare/verdict.md`), so point-estimate rankings
inside a band are **ties**, not winners.*

## 1. Headline
**On fold 5 the mexiletine _responder label_ is the only cleanly predictable
endpoint — stepwise logistic reaches ROC-AUC 0.77 (95% CI 0.59–0.93) — while the
_magnitude_ of relative myotonia improvement is at best weakly learnable
(R² ≈ 0.19–0.24, bootstrap CI spanning 0), and no covariate clears the
pre-registered "real-signal" bar.**
(`outputs/runs/binary/fold5/Mexiletine/scoreboard.csv`: stepwise AIC/BIC/best-subset
ROC_AUC 0.7727 [0.587, 0.928]; `outputs/runs/continuous/fold5/Mexiletine/scoreboard.csv`
best point estimate SVM 0.193 / stepwise AIC 0.190, both CIs include 0;
`.../continuous/.../compact_scoreboard.csv` 3-term model R² 0.242.)

## 2. Mechanism (and priors)
Mexiletine is a use-dependent sodium-channel blocker whose direct action is
relieving myotonia, so a myotonia-anchored response should track the baseline
myotonia axis — and it does: baseline **myotonia_severity** is the strongest
marginal correlate of absolute 12-wk improvement (Spearman rho **+0.825**, CI
0.743–0.878), with **ctg_repeats +0.714** (0.608–0.790) and **disease_duration
−0.287** (−0.433 to −0.129) (`results/tables/outcome_associations.csv`,
Arm==Mexiletine, all FDR q<0.05). CTG repeat length is the classic genetic
severity marker; longer disease_duration indexes accumulated, less-reversible
fibrosis, consistent with its negative sign (longer → smaller relative gain).

Priors (`docs/hypothesis_sheet.md`) — **directions all held**: myotonia_severity
and ctg_repeats positive (severity ↔ response) ✓; disease_duration negative ✓.
**What did not hold** is the prior that these are *real drivers*: on the
pre-registered **relative** target they are stable but do not beat the
shuffled-outcome RF null → only "suggestive" (§3). The mechanical reason is that
the target divides absolute improvement by baseline myotonia_severity
(`−myotonia_change_12wk / myotonia_severity`), so severity — the dominant driver
of *absolute* change — is largely divided back out, leaving a weak residual.

## 3. Real signal vs noise
**Continuous (relative-improvement) — `outputs/stability/continuous/Mexiletine/stability.csv`:**
ctg_repeats (freq 0.71), myotonia_severity (0.70), disease_duration (0.65) are all
**stable** but each has RF grouped importance **below** the null q95 of 0.195
(0.116 / 0.191 / 0.110) → verdict **suggestive**. Every other covariate is
**noise** (freq ≤ 0.54, incl. insulin_resistance 0.54, pr_interval 0.46). No term
is "real signal."

**Binary (responder-label) — `outputs/stability/binary/Mexiletine/stability.csv`:**
nothing is stable (top freq ctg_repeats 0.26, myotonia_severity 0.20); RF
importances collapse to ≈0 and only family_history nominally beats null at freq
0.06 → all **noise/suggestive**.

The nuance is a split-endpoint story: the relative *magnitude* leaves severity
**stable-but-weak**, whereas the responder *label* (relative improvement > 0.45,
`docs/hypothesis_sheet.md`) is cleanly separable by logistic models — a one-term
logistic on myotonia_severity already reaches ROC-AUC **0.782**
(`.../binary/.../compact_scoreboard.csv`) — even though the RF stability audit
certifies no single term. Cross-seed selection frequency
(`outputs/compare/selection_frequency.csv`, `.../verdict.md`) pins the reproducible
axis: **myotonia_severity 0.85, disease_duration 0.75**, with ctg_repeats 0.56 and
insulin_resistance 0.60 straddling the 0.6 line. So the top two covariates persist
across 20 seeds while the leading R² swings (+0.19 fold5 / −0.01 single80 / +0.14
single75) — exactly the pre-registered conclusion: *which patients are held out
moves the score, not the covariates.*

## 4. Enrichment / stratification rule
Data-chosen depth-1 rule (`outputs/stratify/Mexiletine/rule.txt`):
**CTG repeats > 448.5**. Patients above the cut have higher mean relative
improvement (**0.467 vs 0.344**; enriched subgroup 24/96 training). But the hard
threshold is **weaker** than treating CTG as continuous: test R² for the indicator
`1[ctg>448]` is **+0.138** vs **+0.163** for the linear ctg_repeats term — it does
*not* recover the forest's gain over the linear term, so by the pre-registered
decision rule the cut-point is **not preferred**. Partial dependence
(`.../partial_dependence.csv`) shows a gentle monotone rise (~0.37 below ~440 to
~0.43 at the top) with only a mild bend near 450–460 — a dose-like trend, not a
clean step. Honest read: for this arm the stratification rule is weak and better
stated as "more CTG repeats → somewhat more relative improvement" than as a
threshold.

## 5. Prior-vs-data table

| Covariate | Pre-registered expectation | What the data showed |
|---|---|---|
| myotonia_severity | real driver, severity ↔ response (+) | marginal rho **+0.825**; stable (0.70) but within RF null → **suggestive**; cross-seed **0.85**; 1-term responder AUC 0.782 |
| ctg_repeats | real driver, severity ↔ response (+) | marginal rho **+0.714**; stable (0.71) → **suggestive**; cross-seed **0.56** (borderline); leading stratifier |
| disease_duration | − (longer → less) | marginal rho **−0.287** (direction ✓); stable (0.65) → **suggestive**; cross-seed **0.75** |
| insulin_resistance / pr_interval / bmi / ck / sex / smoking / cataracts | weak/unstable, flip across resamples | all **noise** (freq ≤ 0.54); insulin_resistance 0.54 → 0.60 cross-seed = borderline flip, as predicted ✓ |

## 6. Trial-design implication
Prognostic enrichment on CTG > 448 roughly **doubles responder prevalence, from
0.289 (37/128) to 0.543 (19/35)** in the non-locked arm
(`inputs/dm1_clinical_trial_dataset.csv`, folds 2–5), which for a responder-rate
endpoint would raise the per-arm event rate and shrink the required N. Strong
caveats: this rests on **35 enriched patients**, CIs are wide, fold 1 (33
patients) is still locked, and because arm assignment was a *weighted, non-random*
draw (`README.txt`, `work/dictionary.json`) this is **prognostic** (who responds),
not a validated predictive effect-modifier — it must be pre-specified and
confirmed on fold 1 before it can inform a real mexiletine design.
