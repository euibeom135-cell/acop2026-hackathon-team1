# Team 1 slide outline (5-minute talk, 3-minute Q&A, one judge question)

Five slides. Brackets are filled from `dm1_outputs/` after `Rscript dm1_analysis.R` runs on the real data.
Scoring: Clinical 10, Technical 10, Communication 10. "Meaningful covariate identification matters more than fancy models."
Due: slides and code in the Team 1 SharePoint folder by Tue Oct 13, 11:59 PM ET. Nominate one representative to email the chairs when the final slides are up.

## 1. Answer first (30 s) — Communication
- Title: "Does ML find more than covariate modelling? [Yes / No / Only in arm X]"
- One sentence: "Across three arms, [N] baseline features drive response; ML [did / did not] add predictors or accuracy beyond penalised regression."

## 2. Workflow (45 s) — Technical
- Six-step strip: Understand, Split, Preprocess, Select, Train, Evaluate.
- Per-arm 75/25 split, stratified by responder label, fixed seed; test set used once; tuning by 5-fold CV inside training; scaling and imputation learned on training only.
- Noise handling, three checks: a pure-noise "probe" covariate as negative control, LASSO stability over 200 resamples, agreement across five methods.
- Outcome: continuous as primary (the responder label is derived from it, so it carries less information); label metrics reported alongside.

## 3. What drives response, per arm (75 s) — Clinical
- Figure: `fig_covariate_matrix.png` (filled dot = method picked it).
- One line per arm, signal covariates only:
  - Mexiletine (myotonia change, 12 wk): [covariates]
  - Oligonucleotide (QMT change, 26 wk): [covariates]
  - Tideglusib (composite, 26 wk): [covariates]
- Name the plausible-looking covariates that turned out to be noise: [list].

## 4. Clinical sense, and covariate models vs ML (75 s) — Clinical, Technical
- Figures: `fig_effects_<arm>.png` (direction and size per 1 SD) and `fig_scoreboard.png`.
- One mechanism line per arm, to be checked against the results:
  - Mexiletine blocks sodium channels, so benefit should track baseline myotonia severity.
  - The oligonucleotide lowers toxic RNA, so CTG repeats, mosaicism and remaining muscle strength should matter.
  - Tideglusib acts across tissues, so a motor and a cognitive feature may both contribute.
- ML message: "[matched / beat / lost to] penalised regression; intervals overlap with about 40 test patients per arm, so we do not rank on small gaps."
- Covariates only ML picked ("uncertain" with random forest and XGBoost votes): [covariate], a candidate nonlinearity or interaction.

## 5. So what (60 s) — all three
- Figure: `fig_strata_<arm>.png` (held-out patients grouped by predicted benefit vs observed responder rate).
- One stratification or trial-design implication per arm: enrich or stratify on [covariate] for [drug].
- Limits: simulated data, one split, small arms.
- AI disclosure: Claude (Anthropic) via Claude Code for code drafting and workflow design [add InsightRX Astra if used]; the team reviewed every step.

## Likely judge questions
1. How did you separate signal from noise? Noise probe, bootstrap stability, five-method agreement.
2. Why continuous over binary? The label is derived from it; both are reported.
3. Why did ML not win (or win)? [Additive linear signal / interaction found in arm X.]
4. Correlated covariates (age, onset, duration)? [What the correlation check showed; elastic net keeps correlated ones together.]
5. Would the result survive a different split? [Stability percentages; optionally repeat with other seeds.]
