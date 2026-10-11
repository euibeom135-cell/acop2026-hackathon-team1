# Purpose: find out why the responder model finds almost no responders in the Mexiletine arm.
# Input:   Mexiletine training patients, via load_arm(). The test set is not used here.
# Finding: (1) The label is a relative rule: responder = myotonia fell by 45% or more of the baseline value.
#              The continuous outcome is the absolute fall, which mostly reflects room to improve:
#              baseline myotonia_severity alone gives cross-validated R2 0.69 and nothing adds to it.
#          (2) Only 29% respond, so predicted probabilities rarely pass 0.5. Using the responder share as
#              the cut-off instead finds most responders, at the price of more false alarms.
#          (3) Responder share climbs with ctg_repeats (7% in the lowest quarter, 57% in the highest) and
#              with myotonia_severity (9% to 50%). The two are 0.88 correlated, so they are one signal.
source("_helpers.R")
arm <- load_arm("Mexiletine"); train <- arm$train; y <- arm$info$outcome

pct <- train[[y]] / train$myotonia_severity                      # relative change; lower is better
cat("Relative change, responders:    ", round(range(pct[train$.resp == 1], na.rm = TRUE), 3), "\n")
cat("Relative change, non-responders:", round(range(pct[train$.resp == 0], na.rm = TRUE), 3), "\n")

quarters <- function(x) cut(x, quantile(x, 0:4 / 4), include.lowest = TRUE)
cat("\nResponder share by quarters of ctg_repeats:\n");       print(round(tapply(train$.resp, quarters(train$ctg_repeats), mean), 2))
cat("Responder share by quarters of myotonia_severity:\n");   print(round(tapply(train$.resp, quarters(train$myotonia_severity), mean), 2))

cat("\nAbsolute change, cross-validated R2 inside the training set:\n")
for (rhs in c("myotonia_severity", "myotonia_severity + ctg_repeats", "myotonia_severity + sex")) line(rhs, cv_r2(train, y, rhs))
line("random forest, all covariates", cv_r2_forest(train, y, arm$covs))

# Responder label: same model, two cut-offs. The second is the training responder share, re-computed in each fold.
p   <- cv_pred(train, function(d) glm(.resp ~ myotonia_severity + ctg_repeats, binomial, d), function(m, d) predict(m, d, type = "response"))
cut <- cv_pred(train, function(d) mean(d$.resp), function(m, d) rep(m, nrow(d)))
show <- function(label, called) cat(sprintf("  %-28s recall %.2f  precision %.2f  accuracy %.2f\n", label,
  sum(called & train$.resp == 1) / sum(train$.resp == 1), sum(called & train$.resp == 1) / max(sum(called), 1), mean(called == (train$.resp == 1))))
cat("\nResponder label, logistic model on myotonia_severity + ctg_repeats (cross-validated, AUC",
    round(auc(train$.resp, p), 2), "):\n")
show("cut-off 0.5", p >= 0.5); show("cut-off = responder share", p >= cut)
