# Oligonucleotide (antisense) arm — interpretation

*Rehearsal mode. All scores below are on **fold 5** (pseudo-test, n = 34 Oligonucleotide
patients; `outputs/splits/summary.json` fold_counts["5"]). The locked **fold 1** is NOT
opened; its hash (seed 2026, `outputs/splits/summary.json`) is confirmed only at the final run.
Continuous target = `qmt_change_26wk` (QMT, higher = more improvement). Binary = responder label.*

## 1. Headline
**On this arm the covariates are identifiable even where the per-patient score is not:**
we cannot predict an individual's QMT change on held-out patients (best continuous test
R² ≈ 0.06, 95% CI straddling zero), yet repeat burden (`ctg_repeats`) is pinned as the
leading, stable axis by two independent resampling procedures at ≈0.90.

## 2. Mechanism
The pre-registered biology (`docs/hypothesis_sheet.md`) is an **ASO splicing-correction ceiling**:
CTG-repeat burden (`ctg_repeats`) and `somatic_mosaicism_index` index how much mis-spliced
*DMPK*/CUG-foci load an antisense drug must clear, so higher burden was expected to *cap*
achievable correction (direction −). The data instead show both marginals **positive and
FDR-significant** — `ctg_repeats` Spearman ρ = +0.42 (q = 6.0e-6) and
`somatic_mosaicism_index` ρ = +0.32 (q = 7.0e-4) on `qmt_change_26wk`
(`results/tables/outcome_associations.csv`). The most parsimonious reconciliation is a
**room-to-improve** effect: higher-repeat, weaker patients have more measurable QMT headroom
(baseline `muscle_strength` ρ = −0.24, q = 0.021), and in this *simulated* data that floor
effect outruns the mechanistic ceiling. The axis the prior named is real; its **sign is
reversed** here, so treat the direction as a property of the simulation to confirm on fold 1.
`insulin_resistance` is biologically plausible in DM1 (INSR mis-splicing → metabolic
dysfunction), but there is no strong prior that it modifies ASO response, and the
pre-registration listed it among weak/unstable candidates — see §4/§6 for why the data
agree with that caution despite one "real signal" flag.

