# Analysis

Repository: https://github.com/euibeom135-cell/acop2026-hackathon-team1


One script, `dm1_analysis.R`, runs everything for all three arms. It gets the cleaned data and the train/test split from `R/common.R`, which the per-member `explorations/` also use, so everyone works from the same split.

## Run

1. Put the dataset in `data/` (any `.xlsx` or `.csv` whose name contains `DM1`).
2. `Rscript install_packages.R` (first time only)
3. `Rscript dm1_analysis.R` (about one minute)

## What it prints

1. **Data checks:** label spellings fixed, duplicates removed, and a list of things for the team to decide (extreme values, impossible ages, text in numeric columns).
2. **Per arm:** sample sizes, responder share and phenotype mix in training vs test; correlated covariates; the covariate calls; the test-set scoreboard; the stratification rule.
3. **Summary:** signal covariates per arm.

## Outputs

Your own run writes to `dm1_outputs/` (not uploaded). The team's official copy lives in `../results/` and is produced with `DM1_OUT=../results Rscript dm1_analysis.R`. Both contain the same files:

| File | What it is | Used for |
|---|---|---|
| `data_checks.txt` | Everything the data checks found | Cleaning decisions |
| `covariates_<arm>.csv`, `covariates_all_arms.csv` | Per covariate: which of the five methods picked it, LASSO stability %, and the call (signal / uncertain / noise) | Slide 3 |
| `fig_covariate_matrix.png` | Dot grid of method vs covariate, per arm | Slide 3 |
| `effects_<arm>.csv`, `fig_effects_<arm>.png` | Direction and size of each consensus covariate, per 1 SD, with 95% intervals | Slide 4 |
| `fig_shap_<arm>.png` | SHAP summary for the tuned XGBoost model | Slide 4 or backup |
| `scoreboard_<arm>.csv`, `scoreboard_all_arms.csv` | Test-set RMSE, MAE, R², ROC-AUC, recall, precision, accuracy for every method, with bootstrap intervals | Slide 4 |
| `fig_scoreboard.png` | Covariate models vs ML, test-set R² | Slide 4 |
| `tree_<arm>.csv`, `fig_tree_<arm>.png` | Two-level decision rule and the responder rate in each group among test patients | Slide 5 |
| `strata_<arm>.csv`, `fig_strata_<arm>.png` | Test patients in thirds by predicted benefit vs observed responder rate | Slide 5 |
| `session_info.txt` | R and package versions used | Reproducibility |

## Reading the covariate calls

- **signal:** at least 4 of 5 methods picked it and LASSO kept it in 60% or more of resamples.
- **uncertain:** 2 or 3 methods picked it. If those are the ML methods only, look for a curved effect or an interaction; that is where ML may have added something.
- **noise:** at most one method picked it.
- **negative control:** the random probe column. Anything ranked at or below it is noise.

## Changing things

- Column names: edit `num_cov`, `cat_cov` and the `arms` table in `R/common.R`.
- Cleaning rules: add one line each in the marked "Team cleaning decisions" block in `R/common.R`, with the reason, and log it in `../DECISIONS.md`.
- Options without editing: `DM1_DATA=path/to/file` and `DM1_OUT=folder` environment variables.
