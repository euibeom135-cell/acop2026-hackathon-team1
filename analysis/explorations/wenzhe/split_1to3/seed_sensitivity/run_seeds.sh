#!/usr/bin/env bash
# 20-seed sensitivity: repeats the 1:3 covariate-re-randomised split + all methods for master seeds 101..120 (3 seeds in parallel; ~1 min per seed).
cd "$(dirname "$0")/../.."; PY=.venv/bin/python
seq ${SEEDS:-101 120} | tail -n +1 >/dev/null
for s in $(seq 101 120); do echo $s; done | xargs -P 3 -I{} sh -c "$PY -W ignore split_1to3/seed_sensitivity/src/seed_run.py {} > split_1to3/seed_sensitivity/results/log_{}.txt 2>&1"
echo ALLDONE > split_1to3/seed_sensitivity/results/ALLDONE
