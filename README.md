# ACoP 2026 Hackathon, Team 1: Beyond CTG repeats

Which baseline measures predict who responds to three DM1 treatments, and does machine learning find more than standard covariate models? A simulated trial of 500 patients, three arms (mexiletine, antisense oligonucleotide, tideglusib), 18 baseline covariates, some of them noise by design.

**Answer.** Each arm has one dominant baseline predictor, and it is the measure closest to the drug's site of action: myotonia severity for mexiletine (one axis with CTG repeat length), CTG repeat length for the antisense oligonucleotide, cognitive function for tideglusib, as a threshold near z = -0.5. Machine learning selected the same covariates and added no new predictor; it was ahead in one arm only, because that effect is a step, and a linear model with one cut-off recovers most of the gap. A planted pure-noise covariate was never selected. Four independent pipelines (R and Python, different splits) reached the same three covariates.

## Start here

| File | What it is |
|---|---|
| [`slides/Team1_DM1_slides.pptx`](slides/Team1_DM1_slides.pptx) | The talk: 8 slides plus backups, speaker notes on every slide |
| [`analysis/dm1_analysis_onefile.R`](analysis/dm1_analysis_onefile.R) | The analysis in one R file; every number on the slides comes from its outputs ([PDF listing](analysis/dm1_analysis_onefile.pdf)) |
| [`results/`](results/) | The outputs of that script: tables and figures the slides quote |
| [`slides/5_analysis_report.pdf`](slides/5_analysis_report.pdf) | Full report, pages 1 and 2 are the conclusion ([annotated copy](slides/5_analysis_report_annotated.pdf) with plain-English notes) |
| [`DECISIONS.md`](DECISIONS.md) | Every analysis choice and its reason |
| [`AI_DISCLOSURE.md`](AI_DISCLOSURE.md) | Which AI tools were used, and for what |

## Reproduce

The dataset is not in this repository. Place `dm1_clinical_trial_dataset.csv` in `analysis/data/`, then:

```bash
Rscript analysis/install_packages.R          # once
cd analysis && Rscript dm1_analysis_onefile.R   # about a minute; writes dm1_outputs/
Rscript sensitivity_splits.R                    # optional, 20 repeated splits, about 12 minutes
```

`dm1_analysis_onefile.R` is `R/common.R` and `dm1_analysis.R` joined for reading; the two-file form is what the explorations source.

## Workflow

Per arm: 75/25 train/test split stratified by responder status and onset phenotype, fixed seed, test set scored once. All model choices by 5-fold cross-validation inside the training set. Covariate models: stepwise (BIC), LASSO, elastic net, plus a linear model on the agreed covariates with one cut-off where the data show a step. Machine learning: random forest, XGBoost untuned and tuned; importance by permutation and SHAP. Noise control: a pure-noise covariate, 200 bootstrap resamples for selection stability, agreement across the five methods. Robustness: the split repeated with 20 seeds.

## Folders

```
slides/        the deck, the report, references, the talk outline, the team's kickoff notes and guides
analysis/      the R pipeline (one-file and two-file forms), the sensitivity script, and explorations/
results/       outputs of the main script on the locked split (aggregate tables and figures only)
```

`analysis/explorations/` holds each member's work: `euibeom/` (follow-up checks and the covariate forest plot), `bei/` (correlation screen), `wenzhe/` (two Python + R pipelines and a cross-pipeline comparison), `ming/` (agentic pipeline with pre-registration and a shuffled-outcome null). Patient-level files were removed from all of them before upload.

## Team

Euibeom Shin, Wenzhe Ma, Leo Vuong, Bei Zhao, Ming Gao, Izumi Hamada. Context for teammates and their AI assistants: [`TEAM_CONTEXT.md`](TEAM_CONTEXT.md); rules for AI assistants working in this repository: [`AGENTS.md`](AGENTS.md).

## AI use

Claude (Anthropic) via Claude Code, and Codex, drafted code, documentation and the slides, as noted in the code headers and in `AI_DISCLOSURE.md`. Every analysis decision and interpretation was reviewed by the team, which is accountable for the results. Data are simulated; nothing here describes real patients or approved therapies.
