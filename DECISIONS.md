# Decision log

Judges score whether the split, noise handling and metrics are "explained and justified". Every analysis choice goes here with its reason, so the slides and the Q&A answers can be taken straight from this page.

Status: **proposed** = in the script, not yet agreed by the team. **agreed** = team confirmed. **open** = needs a decision.

| # | Decision | Choice | Reason | Status |
|---|---|---|---|---|
| 1 | Unit of analysis | Three separate analyses, one per arm | Outcomes are arm-specific and on different scales | proposed |
| 2 | Primary outcome | Continuous outcome; responder label reported alongside | The label is derived from the continuous value, so it carries less information; about 40 test patients per arm | proposed |
| 3 | Split | 75/25 per arm, stratified by responder label and onset phenotype, seed 20261011, test set used once | Kickoff rules; phenotype added after the organizers' example of a biased split | proposed |
| 4 | Covariate models | Stepwise (BIC), LASSO, elastic net | Taught at kickoff; BIC penalises extra covariates | proposed |
| 5 | ML models | Random forest; XGBoost untuned and tuned on a 6-point grid | Taught at kickoff; small grid because arms are small | proposed |
| 6 | Signal vs noise | "signal" = at least 4 of 5 methods pick it and LASSO keeps it in 60% or more of 200 bootstrap resamples; "uncertain" = at least 2 votes and stability 20% or more; otherwise noise. A pure-noise probe column is the negative control (its stability is 6 to 12%) | Agreement across methods builds confidence; the stability floor for "uncertain" stops the two ML votes alone (a low bar) from promoting noise | proposed |
| 7 | Random-forest selection | Permutation importance above the noise probe (kickoff slide 72). Boruta removed | Taught at kickoff; uses what the forest already computes; same leaders in every arm | proposed |
| 8 | Metrics | Continuous: RMSE, MAE, R². Label: ROC-AUC, recall, precision, accuracy at a cut-off equal to the training responder share (0.29 / 0.41 / 0.48). Bootstrap 95% intervals | Kickoff recommendations. At 0.5 the Mexiletine models found 0 to 17% of responders because only 29% respond; the share cut-off is fixed before the test set is seen | proposed |
| 9 | Class imbalance | No oversampling. Check responder share per arm first; use class weights or a different cut-off only if an arm is badly imbalanced | Oversampling was not taught, risks leakage, and does not apply to the continuous outcome | proposed |
| 10 | Stratification rule | Two-level decision tree built from consensus covariates only, checked on test patients | Gives a rule that can be said aloud; cannot split on noise | proposed |
| 12 | Split sensitivity | `analysis/sensitivity_splits.R` repeats the split and test-set scoring with 20 seeds, continuous outcome. The single locked split stays the main result | Suggested by Leo; about 41 test patients is noisy, so show that the method pattern does not depend on one draw | proposed |
| 11 | "Linear with cut-off" model | Consensus linear model where the top covariate enters as above/below a cut-off chosen by a one-level tree on training patients | Exploration on training data showed the Tideglusib outcome steps at cognitive_function about -0.5 rather than sloping; this keeps an explainable model competitive with ML | proposed |

## Data cleaning decisions

Filled in after the first run on real data. One row per rule. Decide from baseline columns and plausibility, never from the outcome.

| # | Issue found | Action | Reason | Patients affected |
|---|---|---|---|---|
| C1 | `albumin` is 4.18 for every Mexiletine patient | Dropped as a predictor in the Mexiletine arm only (automatic: any covariate with a single value among an arm's training patients is dropped there). **proposed** | A constant cannot predict anything, and it breaks scaling. 4.18 is the median of the whole dataset, which suggests the column was filled in for this arm. Kickoff slide 44: "note how much each one varies" | All 161 Mexiletine patients; no rows removed |
| C2 | `ck_level`: 32% of patients are exactly 50, none below | Keep as is; state the floor on the cleaning slide. **proposed** | Looks like a floor or detection limit. Tree models are unaffected; linear models treat 50 as a real value | About 160 |
| C3 | `somatic_mosaicism_index`: 15% of patients are exactly 0 | Keep as is. **proposed** | Lower bound of a 0 to 1 index. These patients have short repeats (median 107 against 316 for the rest), and short repeats are stable, so 0 is plausible | About 75 |
| C4 | `albumin`: 9 values beyond 3 IQR (3.14 to 5.35) in the other two arms | Keep as is. **proposed** | Within a physiologically plausible range; flagged only because most values sit close to 4.2 | 9 |
| | No missing values, no duplicate rows or IDs, no inconsistent category spellings, age minus onset equals duration for every patient | None needed | Checked on the full file | |

Design fact from the data dictionary: `treatment_arm` was "assigned by a weighted random draw informed by each patient's relative fit across all three arms; not purely random". Arms are therefore not randomised samples of the same population. Findings describe who does well within each arm as enrolled.

## Expectations written before seeing results

From the organizers' hints and the drugs' mechanisms. To be compared with what the data selects.

| Arm | Expected predictors | Confirmed? |
|---|---|---|
| Mexiletine (symptom relief) | Baseline `myotonia_severity`; possibly `phenotype` | |
| Oligonucleotide (toxic RNA) | `ctg_repeats`, `somatic_mosaicism_index`, `muscle_strength`; possibly `disease_duration` | |
| Tideglusib (multi-tissue) | `cognitive_function` and a motor measure such as `muscle_strength` | |
