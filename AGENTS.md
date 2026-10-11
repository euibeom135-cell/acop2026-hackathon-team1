# Instructions for AI coding assistants (Codex, Claude Code, and others)

This file is read automatically by Codex. Claude Code reads `CLAUDE.md`, which points here. Team members: you can also paste this file into any chatbot before asking for help.

## What this project is

ACoP 2026 Hackathon, Team 1. A simulated trial of 500 DM1 patients, one row per patient, three treatment arms (Mexiletine, Oligonucleotide, Tideglusib). Each arm has its own continuous outcome and a responder label, plus 18 baseline covariates, some of which are deliberate noise. Goal: identify which covariates drive response in each arm, and compare covariate models with machine-learning models. Scoring: clinical 10, technical 10, communication 10. "Meaningful covariate identification matters more than fancy models."

Deadline: slides and code due Tue 13 Oct 2026, 11:59 PM ET. Favour simple, explainable work over new machinery.

## Hard rules

1. **Never commit the dataset** or copy its rows into any file, chat or commit message. It lives only in `analysis/data/`, which git ignores.
2. **The test set is locked.** In an exploration, get data only with `load_arm("<arm>")`, which returns training patients. Never call `load_arm(..., include_test = TRUE)`, never read the data file directly, and never reimplement the split. Compare ideas with cross-validation inside the training set (`cv_folds()`).
3. **Do not change the seed, the split, or `analysis/R/common.R`** unless the user tells you the team has agreed. Everyone's results depend on them being identical.
4. **Do not edit `analysis/dm1_analysis.R` for an experiment.** Work in the user's own folder under `analysis/explorations/<name>/`. A finding moves into the main script only after the team agrees.
5. **Decide data cleaning from baseline columns and plausibility, never from the outcome.**
6. **Log it.** Any change to methods, thresholds or cleaning gets a row in `DECISIONS.md`. Any AI tool used gets a row in `AI_DISCLOSURE.md`.
7. **Report results as they are.** A null result is a result. With about 40 test patients per arm, do not rank methods on small differences. State which direction is better: Mexiletine lower, the other two higher.
8. **The team must understand every step.** Explain what code does in plain terms, and prefer methods taught at kickoff: linear/logistic regression, stepwise, best subset, LASSO, ridge, elastic net, splines, GAM, decision tree, random forest, XGBoost, permutation importance, SHAP.

## Layout

```
analysis/
  dm1_analysis.R        main pipeline, all three arms; the only place the test set is used
  R/common.R            data loading, cleaning, the split, small helpers (shared; do not copy)
  explorations/
    _template.R         starting point for a new exploration
    <name>/             one folder per team member; work here
  data/                 dataset goes here locally (ignored by git)
  dm1_outputs/          created by the main script
slides/                 kickoff deck, brief, detailed guide (PDF), presentation outline and deck
DECISIONS.md            analysis decisions and reasons
AI_DISCLOSURE.md        AI tools used and for what
```

## Commands

```bash
Rscript analysis/install_packages.R                 # once
cd analysis && Rscript dm1_analysis.R               # full analysis, about a minute
cd analysis/explorations/<name> && Rscript my_idea.R
```

There is no test suite. To check a change to the main script, run it and confirm it prints `Done.`

## Starting an exploration

Copy `analysis/explorations/_template.R` into the user's folder. It loads the shared code and one arm's training data:

```r
root <- normalizePath(getwd()); while (!file.exists(file.path(root, "dm1_analysis.R")) && dirname(root) != root) root <- dirname(root)
setwd(root); source("R/common.R")
arm <- load_arm("Oligonucleotide"); train <- arm$train
```

Available after sourcing: `covs`, `num_cov`, `cat_cov`, `arms` (name, outcome, label, better), `load_arm()`, `cv_folds()`, `reg_metrics()`, `cls_metrics()`, `auc()`, `SEED`. In `train`, `.resp` is the 0/1 responder label.

## Conventions

- R is the team's main language. Python is fine inside an exploration folder if the user prefers it; keep its data access to an export of training rows written locally (never committed).
- Write small scripts with a three-line header: purpose, input, finding.
- Before pushing: `git pull`, then commit only files in the user's own exploration folder, `slides/`, or the log files. Changes to shared files need the team's agreement first.
- Commit messages: what changed and why, one line.
