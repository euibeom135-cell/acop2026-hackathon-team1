# Purpose: find out why the continuous outcome is poorly predicted in the Oligonucleotide arm.
# Input:   Oligonucleotide training patients, via load_arm(). The test set is not used here.
# Finding: the ctg_repeats effect is real and steady (mean change rises from about 0 in the lowest fifth
#          to about 2.2 in the highest), but patients with the same repeat length still differ a lot:
#          the spread drops only from 1.73 to about 1.5 after accounting for ctg_repeats.
#          No curve, cut-off, second covariate or interaction adds anything reliable (all cross-validated
#          R2 between 0.17 and 0.25), and the random forest is worse (0.15). So this is a weak-signal arm,
#          not a missed pattern. A plain straight line in ctg_repeats is the right model.
source("_helpers.R")
arm <- load_arm("Oligonucleotide"); train <- arm$train; y <- arm$info$outcome

cat("Mean outcome by fifths of ctg_repeats (higher outcome is better):\n")
print(round(tapply(train[[y]], cut(train$ctg_repeats, quantile(train$ctg_repeats, 0:5 / 5), include.lowest = TRUE), mean), 2))
cat("Spread of the outcome:", round(sd(train[[y]]), 2), " after accounting for ctg_repeats:",
    round(sd(resid(lm(train[[y]] ~ train$ctg_repeats))), 2), "\n")

cat("\nCross-validated R2 inside the training set:\n")
for (rhs in c("ctg_repeats", "log(ctg_repeats)", "splines::ns(ctg_repeats, 3)", "I(ctg_repeats >= 350)",
              "ctg_repeats + muscle_strength", "ctg_repeats + disease_duration", "ctg_repeats + myotonia_severity",
              "ctg_repeats + somatic_mosaicism_index", "ctg_repeats * muscle_strength")) line(rhs, cv_r2(train, y, rhs))
line("random forest, all covariates", cv_r2_forest(train, y, arm$covs))
