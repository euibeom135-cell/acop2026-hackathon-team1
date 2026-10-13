# Team 1 slide outline (5-minute talk, 3-minute Q&A, one judge question)

Five slides plus two backup slides. Numbers are from the run of `analysis/dm1_analysis.R` and the explorations in `analysis/explorations/euibeom/` on 11 October 2026; replace them from `results/` after the official team run. Figures named here are in `analysis/dm1_outputs/` unless stated.
Scoring: Clinical 10, Technical 10, Communication 10. "Meaningful covariate identification matters more than fancy models."
Due: slides and code in the Team 1 SharePoint folder by Tue Oct 13, 11:59 PM ET. One representative emails the chairs when the final slides are up.
References: `references.md`, one per claim, in small type on the slide that makes the claim.

## 1. Answer first (30 s) — Communication

- Title: "Each drug has one predictor, and it is the measurement nearest where the drug acts"
- Table, three rows:

| Drug | Main covariate | Held-out responders, high vs low |
|---|---|---|
| Mexiletine (symptomatic) | Myotonia severity | 48% vs 10% |
| Oligonucleotide (targets the RNA) | CTG repeat length | 59% vs 31% |
| Tideglusib (multisystem) | Cognitive function | 74% vs 17% |

- One sentence: "Five methods agree on each; machine learning found no new predictors; the planted noise column was never selected."
- Say aloud: mexiletine lower is better, the other two higher is better.

## 2. Disease, data and workflow (50 s) — Technical, Clinical

- Left: the chain *repeat → toxic RNA → mis-splicing → organ damage → symptom*, with the three drugs marked at their link (mexiletine at symptom; oligonucleotide at RNA; tideglusib at mis-splicing/GSK3β). Refs 1, 7, 8.
- Right: the six-step strip: Understand, Split, Preprocess, Select, Train, Evaluate.
- Three bullets: per-arm 75/25 split stratified by responder and onset phenotype, fixed seed, test set scored once; all tuning by 5-fold CV inside training; cleaning decided from baseline columns only.
- Cleaning line: "No missing values, but albumin was a single filled-in value for every mexiletine patient; dropped in that arm. CK floor at 50 and mosaicism at 0 kept as is. No patient removed."
- Noise handling, three checks: planted noise probe, LASSO stability over 200 resamples, agreement across five methods.

## 3. What drives response, per arm (80 s) — Clinical

- Figure: `explorations/euibeom/fig_covariate_forest.png` (replaces the effect-size figure): reference patient, key covariate at 10th and 90th percentile, each onset phenotype; predicted responder probability with 90% bootstrap interval. Say: "presented in the standard pharmacometric covariate format".
- Read one row per arm:
  - Mexiletine: myotonia 2 → 7.7 moves response 17% → 38%; late onset lower (11%) because there is little myotonia to treat. Symptomatic drug, effect scales with the symptom. Refs 5, 6.
  - Oligonucleotide: repeats 73 → 510 moves response 22% → 75%; the only predictor. Target-engagement drug, effect scales with the substrate. Individual prediction weak (R² < 0.1). Ref 7.
  - Tideglusib: cognition -1.2 → 0.27 moves response 87% → 14%; a step at about -0.5, not a slope. Composite endpoint with a cognitive part: normal cognition has no room to improve. Refs 8, 9.
- Disease-wide vs arm-specific: CTG repeats carries signal in two arms and the same trend in the third (prognostic-like); cognition matters in one arm only (treatment-specific-like). Without a placebo arm these are readings, not proofs.
- Noise list, one line: sex, BMI, smoking, cataracts, CK, PR interval, albumin were noise in every arm; disease duration borderline everywhere.

## 4. Covariate models vs machine learning (60 s) — Technical

- Figures: `fig_covariate_matrix.png` (small, top) and `fig_scoreboard.png` (main).
- Three bullets:
  - Same leaders from stepwise, LASSO, elastic net, random forest (permutation importance) and XGBoost (SHAP); noise probe last or near last in every arm.
  - Test-set R²: Mexiletine about 0.5 for every method; Oligonucleotide under 0.1 for every method; Tideglusib trees 0.55 vs straight lines 0.24 to 0.30.
  - Why ML won in one arm: the step. A linear model with one cut-off (chosen in training) reaches 0.45. Tuned XGBoost chose depth-1 trees everywhere: no interactions to find.
