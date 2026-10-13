#!/usr/bin/env bash
# 1:3 (25% test) covariate-re-randomised replication of the all-methods analysis. Needs the main project's src/ (feature builder) and R packages MASS leaps glmnet splines mgcv.
# N06 test scoring is guarded (scores the new test set once; FORCE6=1 for a documented re-run).
set -euo pipefail; cd "$(dirname "$0")/.."; PY=.venv/bin/python; S=split_1to3/src
$PY -W ignore $S/n00_split.py; $PY -W ignore $S/s01_export.py
(cd $S && for a in Mexiletine Oligonucleotide Tideglusib; do for t in reg bin; do Rscript r_covariate.R $a $t cv; done; done)
$PY -W ignore $S/s02_ml_cv.py reg; $PY -W ignore $S/s02_ml_cv.py bin
$PY -W ignore $S/s03_pca.py; $PY -W ignore $S/s04_cv_scoreboard.py; $PY -W ignore $S/s05_covariate_comparison.py
if [ "${FORCE6:-0}" = "1" ]; then (cd $S && ../../$PY -W ignore s06_test_scoring.py --force); else (cd $S && ../../$PY -W ignore s06_test_scoring.py); fi
$PY -W ignore $S/s07_summary_tables.py
