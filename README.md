# ACoP 2026 Hackathon — Team 1

**Beyond CTG Repeats: Advancing Patient Stratification in Myotonic Dystrophy Type 1 (DM1)**

> **The question:** can machine learning identify additional predictors and improve patient stratification beyond traditional covariate modelling?

For each of three treatment arms in a simulated 500-patient dataset, we find which baseline covariates drive response, separate real predictors from planted noise, and compare covariate models with machine-learning models.

| | |
|---|---|
| **Submission** | Slides and all code in the Team 1 SharePoint folder by **Tue 13 Oct 2026, 11:59 PM ET** |
| **Presentation** | Wed 14 Oct, 9:00 AM. 5-minute talk + 3-minute Q&A (one judge question) |
| **Scoring** | Clinical 10, Technical 10, Communication 10 |
| **Office hour** | Tue 13 Oct, 8:00 to 9:00 AM, Magnolia 1 |

## Start here

| If you want to... | Go to |
|---|---|
| Understand the task in 3 pages | [`2_team_docs/Team1_hackathon_brief.pdf`](2_team_docs/Team1_hackathon_brief.pdf) |
| Read the full background and method notes | [`2_team_docs/Team1_hackathon_detailed_guide.pdf`](2_team_docs/Team1_hackathon_detailed_guide.pdf) |
| Run the analysis | [`3_analysis/`](3_analysis/) |
| See or record a team decision | [`DECISIONS.md`](DECISIONS.md) |
| Work on the slides | [`4_slides/`](4_slides/) |
| Know how to share a change | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Check what we must disclose about AI | [`AI_DISCLOSURE.md`](AI_DISCLOSURE.md) |

## Repository layout

```
├── README.md              this page
├── DECISIONS.md           log of analysis decisions and their reasons
├── AI_DISCLOSURE.md       which AI tools were used, and for what
├── CONTRIBUTING.md        how to share changes; what must not be uploaded
├── 2_team_docs/           brief and detailed guide (PDF)
├── 3_analysis/
│   ├── README.md          how to run, what each output means
│   ├── dm1_analysis.R     the whole analysis in one script
│   ├── install_packages.R one-off package install
│   ├── data/              put the dataset here (never uploaded)
│   └── dm1_outputs/       tables and figures, created by the script
└── 4_slides/
    └── slide_outline.md   five-slide outline mapped to the scoring
```

Folder numbers follow the team's local working copy, where `1_kickoff/` (organizers' deck) and `5_reference/` are kept off GitHub.

## Quick start

1. Get the dataset from the team SharePoint folder and save it into `3_analysis/data/`.
2. Install packages once: `Rscript 3_analysis/install_packages.R`
3. Run:

```bash
cd 3_analysis && Rscript dm1_analysis.R
```

Results appear in `3_analysis/dm1_outputs/`. See [`3_analysis/README.md`](3_analysis/README.md) for what each file means.

## Workflow

The script follows the six steps from the kickoff session.

| Step | What the script does |
|---|---|
| 1. Understand | Data checks, correlated covariates, responder balance (training data only after the split) |
| 2. Split | Per arm, 75/25, stratified by responder label and onset phenotype, fixed seed, test set locked |
| 3. Preprocess | Category encoding; scaling and imputation learned on the training set only |
| 4. Select | Covariate models (stepwise, LASSO, elastic net) and ML (random forest, XGBoost) |
| 5. Train | Tuning by 5-fold cross-validation inside the training set |
| 6. Evaluate | Once on the test set, with bootstrap intervals; covariates compared across methods |

## Task board

- [ ] Dataset received and placed in `3_analysis/data/`
- [ ] Data checks reviewed; cleaning decisions recorded in `DECISIONS.md` and in the script
- [ ] Analysis run on real data; outputs shared
- [ ] Clinical sense-check of selected covariates per arm
- [ ] Team call: agree the story
- [ ] Slides drafted (five slides)
- [ ] Slides reviewed after Tuesday office hour
- [ ] AI disclosure final in code and slides
- [ ] Slides and code uploaded to SharePoint; representative emails the chairs
- [ ] Presenter rehearsed with the likely judge questions

## Team and roles

| Role | Who |
|---|---|
| Analysis and code | Euibeom Shin |
| Clinical sense-check | to be agreed |
| Slides | to be agreed |
| Presenter | to be agreed |
| Team representative (emails the chairs) | to be agreed |

Team 1: Euibeom Shin, Luong Vuong, Vijay Ivaturi, Ming Gao, Wenzhe Ma, Bei Zhao.

## Status

The script has been tested end to end on mock data built with the kickoff's column names. It has **not yet been run on the real dataset**; column names for the arm and responder labels are taken from the slides and may need a small edit.
