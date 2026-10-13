# ming

Ming Gao's agentic pipeline (Python; built on Bei's 11 October data-steward scripts and Bei's 80/20 split), added by Euibeom on Ming's behalf. Read `docs/submission_manifest.md` first, then `docs/LOG.md` and `outputs/report/slide_tables.md`.

What it does: 14 methods per endpoint (8 covariate models, 6 ML), both endpoints, three arms, scored on the same held-out rows with bootstrap intervals; stability selection plus a shuffled-outcome random-forest null as the signal-vs-noise rule; 20-seed split sensitivity; compact models and stratification rules; a 7-slide HTML deck, script and Q&A. Status when added: **rehearsal mode** (fold 5 as a pseudo-test; the locked fold 1, which is Bei's original test set, had not been opened).

Two definitions differ from the shared R pipeline and matter when comparing numbers: the mexiletine continuous target is *relative* change (change divided by baseline myotonia), not the dataset's absolute change column; and `age` is dropped in favour of onset age plus duration.

Not included, by the repository rule on patient data: `inputs/` (the dataset), `results/tables/training_data.csv`, `results/analysis_results.json` (contains training rows), and the virtual environment. Fold and split listings (patient ID and fold only) are kept.
