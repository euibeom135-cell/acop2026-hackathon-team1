# euibeom

Three questions left open by the first run of the main script. Training patients only; the test set is not used. Cross-validated R2 is 5-fold, inside the training set.

Run any script from this folder: `Rscript 1_tideglusib_why_ml_wins.R`

| Script | Question | Finding |
|---|---|---|
| `1_tideglusib_why_ml_wins.R` | Why did ML beat the linear models? | The outcome steps down at `cognitive_function` of about -0.5 (mean score about 8 below, about 3.5 above). A straight line fits a step badly. A linear model with a yes/no cut-off matches the random forest: R2 0.47 vs 0.45, straight line 0.38. |
| `2_oligonucleotide_weak_signal.R` | Why is the continuous outcome poorly predicted? | The `ctg_repeats` effect is real and steady (mean change -0.1 in the lowest fifth, 2.2 in the highest), but patients with the same repeat length differ a lot. Nothing tried adds reliably (R2 0.17 to 0.25); random forest is worse (0.15). A weak-signal arm, not a missed pattern. |
| `3_mexiletine_responder_label.R` | Why does the responder model find so few responders? | The label means "myotonia fell by 45% or more of baseline", a relative rule, while the continuous outcome is the absolute fall, which is mostly room to improve (baseline `myotonia_severity` alone: R2 0.69). With 29% responders, a 0.5 cut-off finds 34% of them; using the responder share as the cut-off finds 71% at the same precision (about 0.5). |

| `4_which_drug_for_whom.R` | Can the three per-arm models be read as one stratification map? | For every training patient, the responder likelihood under each drug relative to that arm's average patient. Best bet: Mexiletine for 12% (very high myotonia, median repeats about 530), Tideglusib for 35% (impaired cognition, median z about -0.9), the oligonucleotide for the remaining 53%. Also a check of the data dictionary's claim that arm assignment was "informed by relative fit": actual arm matches predicted best drug for 41% of patients, against 33% by chance, so the weighting was mild or along other axes. Extrapolates each arm's model to other arms' patients; no outcomes are used across arms; suggestive, not a result for the scoreboard. |
| `5_covariate_forest.R` | Can the findings be shown the way a pharmacometric covariate report shows them, and do they hold in each onset group? | Forest plot of predicted responder probability for a reference patient (median covariates, adult onset) against the key covariate at its 10th and 90th percentile and against each onset phenotype, with 90% bootstrap intervals (`fig_covariate_forest.png`, `forest_scenarios.csv`). Mexiletine: 17% to 38% across the myotonia range; late onset 11%. Oligonucleotide: 22% to 75% across the repeat range. Tideglusib: 87% to 14% across the cognition range; onset group adds nothing. The key covariate keeps the same sign inside every onset phenotype (`key_covariate_within_phenotype.csv`); the slope differs by phenotype only in Mexiletine (interaction p = 0.03, flatter in late onset, n = 21). |

## Suggestions for the team

1. Tideglusib: report the cut-off model next to the ML models, and use "cognitive_function below about -0.5" as the stratification rule.
2. Oligonucleotide: report `ctg_repeats` as the one key covariate and say plainly that prediction for an individual patient is weak.
3. Mexiletine: say on the slide that absolute change mostly reflects baseline severity, and use the responder share as the classification cut-off.

AI use: scripts written with Claude (Anthropic) via Claude Code; run and checked by Euibeom Shin.
