# Results

Outputs of `analysis/dm1_analysis_onefile.R` (equivalently `dm1_analysis.R` + `R/common.R`) on the locked 75/25 split, seed 20261011, plus `sensitivity_splits.R` (20 seeds) and the covariate forest plot from `analysis/explorations/euibeom/5_covariate_forest.R`. Aggregate tables and figures only; no patient-level data.

| File | What it holds |
|---|---|
| `scoreboard_<arm>.csv`, `scoreboard_all_arms.csv`, `fig_scoreboard.png` | Test-set metrics for every method: RMSE, MAE, R² with bootstrap CI; AUC, recall, precision, accuracy |
| `covariates_<arm>.csv`, `covariates_all_arms.csv`, `fig_covariate_matrix.png` | Which method selected which covariate; LASSO bootstrap stability; the signal / uncertain / noise call |
| `tree_<arm>.csv`, `fig_tree_<arm>.png` | The read-aloud rule and the test-set responder rate in each branch |
| `strata_<arm>.csv`, `fig_strata_<arm>.png` | Test patients in thirds by predicted benefit, with observed responder rates |
| `effects_<arm>.csv`, `fig_effects_<arm>.png` | Effect per 1 SD of each consensus covariate, with 95% CI |
| `fig_shap_<arm>.png` | SHAP values from the tuned XGBoost model, training patients |
| `eda_numeric_<arm>.csv`, `eda_categorical_<arm>.csv`, `fig_eda_*.png` | Exploratory tables and figures, training patients |
| `sensitivity_splits.csv`, `sensitivity_splits_all.csv`, `fig_sensitivity_splits.png` | Test R² over 20 different train/test splits |
| `forest_scenarios.csv`, `fig_covariate_forest.png`, `key_covariate_within_phenotype.csv` | Predicted response for the reference patient and covariate scenarios; the key covariate within each onset phenotype |
| `data_checks.txt`, `session_info.txt` | Data checks printed by the script; R and package versions |