## 3. Scores move, covariates don't (the core contrast)
- **Scores move toward/around zero and depend on the split.** Best continuous test R² = **0.057**
  (Stepwise BIC / Best subset), 95% CI **[−0.29, +0.25]**; OLS-all R² = 0.022, CI [−0.47, +0.29];
  Random forest R² = −0.028 (`outputs/runs/continuous/fold5/Oligonucleotide/scoreboard.csv`).
  Across 20 seeds the per-method R² SD is **0.064–0.176** (median across arms 0.131 — "rankings
  inside this band are ties"), and the leading R² is **+0.06 (fold5), +0.01 (single80),
  +0.02 (single75)** depending only on which patients are held out (`outputs/compare/verdict.md`).
- **Covariates do not move.** `ctg_repeats` is selected in **0.90** of the 100 half-subsamples,
  beats the RF permutation null (rf_importance 0.464 > null_q95 0.172) → verdict **"real signal"**
  (`outputs/stability/continuous/Oligonucleotide/stability.csv`), and independently in **0.90**
  (54/60) of the 20 cross-seed splits (`outputs/compare/selection_frequency.csv`; `verdict.md`).
  Its consensus score is 0.857 (continuous) / 0.9375 (binary)
  (`.../fold5/Oligonucleotide/consensus.csv`).

**One number to carry:** best test R² ≈ **0.057, CI [−0.29, +0.25]** (straddles zero) versus
`ctg_repeats` selected in **≈90% of resamples by both** the half-subsample auditor and the
cross-seed splits. Which patients are held out moves the *score*; it does not move the *covariate*.

## 4. Real signal vs noise (stability-auditor verdicts)
- **Continuous** (`outputs/stability/continuous/Oligonucleotide/stability.csv`):
  **real signal** = `ctg_repeats` (0.90), `insulin_resistance` (0.78, rf_imp 0.262 > 0.172);
  **suggestive** = `disease_duration` (0.83), `somatic_mosaicism_index` (0.81, rf_imp 0.162 — just
  below null 0.172); everything else **noise** (e.g. `myotonia_severity` 0.39, `family_history` 0.34).
- **Binary** (`outputs/stability/binary/Oligonucleotide/stability.csv`):
  **real signal** = `disease_duration` (0.91), `ctg_repeats` (0.76); `bmi` **suggestive** (0.28,
  barely beats a near-zero null); `somatic_mosaicism_index` (0.54) and `insulin_resistance` (0.31)
  fall to **noise**.

`ctg_repeats` is the only term that is "real signal" on **both** tasks. `insulin_resistance`
earns "real signal" (continuous) via RF importance only; it is **not** a consensus term
(0.42 < 0.5), is kept in just **0.167** (10/60) of cross-seed splits, and its marginal washes
out under FDR (ρ = 0.19, q = 0.075). Read it as a one-fold nonlinear quirk, consistent with
its pre-registered "unstable" label — not a robust driver.

## 5. Enrichment / stratification rule — honestly, it does not help here
The depth-1 rule picks `ctg_repeats > 346.5`, with enriched-subgroup mean QMT change **2.026 vs
0.384** (41/102 training patients), and the partial-dependence curve rises monotonically from
**0.37 (50 repeats) to ~1.76 (≥400)** (`outputs/stratify/Oligonucleotide/rule.txt`,
`partial_dependence.csv`). But the pre-specified adoption test fails: the indicator's test
R² = **−0.071** is *worse* than the bland single linear term's **+0.002** — the threshold does
**not** recover the forest's gain over the linear term, and both are ~0. **There is a real
ordering axis but no exploitable magnitude signal:** the in-sample mean gap does not survive to
held-out prediction, so no stratification threshold is adopted for this arm.

## 6. Prior vs data
| Covariate | Pre-registered expectation | Data showed (direction, verdict, number) |
|---|---|---|
| `ctg_repeats` | Real driver, **−** (higher burden → less; ceiling) | **+** ρ = +0.42, q = 6e-6; **real signal** (stab 0.90, cross-seed 0.90). Axis confirmed, **sign reversed**. |
| `somatic_mosaicism_index` | Real driver, **−** | **+** ρ = +0.32, q = 7e-4; **suggestive** (cont) / **noise** (binary); cross-seed 0.57. Sign reversed; not real signal. |
| `muscle_strength` (baseline) | Context (QMT depends on capacity) | **−** ρ = −0.24, q = 0.021; **noise** (stab 0.18). Lower strength → more improvement; not retained. |
| `insulin_resistance` | Weak / unstable | **real signal** (cont, RF only) but cross-seed 0.167, not consensus, q = 0.075. Prior ("unstable") essentially upheld. |
| `disease_duration` | (not an Oligo prior) | **+** ρ = +0.23, q = 0.026; **real signal** (binary 0.91) / **suggestive** (cont 0.83). Likely correlated surrogate of repeat burden / age. |
| `family_history` | Weak | cross-seed 0.65 yet **noise** (q = 0.099). "Often selected, not real signal." |

## 7. Trial-design implication
You can **identify a repeat-burden axis** but you **cannot predict QMT magnitude** on a new
patient. Concretely: `ctg_repeats` is a defensible **randomization-stratification / pre-specified
subgroup factor** — it stably orders patients and concentrates a higher-mean subgroup
(2.026 vs 0.384) — but it is **not** a trial-ready individual-level predictive-enrichment
biomarker: do not power a trial on a per-patient predicted ΔQMT (best R² 0.057 with CI through
zero; the indicator version is *negative* out-of-sample). Two cautions before any use: (i) the
enrichment direction is **positive** in this simulation (higher repeats → more improvement),
**opposite** the mechanistic ceiling prior, so pre-specify the sign rather than assume it; and
(ii) everything here is fold-5 rehearsal — the ordering and its direction must hold on the
**locked fold 1** before informing a real design.
