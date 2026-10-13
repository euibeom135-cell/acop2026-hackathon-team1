#!/usr/bin/env bash
# PDF-faithful six-step DM1 analysis: COMPUTE layer only (no HTML pages). Run from anywhere; it cd's to the main project root. From scratch: results/ is wiped first.
# Needs: .venv python, R packages MASS leaps glmnet splines mgcv (in ~/R-lib), the main project's src/ and results/split_seed42.csv (read-only).
# Test discipline: s05 picks the primary models by TRAIN CV only; s07 is the ONLY step that reads the test rows and writes the guard results/TEST_SCORED.lock (FORCE7=1 only for a documented re-run).
set -euo pipefail; cd "$(dirname "$0")/.."; PY=.venv/bin/python; S=pdf_pipeline/src; R=pdf_pipeline/results
find "$R" -mindepth 1 -delete 2>/dev/null || true; mkdir -p "$R"
par() { local script=$1; shift; local pids=(); for a in Mexiletine Oligonucleotide Tideglusib; do for t in reg bin; do Rscript "$S/$script" $a $t "$@" & pids+=($!); done; done; for p in "${pids[@]}"; do wait "$p"; done; }   # 6 arm x task jobs in parallel; fails if any fails
echo "== S01 export (train features unscaled, folds)";                $PY -W ignore $S/s01_export.py
echo "== Covariate track (R): repeated 5-fold CV, per-fold scaling";  par r_covariate.R cv
echo "== ML track (Python): CV, untuned + tuned";                     $PY -W ignore $S/s02_ml_cv.py reg; $PY -W ignore $S/s02_ml_cv.py bin
echo "== S03 PCA / S04 CV scoreboard / S05 primary selection (CV only)"; $PY -W ignore $S/s03_pca.py; $PY -W ignore $S/s04_cv_scoreboard.py; $PY -W ignore $S/s05_select_primary.py
echo "== Signal vs noise (TRAIN only): R evidence, RF null, verdict";  par r_signal.R; $PY -W ignore $S/s06a_rf_null.py; $PY -W ignore $S/s06_signal_noise.py
echo "== S07 SINGLE test pass (scoreboard + test permutation importance + SHAP)"
if [ "${FORCE7:-0}" = "1" ]; then $PY -W ignore $S/s07_test_scoring.py --force; else $PY -W ignore $S/s07_test_scoring.py; fi
echo "== S08 headline tables";                                        $PY -W ignore $S/s08_headlines.py
echo "== S09 train-only diagnostics (glmnet paths, GAM smooths, tree diagrams)"; par r_diag.R; $PY -W ignore $S/s09_diagnostics.py
echo "== REPORT layer (HTML step pages + summary; read-only on results/)";  $PY -W ignore pdf_pipeline/src/step_reports/build_steps.py
echo "PIPELINE OK"
