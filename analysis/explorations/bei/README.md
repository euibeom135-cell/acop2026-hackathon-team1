# bei

Bei's covariate-correlation screening, 11 October 2026 (Python; see `README.txt` for the full method). Added to the repository by Euibeom on Bei's behalf.

What is here: `code/` (analysis and plotting scripts), `figures/` (PNG, PDF and SVG), `results/` (summary tables and JSON), `work/dictionary.json`.

Not here, by the repository rule on patient data: `inputs/` (the dataset and dictionary) and `results/tables/training_data.csv` (patient rows); the `training` block of `results/analysis_results.json` was removed for the same reason. `results/tables/patient_partitions.csv` is kept because it holds only patient ID, arm and split.

Note for the team comparison: this work uses an 80/20 split stratified on the responder label (seed 20261011, scikit-learn). The shared R code uses 75/25 stratified on responder label and onset phenotype with the same seed, so the two training sets are not identical. The leading covariates agree: myotonia severity and CTG repeats (Mexiletine), CTG repeats (Oligonucleotide), cognitive function (Tideglusib).
