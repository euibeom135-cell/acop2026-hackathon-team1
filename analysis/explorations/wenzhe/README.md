# wenzhe

Wenzhe Ma's pipelines (Python for ML, R for covariate models), added by Euibeom on Wenzhe's behalf. Their own notes are inside each folder.

| Folder | What it is |
|---|---|
| `pdf_pipeline/` | The "PDF-faithful" six-step analysis: genuine 80/20 split (seed 42), every method in the kickoff deck, one pre-stated signal-vs-noise rule, primary models chosen by cross-validation, test set scored once. Start with `reports/summary.html` and `notes/compute_notes.html`. |
| `split_1to3/` | Earlier 75/25 re-randomised replication with 30 methods and a 20-seed sensitivity run. Start with `reports/summary_clean.html`. |
| `comparison_vs_onefile.html` | Wenzhe's comparison of Leo's R zip, Euibeom's one-file script and their own pipeline: same lead covariates in every arm. |

Not included, by the repository rule on patient data: feature tables, training-row exports, split listings and any file carrying observed outcomes per row (`obs` columns). Fold assignments and prediction files (row index and prediction only) are kept. Both pipelines need the dataset in place and their own environment (`.venv`, R packages) to re-run.
