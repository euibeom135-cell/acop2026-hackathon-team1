# DM1 submission manifest

What goes in the submission, where it lives, and which agent owns it.
Status reflects the **rehearsal** run (Mon Oct 12). The final run (G3) only
replaces numbers; file layout is unchanged.

## Code (reproducible)
- `config.py` — frozen decisions and compute knobs (the G2 freeze point).
- `pipeline/` — `data.py` (load/orient/folds/transform), `models.py` (14+14
  methods, one interface), `metrics.py` (scoring, bootstrap, OOF cutoff,
  grouped permutation).
- `02_make_splits.py` · `03_run_models.py` · `05_stability.py` ·
  `06_compare_splits.py` · `08_compact_and_stratify.py` · `07_build_report.py`.
- `run_all.sh` — `bash run_all.sh rehearsal|final`.
- `requirements.txt` — exact package versions (`.venv`, Python 3.9).
- `code/` — the Oct 11 data-steward scripts (`analyze_dm1.py`, `plot_dm1.py`).

## The split
- `data/folds_5fold_seed2026.csv` — the locked partition.
- `outputs/splits/summary.json` — per-fold counts + **fold1_sha256** (G3 check).

## Results (judges' asks)
- `outputs/runs/<task>/<scheme>/<arm>/scoreboard.csv` — all methods, same test
  rows, bootstrap CIs on the fold5 headline; untuned + tuned rows.
- `outputs/runs/<task>/fold5/<arm>/consensus.csv`, `agreement.csv`,
  `compact_scoreboard.csv` — covariate agreement and compact models.
- `outputs/stability/<task>/<arm>/stability.csv` — real-signal verdicts.
- `outputs/compare/{repeat20_r2.csv, selection_frequency.csv, r2_by_scheme.csv,
  verdict.md}` — split sensitivity.
- `outputs/stratify/<arm>/{rule.txt, partial_dependence.csv}` — enrichment rules.
- `outputs/report/results_report.html` + `slide_tables.md` + `figures/` — report.

## Narrative
- `docs/hypothesis_sheet.md` — pre-registration (dated, before the locked run).
- `docs/interpretation_{Mexiletine,Oligonucleotide,Tideglusib}.md` — biologist.
- `docs/data_report.html` *(to regenerate from `code/plot_dm1.py` if required)*.
- `docs/deck.md`, `docs/script.md`, `docs/qa.md` — communicator (gate G4).
- `docs/presentation.html` — the **built deck** (self-contained, embedded figures;
  **F** fullscreen · **N** speaker notes · Cmd/Ctrl-P → PDF), with
  `docs/presentation.pdf` (one slide per page) and
  `docs/presenter_checklist.md` (pre-talk checklist + top-3 Q&A).
- `docs/LOG.md` — decisions, gates, deviations.
- `CLAUDE.md` — orchestrator brief; `.claude/agents/*.md` — the team.

## One-command reproduction
```
python -m venv .venv && .venv/bin/pip install -r requirements.txt
bash run_all.sh rehearsal      # Monday pipeline (fold 5 pseudo-test)
# at G3, a custodian runs once, after confirming the fold-1 hash:
bash run_all.sh final
```
