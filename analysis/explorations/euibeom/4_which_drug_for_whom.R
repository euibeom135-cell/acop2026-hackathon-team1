# Purpose: turn three per-arm models into one stratification map: for a given patient, which drug would
#          they most likely respond to? Also checks the data dictionary's statement that arm assignment was
#          "informed by each patient's relative fit across all three arms".
# Input:   training patients of all three arms, via load_arm(). Baseline covariates only are used across
#          arms; no patient's outcome is predicted for an arm they were not in. The test set is not used.
# Finding: see README.
source("_helpers.R")

# One responder model per arm, on that arm's consensus covariates (section 8 of the report).
rule <- list(Mexiletine = ".resp ~ myotonia_severity + ctg_repeats",
             Oligonucleotide = ".resp ~ ctg_repeats",
             Tideglusib = ".resp ~ I(cognitive_function < -0.48)")
fits <- lapply(arms$name, function(nm) glm(as.formula(rule[[nm]]), binomial, load_arm(nm)$train)); names(fits) <- arms$name
pool <- do.call(rbind, lapply(arms$name, function(nm) { d <- load_arm(nm)$train; d$arm <- nm; d }))

# Predicted responder probability for every training patient under each of the three drugs.
P <- sapply(arms$name, function(nm) predict(fits[[nm]], pool, type = "response"))
# The three responder definitions differ (a 45% relative fall vs fixed thresholds), so raw probabilities are not
# comparable between drugs. Compare each patient with that arm's average patient instead: probability / arm responder rate.
base <- sapply(arms$name, function(nm) mean(load_arm(nm)$train$.resp))
R <- sweep(P, 2, base, "/")
pool$best <- arms$name[apply(R, 1, which.max)]
cat("Responder probability relative to the arm average (1 = average patient), all training patients:\n"); print(round(apply(R, 2, quantile, c(.1, .5, .9)), 2))
cat("\nShare of patients for whom each drug is the best bet:\n"); print(round(100 * prop.table(table(pool$best))))
cat("\nActual arm (rows) vs predicted best drug (columns), %:\n"); print(round(100 * prop.table(table(actual = pool$arm, best = pool$best), 1)))
cat("Agreement if assignment were random: about 33%. Observed:", round(100 * mean(pool$arm == pool$best)), "%\n")

# What does the map look like in covariate terms?
cat("\nMedian covariates by predicted best drug:\n")
print(aggregate(cbind(ctg_repeats, myotonia_severity, cognitive_function) ~ best, pool, median))
