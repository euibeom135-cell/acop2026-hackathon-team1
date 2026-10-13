# Split-sensitivity verdict

- Across 20 seeds, the median per-method SD of test R² is **0.131** — rankings inside this band are ties.
  - Mexiletine: R² SD ranges 0.074–0.260 (widest: Gradient boosting (untuned)).
  - Oligonucleotide: R² SD ranges 0.064–0.176 (widest: OLS all).
  - Tideglusib: R² SD ranges 0.093–0.181 (widest: OLS all).

- Cross-seed selection frequency (covariate stability):
  - Mexiletine: myotonia_severity 85%, disease_duration 75%, insulin_resistance 60%, ctg_repeats 56%, sex 42%
  - Oligonucleotide: ctg_repeats 90%, disease_duration 77%, family_history 65%, somatic_mosaicism_index 57%, myotonia_severity 40%
  - Tideglusib: cognitive_function 100%, disease_duration 93%, cataracts 40%, ctg_repeats 28%, muscle_strength 27%

- Leading R² by scheme (same arm, different split):
  - Mexiletine: fold5 +0.19, single80 -0.01, single75 +0.14
  - Oligonucleotide: fold5 +0.06, single80 +0.01, single75 +0.02
  - Tideglusib: fold5 +0.26, single80 +0.30, single75 +0.35
