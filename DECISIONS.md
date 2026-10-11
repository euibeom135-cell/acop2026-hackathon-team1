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
| 6 | Signal vs noise | A covariate is "signal" if at least 4 of 5 methods pick it and LASSO keeps it in 60% or more of 200 bootstrap resamples. A pure-noise probe column is the negative control | Agreement across methods builds confidence; thresholds are a judgement call | proposed |
| 7 | Random-forest selection | Boruta (shadow-feature test) | Established, but not taught at kickoff. Alternative: permutation importance above the noise probe (kickoff slide 72) | **open** |
| 8 | Metrics | Continuous: RMSE, MAE, R². Label: ROC-AUC, recall, precision, accuracy at cut-off 0.5. Bootstrap 95% intervals | Kickoff recommendations | proposed |
| 9 | Class imbalance | No oversampling. Check responder share per arm first; use class weights or a different cut-off only if an arm is badly imbalanced | Oversampling was not taught, risks leakage, and does not apply to the continuous outcome | proposed |
| 10 | Stratification rule | Two-level decision tree built from consensus covariates only, checked on test patients | Gives a rule that can be said aloud; cannot split on noise | proposed |

## Data cleaning decisions

Filled in after the first run on real data. One row per rule. Decide from baseline columns and plausibility, never from the outcome.

| # | Issue found | Action | Reason | Patients affected |
|---|---|---|---|---|
| | | | | |

## Expectations written before seeing results

From the organizers' hints and the drugs' mechanisms. To be compared with what the data selects.

| Arm | Expected predictors | Confirmed? |
|---|---|---|
| Mexiletine (symptom relief) | Baseline `myotonia_severity`; possibly `phenotype` | |
| Oligonucleotide (toxic RNA) | `ctg_repeats`, `somatic_mosaicism_index`, `muscle_strength`; possibly `disease_duration` | |
| Tideglusib (multi-tissue) | `cognitive_function` and a motor measure such as `muscle_strength` | |