- Closing line: "Intervals overlap with about 41 test patients per arm; we do not rank methods inside an arm. ML was the check that nothing was missed."

## 5. So what, limits, AI (40 s) — all three

- Stratification proposal, one line: "Measure the organ the drug acts on: myotonia before mexiletine, repeat length before the antisense drug, cognition before tideglusib. One routine measurement per drug separates groups that differ 2- to 5-fold in response."
- Small figure: `fig_strata_Tideglusib.png` (held-out thirds by predicted benefit: 21 / 46 / 79%).
- Trial-design implication, one line per arm (judge Sarah Kim works on model-based trial design):
  - Mexiletine: enrol by baseline myotonia severity, not by diagnosis; mild-myotonia patients dilute the effect (ref 5, the null 6-minute-walk trial).
  - Oligonucleotide: stratify randomisation by repeat length; the only predictor, and prognostic, so imbalance would bias a small trial.
  - Tideglusib: enrich for impaired cognition; expected response about 48% → 74%, so a smaller trial can show an effect.
- Next step, said before a judge asks: "This dataset is one time point per patient. The natural next step is a disease-progression model on repeated measures, where these baseline covariates become covariates on progression rate and drug effect."
- Robustness line: "We repeated the split 20 times; the pattern held in every arm." (backup figure `fig_sensitivity_splits.png`)
- Limits: no placebo arm (who does well on the drug, not who the drug helps); 41 test patients per arm, so cut-offs are "about 5, about 350, about -0.5"; arm assignment not random; the test set was scored twice, both runs logged; real DM1 would add repeat interruptions, somatic expansion rate, splicing biomarkers, exposure.
- AI disclosure: "Claude (Anthropic) via Claude Code for code drafting, workflow design and documentation; Codex / Claude Code by individual members for explorations. Every analysis choice was reviewed and is the team's."

## Backup C. Split sensitivity

- `dm1_outputs/fig_sensitivity_splits.png` and `sensitivity_splits.csv`: test R² over 20 splits. Mexiletine: all methods tie, median about 0.6. Oligonucleotide: all weak, medians 0.06 to 0.12. Tideglusib: tree models first on 19 of 20 splits, linear never.

## Backup A. Does the key covariate hold within each onset group? (for Q&A)

- Table from `explorations/euibeom/key_covariate_within_phenotype.csv`: slope of the outcome per unit of the key covariate, by adult / juvenile / late onset, with the interaction p-value.
- Message: same direction in every onset group in every arm; the slope differs only for mexiletine (p = 0.03, flatter in late onset, n = 21).

## Backup B. Which drug for whom (for Q&A)

- From `explorations/euibeom/4_which_drug_for_whom.R`: each arm's responder model applied to all training patients, relative to that arm's average patient. Best bet: mexiletine for 12% (very high myotonia), tideglusib for 35% (impaired cognition), oligonucleotide for the rest.
- Say it is an extrapolation across arms, no outcomes used across arms, a proposal not a result.
- Arm-assignment check: actual arm matches predicted best drug for 41% of patients vs 33% by chance, so the dictionary's "weighted by fit" was mild.

## Likely judge questions

1. How did you separate signal from noise? Planted noise probe (never selected), LASSO stability (leaders 90 to 100%, probe 6 to 12%), five-method agreement with a stability floor for "uncertain".
2. Why continuous over binary? The label is the continuous value cut at one point, so it carries less information; both are reported; responder cut-off set at the training responder share because mexiletine has only 29% responders.
3. Why did ML win in tideglusib only? A threshold in cognitive function; linear models cannot draw a step; one cut-off closes most of the gap. Depth-1 XGBoost everywhere: no interactions.
4. Correlated covariates? CTG and myotonia severity r = 0.88; age and onset r = 0.85; muscle strength and duration r = -0.75. Elastic net keeps pairs together; stepwise picks one; we present them as pairs.
5. Would the result survive a different split? Stability percentages; Bei's independent Python screen on an 80/20 split found the same leaders.
6. Is the oligonucleotide result a failure? No: the repeat-length effect is real and in the right direction; individual prediction is weak, which matches the clinical trial experience (ref 7).
7. Why no oversampling / class weights? Not taught, risks leakage, irrelevant to the continuous outcome; the cut-off change solves the recall problem.
