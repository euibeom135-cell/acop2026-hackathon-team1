# Purpose: find out why machine learning beat the linear models in the Tideglusib arm.
# Input:   Tideglusib training patients, via load_arm(). The test set is not used here.
# Finding: the outcome does not fall gradually with cognitive_function; it steps down at about -0.5.
#          Below the step the mean score is about 8, above it about 3.5. A straight line fits a step badly,
#          trees fit it well. A linear model given a yes/no "cognitive_function below cut-off" does as well
#          as the random forest (cross-validated R2 0.47 vs 0.45; straight line 0.38).
source("_helpers.R")
arm <- load_arm("Tideglusib"); train <- arm$train; y <- arm$info$outcome

cat("Mean outcome by eighths of cognitive_function (higher outcome is better):\n")
print(round(tapply(train[[y]], cut(train$cognitive_function, quantile(train$cognitive_function, 0:8 / 8), include.lowest = TRUE), mean), 1))

# The cut-off is re-chosen inside every fold, so the held-out patients never help to pick it.
best_cut <- function(d) {
  cuts <- quantile(d$cognitive_function, seq(0.2, 0.8, 0.05))
  cuts[[which.min(sapply(cuts, function(k) deviance(lm(d[[y]] ~ I(d$cognitive_function < k)))))]]
}
step_r2 <- function(extra = NULL) {
  p <- cv_pred(train, function(d) { k <- best_cut(d); d$low_cog <- d$cognitive_function < k
                                    list(k = k, m = lm(reformulate(c("low_cog", extra), y), d)) },
               function(f, d) { d$low_cog <- d$cognitive_function < f$k; predict(f$m, d) })
  reg_metrics(train[[y]], p)[["R2"]]
}

cat("\nCross-validated R2 inside the training set:\n")
line("straight line in cognitive_function", cv_r2(train, y, "cognitive_function"))
line("smooth curve (spline, 3 df)", cv_r2(train, y, "splines::ns(cognitive_function, 3)"))
line("step: below cut-off yes/no", step_r2())
line("step + disease_duration", step_r2("disease_duration"))
line("step + disease_duration + muscle_strength", step_r2(c("disease_duration", "muscle_strength")))
line("random forest, all covariates", cv_r2_forest(train, y, arm$covs))
cat("\nCut-off chosen on all training patients:", round(best_cut(train), 2), "\n")
