# Small helpers shared by the three scripts in this folder. Training patients only.
# AI use: written with Claude (Anthropic) via Claude Code; checked by Euibeom Shin.
root <- normalizePath(getwd()); while (!file.exists(file.path(root, "dm1_analysis.R")) && dirname(root) != root) root <- dirname(root)
setwd(root); suppressMessages(source("R/common.R"))

# Out-of-fold predictions: fit(train_part) returns a model, pred(model, held_out_part) returns numbers.
cv_pred <- function(train, fit, pred) {
  fold <- cv_folds(train); p <- numeric(nrow(train))
  for (k in sort(unique(fold))) p[fold == k] <- pred(fit(train[fold != k, ]), train[fold == k, ])
  p
}
cv_r2 <- function(train, y, rhs) {
  f <- as.formula(paste(y, "~", rhs))
  reg_metrics(train[[y]], cv_pred(train, function(d) lm(f, d), function(m, d) predict(m, d)))[["R2"]]
}
cv_r2_forest <- function(train, y, vars) {
  f <- reformulate(vars, y)
  reg_metrics(train[[y]], cv_pred(train, function(d) ranger::ranger(f, d, num.trees = 500, seed = SEED),
                                  function(m, d) predict(m, d)$predictions))[["R2"]]
}
line <- function(label, value) cat(sprintf("  %-52s %6.2f\n", label, value))
