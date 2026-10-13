# ACoP 2026 Hackathon — Team 1

Repository: https://github.com/euibeom135-cell/acop2026-hackathon-team1


**Beyond CTG Repeats: Advancing Patient Stratification in Myotonic Dystrophy Type 1 (DM1)**

> **The question:** can machine learning identify additional predictors and improve patient stratification beyond traditional covariate modelling?

For each of three treatment arms in a simulated 500-patient dataset, we find which baseline covariates drive response, separate real predictors from planted noise, and compare covariate models with machine-learning models.

| | |
|---|---|
| **Submission** | Slides and all code in the Team 1 SharePoint folder by **Tue 13 Oct 2026, 11:59 PM ET** |
| **Presentation** | Wed 14 Oct, 9:00 AM. 5-minute talk + 3-minute Q&A (one judge question) |
| **Scoring** | Clinical 10, Technical 10, Communication 10 |
| **Office hour** | Tue 13 Oct, 8:00 to 9:00 AM, Magnolia 1 |

**New here? Read [`GETTING_STARTED.md`](GETTING_STARTED.md).** Everyone on the team has write access.

## Folders

| Folder | What's inside |
|---|---|
| [`slides/`](slides/) | The original kickoff deck, our 3-page brief, our 10-page detailed guide, and the outline for our talk |
| [`analysis/`](analysis/) | The analysis script, the shared data-loading and split code, and one folder per member for trying ideas |
| [`results/`](results/) | The team's official tables and figures, which the slides are built from |

```
├── slides/
│   ├── 1_kickoff_slides_original.pdf
│   ├── 2_brief.pdf
│   ├── 3_detailed_guide.pdf
│   └── presentation_outline.md
├── analysis/
│   ├── dm1_analysis.R       main pipeline; the only place the test set is used
│   ├── R/common.R           shared data loading, cleaning and the one train/test split
│   ├── explorations/        one folder per member (training data only)
│   ├── data/                put the dataset here (never uploaded)
│   └── dm1_outputs/         your own run's output (not uploaded)
├── results/                 official team results, one shared copy
├── GETTING_STARTED.md       setup, sharing and troubleshooting
├── sync.sh                  one command to save, pull and upload
├── DECISIONS.md             analysis decisions and their reasons
├── AI_DISCLOSURE.md         which AI tools were used, and for what
├── CONTRIBUTING.md          how to share changes
└── AGENTS.md / CLAUDE.md    rules for Codex and Claude Code
```

## Quick start

1. Get the dataset from the team SharePoint folder and save it into `analysis/data/`.
2. Install packages once: `Rscript analysis/install_packages.R`
3. Run:

```bash
cd analysis && Rscript dm1_analysis.R
```

Your results appear in `analysis/dm1_outputs/` (personal, not uploaded). The team's official copy is in `results/`. See [`analysis/README.md`](analysis/README.md) for what each file means.

To share work: `bash sync.sh "what I changed"`.

## Working with AI assistants

Several of us use Codex or Claude Code. Both pick up the project rules automatically from `AGENTS.md` / `CLAUDE.md` when started inside this folder. The rules that matter most: the dataset is never uploaded, explorations see training patients only, nobody changes the split or the seed, and every AI tool used is logged in `AI_DISCLOSURE.md`. Each person works in their own folder under `analysis/explorations/`.

## Workflow

| Step | What the script does |
|---|---|
| 1. Understand | Data checks, correlated covariates, responder balance |
| 2. Split | Per arm, 75/25, stratified by responder label and onset phenotype, fixed seed, test set locked |
| 3. Preprocess | Category encoding; scaling and imputation learned on the training set only |
| 4. Select | Covariate models (stepwise, LASSO, elastic net) and ML (random forest, XGBoost) |
| 5. Train | Tuning by 5-fold cross-validation inside the training set |
| 6. Evaluate | Once on the test set, with bootstrap intervals; covariates compared across methods |

## Task board

- [ ] Dataset received and placed in `analysis/data/`
- [ ] Data checks reviewed; cleaning decisions recorded in `DECISIONS.md`
- [ ] Analysis run on real data; outputs shared
- [ ] Clinical sense-check of selected covariates per arm
- [ ] Team call: agree the story
- [ ] Slides drafted (five slides)
- [ ] AI disclosure final in code and slides
- [ ] Slides and code uploaded to SharePoint; representative emails the chairs

## Team and roles

| Role | Who |
|---|---|
| Analysis and code | Euibeom Shin |
| Clinical sense-check | to be agreed |
| Slides | to be agreed |
| Presenter and team representative | to be agreed |

## Status

The script has been tested end to end on mock data built with the kickoff's column names. It has **not yet been run on the real dataset**.
