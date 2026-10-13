# Team context brief

For a teammate, or a teammate's AI assistant (Claude Code, Codex, a chatbot), who has not followed Euibeom's working sessions. Read this, then `AGENTS.md` for the rules and `DECISIONS.md` for the choice log. Last updated 13 October 2026, morning.

## The task, in two lines

Simulated DM1 trial, 500 patients, three arms (mexiletine, antisense oligonucleotide, tideglusib), 18 baseline covariates, some noise by design. Per arm: which covariates predict response, and does machine learning add anything beyond covariate models? Slides and code due to the Team 1 SharePoint folder by Tuesday 13 October, 11:59 PM ET; five-minute talk Wednesday 9:00 AM; judge Sarah Kim (UF, pharmacometrics, disease-progression modelling).

## The answer the team has converged on

| Arm | Dominant predictor | Mechanism reading | Covariate vs ML |
|---|---|---|---|
| Mexiletine | Myotonia severity (CTG repeats is its near-twin, r 0.88) | Symptomatic drug: effect scales with the symptom present | Equivalent |
| Oligonucleotide | CTG repeat length | Target-engaging drug: effect scales with the toxic transcript | Equivalent, all weak (R² under 0.15) |
| Tideglusib | Cognitive function, as a threshold near z = -0.5 | Composite endpoint with a cognitive domain: ceiling effect | Tree ensembles ahead because of the step; one cut-off closes most of the gap |

Four independent pipelines found the same three covariates: Euibeom (R, 75/25, seed 20261011), Leo (R zip), Wenzhe (Python + R, 80/20 and 20 re-randomised splits), Ming (Python, rehearsal on a pseudo-test). The planted pure-noise covariate was never selected. Noise in every arm: sex, BMI, smoking, cataracts, CK, PR interval, albumin. Borderline everywhere: disease duration (longer duration, less response; "signal" in Wenzhe's rule, which drops age).

Stratification message: measure the organ the drug acts on. Held-out test patients who responded, above vs below the training-set cut-off: mexiletine 10 of 21 (48%) vs 2 of 20 (10%); oligonucleotide 10 of 17 (59%) vs 8 of 26 (31%); tideglusib 17 of 23 (74%) vs 3 of 18 (17%).

## Where things live

| What | Where |
|---|---|
| The deck (current master; edit in place, do not regenerate) | `slides/Team1_DM1_slides.pptx`, speaker notes on every slide |
| The full report (page 1 and 2 are the conclusion) | `slides/5_analysis_report.pdf`; annotated copy alongside |
| The code the deck's numbers come from | `analysis/dm1_analysis_onefile.R` (one file) = `analysis/R/common.R` + `analysis/dm1_analysis.R` |
| 20-seed split sensitivity | `analysis/sensitivity_splits.R` |
| Euibeom's follow-ups (why ML wins in tideglusib, why the oligonucleotide arm is weak, the mexiletine label, which drug for whom, forest plot) | `analysis/explorations/euibeom/` |
| Bei's correlation screen | `analysis/explorations/bei/` |
| Wenzhe's two pipelines and the three-pipeline comparison | `analysis/explorations/wenzhe/` |
| Ming's agentic pipeline | `analysis/explorations/ming/` |
| Decisions and reasons | `DECISIONS.md` |
| AI tools used | `AI_DISCLOSURE.md` |
| References for the slides | `slides/references.md` |
| Talk outline with timings and judge Q&A | `slides/presentation_outline.md` |

The dataset is never in the repository. Each person keeps it in `analysis/data/` locally.

## Definitions that differ between pipelines (so numbers can be compared)

- Split: Euibeom 75/25 stratified by responder and onset phenotype (seed 20261011); Bei, Wenzhe (pdf_pipeline) and Ming's fold 1: 80/20 stratified by responder (Bei seed 20261011, Wenzhe seed 42); Wenzhe split_1to3 and Ming repeat20: re-randomised. Different test sets, so single-split R² differs by noise; the 20-split medians agree.
- Mexiletine continuous target: the dataset's absolute change column (Euibeom, Wenzhe, Leo, Bei) vs relative change, change ÷ baseline (Ming). Relative change divides out the severity signal by construction, which is why Ming's rule calls myotonia "suggestive" while the others call it dominant. Team position: the organizers' column is primary; the responder label (a relative rule, 45% fall) is reported alongside.
- `age`: kept by Euibeom; dropped by Wenzhe and Ming because age = onset + duration. Dropping it makes disease duration look stronger.
- Responder cut-off: training responder share (Euibeom, Wenzhe) or Youden on out-of-fold scores (Wenzhe pdf_pipeline, Ming); never 0.5, because mexiletine has 29% responders.
- Gradient boosting: XGBoost everywhere except Ming (scikit-learn HistGradientBoosting; no OpenMP).

## Open items (as of this brief)

1. Team sign-off on the decisions in `DECISIONS.md` (all marked "proposed").
2. Presenter and the representative who emails the organizers.
3. Whether Ming runs the final (fold-1) scoring today; the deck currently quotes the R pipeline and 20-split medians.
4. Make the repository public before submission: remove `slides/1_kickoff_slides_original.pdf` (organizers' material) first; the link is already on slide 3 and in the AI disclosure.
5. SharePoint upload: deck, code zip (`git archive`), report; then the email.

## Answers to likely judge questions

- How did you separate signal from noise? A planted noise covariate (never selected), LASSO stability over 200 resamples (leaders 90 to 100%, noise 6 to 12%), agreement across five methods; Wenzhe and Ming add a shuffled-outcome random-forest null; four pipelines agree.
- Why did ML win in tideglusib only? A threshold in cognition; straight lines cannot draw a step; tuned XGBoost chose depth-1 trees, so no interactions; a linear model with one cut-off reaches about 0.45 vs 0.55.
- Why is the oligonucleotide arm weak? The repeat-length effect is consistent (mean change rises steadily with repeats) but between-patient variability dominates; no transformation or second covariate helps; honest to say direction is knowable, the individual is not.
- Correlated covariates? CTG and myotonia severity r 0.88; age and onset 0.85; strength and duration -0.75. Presented as pairs; elastic net keeps both, stepwise picks one.
- Would it survive a different split? 20 repeated splits: same pattern in every arm; absolute R² moves by up to 0.15, hence ranges, not point estimates.
- Continuous or binary? Continuous primary (the label is the continuous value cut at one point); label alongside; responder rates used for the stratification message.
- Trial design? Enrol mexiletine on baseline myotonia; stratify oligonucleotide randomisation on repeat length (prognostic); enrich tideglusib for cognitive impairment (48% to 74% expected responders).
- Limits? No placebo arm (prognostic within treated patients, not effect modification); about 41 test patients per arm; cross-sectional; next step a longitudinal disease-progression model.

## AI use

Claude (Anthropic) via Claude Code drafted the shared code, documentation, report and deck for Euibeom; Codex and Claude Code were used by other members for their pipelines; Ming's package used Claude Code agents. Every analysis decision was reviewed by the team, which is accountable for the results. Recorded in `AI_DISCLOSURE.md` and in the code headers.
