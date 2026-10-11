# ACoP 2026 Hackathon — Team 1

"Beyond CTG Repeats: Advancing Patient Stratification in Myotonic Dystrophy Type 1"

**Task:** for each of three treatment arms in a simulated 500-patient dataset, find which baseline covariates drive response, separate real predictors from planted noise, and compare covariate models with machine-learning models.

**Due:** slides and code in the Team 1 SharePoint folder by **Tue 13 Oct, 11:59 PM ET**. Talk: Wed 14 Oct, 9:00 AM (5 min + 3 min Q&A).

## Folders, in the order you need them

| Folder | What's inside | Touch it? |
|---|---|---|
| `1_kickoff/` | The organizers' kickoff slide deck (90 slides) | Read |
| `2_team_docs/` | Three-page brief and ten-page detailed guide, both PDF, for sharing with the team | Share |
| `3_analysis/` | `dm1_analysis.R`, the whole analysis in one script. Put the dataset in `3_analysis/data/`. Results appear in `3_analysis/dm1_outputs/` | **Work here** |
| `4_slides/` | `slide_outline.md`: five-slide outline mapped to the scoring. The deck goes here | Work here |
| `5_reference/` | Background notes written before kickoff: DM1 science brief, Certara and nlmixr2lib model catalogues | Reference |
| `archive_before_kickoff/` | The longitudinal `nlmixr2` pipeline, overnight loop and practice data built before the real task was known. Not part of the submission | Leave |

In the shared GitHub repository only `2_team_docs/`, `3_analysis/` and `4_slides/` are present. The kickoff deck, reference notes, archive and the dataset itself are kept off GitHub; get the deck and dataset from the team SharePoint folder.

## Run the analysis

1. Save the dataset (any file name containing `DM1`, `.xlsx` or `.csv`) into `3_analysis/data/`.
2. Run:

```bash
cd 3_analysis && Rscript dm1_analysis.R
```

3. Read the data checks printed at the top, then the per-arm covariate calls and scoreboards. Figures and tables are in `3_analysis/dm1_outputs/`.

The script has only been run on mock data with the kickoff's column names. The arm and label column names are taken from the slides and may need a small edit once the real file arrives.

## What goes to SharePoint

- The slide deck from `4_slides/`.
- `3_analysis/dm1_analysis.R` and the `dm1_outputs/` it produced.
- AI disclosure: Claude (Anthropic) via Claude Code for code drafting and workflow design. Add InsightRX Astra if it is used for a cross-check.
