# Orchestration log

## Mon 2026-10-12

### Team assembled
`.claude/agents/`: data-steward, split-designer, covariate-modeler, ml-modeler,
stability-auditor, biologist, scoreboard-builder, communicator. Orchestrator
brief in `CLAUDE.md`.

### Environment
- System Python is 3.9.6 with no scientific packages; the Oct 11 analysis ran
  elsewhere (Python 3.12). Created `.venv` (3.9) and installed numpy 1.26,
  pandas 2.2, scipy 1.13, scikit-learn 1.5, statsmodels 0.14, matplotlib.
- **XGBoost could not load** (no OpenMP `libomp.dylib`, no Homebrew to install
  it). Substituted scikit-learn **HistGradientBoosting** for both the untuned and
  tuned gradient-boosting rows — same role (the prediction ceiling, importance,
  non-linearity), fully reproducible, no native dependency. Noted in the report.

### G1 — six data decisions (defaults set; confirm with the team)
1. **Albumin** constant (4.18) in Mexiletine → dropped for that arm only.
2. **Age collinearity**: `disease_duration = age − age_at_onset` exactly →
   dropped `age` (the derived sum); kept `age_at_onset` and `disease_duration`.
3. **Collinear severity axis** (ctg_repeats ↔ myotonia_severity, strongly
   correlated): kept both; stability selection and the agreement matrix decide
   which dominates rather than dropping one a priori.
4. **Mexiletine target**: continuous = *relative* myotonia change
   (`−change/baseline`). Verified the 0.45 cutoff reproduces the responder label
   exactly (TP=47, FP=0, FN=0). Baseline myotonia=0 (1 patient, DM1_0095, in the
   locked test) → relative=0.
5. **Locked partition**: fold 1 = the Oct 11 test set (33/34/34 = 101),
   hash `8b3fb2cb33c48f168d0b0e582b7c84f11ffaf661456a1bf51966f9ae20096924`
   recorded in `outputs/splits/summary.json` for the G3 check. Folds 2–5 =
   stratified quarters of the Oct 11 training set (seed 2026).
6. **family_history / cataracts**: family_history kept 3-level (No/Unknown/Yes),
   Unknown as its own level (not imputed); cataracts binary. Categoricals are
   permuted and selected as blocks.

### Rehearsal run (fold 5 pseudo-test; fold 1 untouched)
- `02_make_splits` → folds locked, hash recorded.
- `03_run_models --scheme fold5 --task both` → scoreboards + selection records.
  Headline (rehearsal): continuous best R² — Mex 0.19 (SVM), Oligo 0.06
  (stepwise BIC), Tideglusib 0.26 (random forest); binary best AUC — Mex 0.77,
  Oligo 0.76, Tideglusib 0.70. Bootstrap CIs are wide (≈±0.2 R²), so within-band
  rankings are reported as ties.
- `05_stability`, `03` single80/single75/repeat20, `06_compare_splits`,
  `08_compact_and_stratify`, `07_build_report`: **complete**.
- `tabulate` added to the venv (pandas `.to_markdown` needs it for
  `slide_tables.md`); `requirements.txt` frozen.

### Rehearsal results (fold 5 pseudo-test) — for G2 review
- **Real signal** (stable AND beats RF null): Tideglusib — cognition (both
  tasks); Oligonucleotide — ctg_repeats, insulin_resistance (continuous),
  disease_duration + ctg_repeats (binary); Mexiletine — none (severity trio is
  stable-but-suggestive on the relative target).
  - **Cross-seed override:** Oligo `insulin_resistance` (continuous) is
    **downgraded, not claimed** — it met the fold-5 bar but holds in only 17% of
    cross-seed splits, is non-consensus (0.42 < 0.5), and washes out under FDR
    (q = 0.075). Claimed Oligo/continuous real signal is `ctg_repeats` only
    (`docs/interpretation_Oligonucleotide.md` §4; slide_tables.md annotation).
- **Split sensitivity**: median per-method test-R² SD = **0.131** across 20
  seeds → within-band rankings are ties. Covariate selection is stable across
  seeds (Tideglusib cognition 100%, Oligo ctg_repeats 90%, Mex myotonia 85%).
  Headline sentence holds: *the split moves the scores, not the covariates.*
- **Stratification (the innovation arc)**: Tideglusib `1[cognition ≤ −0.505]`
  lifts single-term test R² from +0.233 (linear) to +0.377 (indicator), enriching
  mean composite improvement to 8.28 vs 3.46 — a one-term rule recovers the
  forest's non-linearity. Oligo/Mex thresholds reported but do not generalize
  out-of-sample (reported honestly).
- Interpretation docs (biologist, delegated subagents) **complete**:
  `docs/interpretation_{Mexiletine,Oligonucleotide,Tideglusib}.md`. Each cites
  its source files; honest caveats baked in (Mex severity trio "suggestive" on
  the relative target; Oligo CTG direction flipped vs prior → flagged for the
  locked run; Oligo/Mex stratifiers not adopted out-of-sample).
- Deck/script/Q&A (communicator, delegated subagent): in progress → `docs/`.

### Gate status (end of Mon rehearsal)
- **G1** defaults set and documented above — team to confirm.
- **G2** rehearsal accepted basis is ready to freeze: `config.py` holds all
  decisions; results reproduce via `bash run_all.sh rehearsal`.
- **G3/G4** not started (Tue): final run is one command and will only refresh
  numbers; fold-1 hash `8b3fb2cb…` to be confirmed first.

### Compute reductions (rehearsal only; restored at final)
- Inner CV repeats 2 (final: 3); bootstrap 1000; stability subsamples 100; null
  permutations 50; repeat20 restricted to continuous + cheap methods. All in
  `config.py`.

### Gates
- G1: defaults set above — **confirm Mon AM**.
- G2: freeze `config.py` after accepting rehearsal — **pending (Mon evening)**.
- G3: flip to final, run once, confirm fold-1 hash — **not started (Tue AM)**.
- G4: slides, timed read-through — **not started (Tue PM)**.
