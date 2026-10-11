# Robustness check: does the method ranking survive a different train/test split?
# Repeats the split and the test-set scoring with 20 seeds, continuous outcome (the primary outcome), all
# three arms. Reports the spread of test R² per method and how often each method ranks first.
# Run:    Rscript sensitivity_splits.R      (from this folder; about 10 to 15 minutes)
# Output: dm1_outputs/sensitivity_splits.csv, dm1_outputs/fig_sensitivity_splits.png
# This is a sensitivity analysis only. The main result stays the single locked split in dm1_analysis.R.
# AI disclosure: drafted with Claude (Anthropic) via Claude Code, after a suggestion from Leo.

suppressPackageStartupMessages({ library(dplyr); library(ggplot2); library(glmnet); library(ranger); library(xgboost) })
OUT <- Sys.getenv("DM1_OUT", "dm1_outputs"); dir.create(OUT, showWarnings = FALSE)
source("R/common.R")
# Reuse the model-fitting code from the main script without running it: evaluate its helper block only.
src <- readLines("dm1_analysis.R")
eval(parse(text = src[grep("^# ---- Helpers ----", src):(grep("^# ---- Per-arm analysis ----", src) - 1)]))

seeds <- 20261011 + 0:19
res <- list()
for (s in seeds) {
  SEED <- s                                   # load_arm() and fit_all() read SEED from the global environment
  for (a in seq_len(nrow(arms))) {
    A <- arms[a, ]; S <- load_arm(A$name, include_test = TRUE); tr <- S$train; te <- S$test
    set.seed(SEED); tr$noise_probe <- rnorm(nrow(tr)); te$noise_probe <- rnorm(nrow(te))
    reg <- fit_all(tr, te, c(S$covs, "noise_probe"), A$outcome, "gaussian")
    r2 <- sapply(reg$pred, function(p) reg_metrics(te[[A$outcome]], p)[["R2"]])
    res[[length(res) + 1]] <- data.frame(seed = s, arm = A$name, method = names(r2), R2 = as.numeric(r2))
    cat(sprintf("seed %d  %-16s %s\n", s, A$name, paste(sprintf("%s %.2f", names(r2), r2), collapse = " | ")))
  }
}
res <- bind_rows(res)
summ <- res |> group_by(arm, method) |>
  summarise(median_R2 = median(R2), q10 = quantile(R2, 0.1), q90 = quantile(R2, 0.9), .groups = "drop")
first <- res |> group_by(arm, seed) |> slice_max(R2, n = 1, with_ties = FALSE) |> count(arm, method, name = "times_ranked_first")
summ <- left_join(summ, first, by = c("arm", "method")) |> mutate(times_ranked_first = coalesce(times_ranked_first, 0L)) |>
  arrange(arm, desc(median_R2))
write.csv(res, file.path(OUT, "sensitivity_splits_all.csv"), row.names = FALSE)
write.csv(summ, file.path(OUT, "sensitivity_splits.csv"), row.names = FALSE)
cat("\nTest R² over", length(seeds), "splits (median, 10th to 90th percentile) and how often each method ranked first:\n")
print(mutate(as.data.frame(summ), across(where(is.numeric), ~ round(.x, 2))), row.names = FALSE)
ggsave(file.path(OUT, "fig_sensitivity_splits.png"),
  ggplot(res, aes(R2, method)) + geom_boxplot(outlier.size = 0.8) + facet_wrap(~arm) + geom_vline(xintercept = 0) +
    labs(x = sprintf("Test-set R² across %d different train/test splits", length(seeds)), y = NULL,
         title = "Does the method ranking depend on which patients landed in the test set?"), width = 11, height = 4.5, dpi = 150)
cat("Done.\n")
