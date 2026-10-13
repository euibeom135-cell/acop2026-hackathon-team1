# DM1 covariate analysis — orchestrator brief

This repository runs the six-step pipeline from *DM1 Hackathon: Agentic Workflow
and Orchestration Plan.md*: understand → split → preprocess → select → train →
evaluate, per treatment arm (Mexiletine, Oligonucleotide, Tideglusib).

## The one rule that protects the deadline
`fold 1` is the **locked test set** (the Oct 11 partition, 33/34/34 = 101
patients). It is scored **once**, at the final run (gate G3). Everything else —
tuning, stepwise, cutoffs, stability, interpretation, slide drafts — is built in
**rehearsal mode**, which trains on folds 2–4 and scores fold 5 as a pseudo-test.
Rehearsal never opens fold 1. At G3 one person flips `MODE='final'` in
`config.py` (or `DM1_MODE=final`), runs `bash run_all.sh final` once, and
confirms the fold-1 hash against `outputs/splits/summary.json`.

## How to run
```
bash run_all.sh rehearsal     # Monday: full pipeline on the pseudo-test
bash run_all.sh final         # Tuesday G3: locked test, once
```
Python is `.venv/bin/python` (3.9; numpy/pandas/scipy/sklearn/statsmodels/
matplotlib). Scripts self-insert the repo root, so `-I` is safe. Every stage is
restartable at the script boundary; nothing downstream needs more than the CSVs.

## Pipeline stages (DAG)
`02_make_splits` → `03_run_models` (continuous, then binary) → `05_stability` →
`06_compare_splits` → `08_compact_and_stratify` → `07_build_report`.
One runner does the compute; the agents split the *reading*, not the compute.

## The team (`.claude/agents/*.md`)
data-steward · split-designer · covariate-modeler · ml-modeler ·
stability-auditor · biologist · scoreboard-builder · communicator.
The orchestrator (this session) delegates, holds the human gates, and keeps
`docs/LOG.md`. A human owns each role as that agent's reviewer.

## Gates (human decisions, in order)
- **G1** — ratify the six data decisions (see `docs/LOG.md`). Confirm Mon AM.
- **G2** — accept rehearsal results; freeze `config.py`. Mon evening.
- **G3** — flip to final; run once; confirm fold-1 hash. Tue morning.
- **G4** — slides: assertion titles, numbers traced to `slide_tables.md`,
  timed read-through under 5:00. Tue evening.

## Conventions (frozen in `config.py`)
- Oriented so higher `improvement_score` = more improvement in every arm.
- Mexiletine continuous target is **relative** myotonia change (−change/baseline);
  its 0.45 cutoff reproduces the responder label exactly.
- `age` dropped (= age_at_onset + disease_duration); `albumin` dropped for
  mexiletine (constant). Categoricals permuted as blocks.
- Gradient boosting = scikit-learn HistGradientBoosting (XGBoost's role; no
  OpenMP runtime here). Documented in the report and `docs/LOG.md`.

## Outputs the judges asked for
`outputs/runs/<task>/<scheme>/<arm>/scoreboard.csv` (+ bootstrap CIs),
`consensus.csv`, `agreement.csv`, `compact_scoreboard.csv`,
`outputs/stability/.../stability.csv` (verdicts),
`outputs/compare/` (split sensitivity), `outputs/stratify/<arm>/rule.txt`,
`outputs/report/results_report.html` + `slide_tables.md`,
`docs/interpretation_<arm>.md`, the deck, script and Q&A.
