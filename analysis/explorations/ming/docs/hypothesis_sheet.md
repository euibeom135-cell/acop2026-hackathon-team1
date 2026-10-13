# DM1 covariate analysis — pre-registration

**Committed:** Monday, 12 October 2026, before the locked fold-1 run (gate G3).
**Analyst team:** orchestrated agentic pipeline (see `CLAUDE.md`).
**Data:** `inputs/dm1_clinical_trial_dataset.csv` (500 simulated patients;
source SHA-256 in `results/analysis_metadata.json`).

This sheet fixes the endpoints, methods, decision rules and signal criteria
**before** the locked test set (fold 1) is opened. Rehearsal (fold 5 pseudo-test)
may be inspected; fold 1 may not. Deviations are logged in `docs/LOG.md`.

## Endpoints
- **Primary (continuous), per arm — higher = more improvement:**
  - Mexiletine: *relative* myotonia change, `−myotonia_change_12wk / baseline
    myotonia_severity` (the 45% responder rule is relative; absolute change is
    mechanically explained by baseline severity).
  - Oligonucleotide: `qmt_change_26wk`.
  - Tideglusib: `tideglusib_composite`.
- **Secondary (binary):** the arm's responder label, cutoff chosen on training
  out-of-fold predictions (Youden's J).

## Methods (pre-specified, 14 per task, one interface)
Inference tier: OLS/logistic (all terms); stepwise AIC; stepwise BIC; best
subset (BIC, ≤5 terms); LASSO; elastic net; ridge; GAM (cubic splines).
Prediction tier: random forest; gradient boosting untuned; gradient boosting
tuned; SVM tuned; kNN tuned; MLP tuned. (Gradient boosting = scikit-learn
HistGradientBoosting; XGBoost's role, no OpenMP runtime available.)
Bridge: stability selection; shuffled-outcome null; cross-method agreement;
cross-seed selection frequency.

## Covariate priors (direction expected on improvement_score)
| Arm | Expected real drivers | Direction | Rationale |
| --- | --- | --- | --- |
| Mexiletine | myotonia_severity, ctg_repeats | severity ↔ response | myotonia is the drug's direct target; CTG repeats index severity |
| Mexiletine | disease_duration | − (longer → less) | established fibrosis responds less |
| Oligonucleotide | ctg_repeats, somatic_mosaicism_index | − (higher burden → less) | splicing-correction ceiling set by repeat/mosaicism burden |
| Oligonucleotide | muscle_strength (baseline) | context | QMT change depends on baseline capacity |
| Tideglusib | cognitive_function | threshold/step near z≈−0.5 | composite is cognition-weighted; expect a non-linear bend |
| Tideglusib | disease_duration, age_at_onset | phenotype axis | onset/duration define the responsive subtype |

Weak / unstable candidates expected to flip across resamples: BMI, PR interval,
CK, insulin resistance, smoking, sex, cataracts, the repeats×strength interaction.

## Decision rules (fixed now)
- **Real signal** iff a term is *stable* (selection frequency ≥ 0.6 over 100
  half-subsamples) **and** beats the shuffled-outcome null (observed RF grouped
  importance > 95th percentile of the 50-permutation null).
- **Consensus covariate** iff mean(inference-kept rate, ML-top5 rate) ≥ 0.5.
- **Compact model**: the 1–3 top consensus covariates; reported with bootstrap CI.
- **Stratification rule**: a single data-chosen threshold (depth-1 tree) on the
  leading numeric consensus term, reported only if it recovers the forest's gain
  over the linear term.
- **Scoring discipline**: fold 1 scored once, at the final run; the fold-1 hash
  (`outputs/splits/summary.json`) is confirmed first.

## Primary conclusion to be tested
*Which patients are held out moves the scores; it does not move the covariates.*
Supported by the 20-seed per-method test-R² SD and the cross-seed selection
frequencies, not by any single split.
