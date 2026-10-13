#!/usr/bin/env bash
# Orchestrated pipeline. Usage: bash run_all.sh [rehearsal|final]
# rehearsal (default): train folds 2-4, score fold 5; never opens fold 1.
# final: train folds 2-5, score the locked fold 1 (G3 — run once).
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-rehearsal}"
PY="${PY:-.venv/bin/python}"
export DM1_MODE="$MODE"
echo "=== DM1 pipeline — MODE=$MODE ==="

echo "--- 02 splits";               "$PY" 02_make_splits.py
echo "--- 03 headline (fold5)";     "$PY" 03_run_models.py --task both --scheme fold5 --mode "$MODE"
echo "--- 05 stability";            "$PY" 05_stability.py  --task both --mode "$MODE"

if [ "$MODE" = "rehearsal" ]; then
  echo "--- 03 sensitivity: single80/single75";
  "$PY" 03_run_models.py --task continuous --scheme single80 --mode "$MODE"
  "$PY" 03_run_models.py --task continuous --scheme single75 --mode "$MODE"
  echo "--- 03 sensitivity: repeat20 (continuous, cheap methods, background-friendly)";
  "$PY" 03_run_models.py --task continuous --scheme repeat20 --mode "$MODE"
  echo "--- 06 compare splits";     "$PY" 06_compare_splits.py
fi

echo "--- 08 compact + stratify";   "$PY" 08_compact_and_stratify.py --task both --mode "$MODE"
echo "--- 07 build report";         "$PY" 07_build_report.py
echo "=== done ($MODE). report: outputs/report/results_report.html ==="
