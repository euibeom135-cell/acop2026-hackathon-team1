# Purpose: present the per-arm covariate findings the way a pharmacometric report does: a reference patient,
#          covariate scenarios (key covariate at its 10th and 90th percentile; each onset phenotype), the
#          predicted responder probability under each scenario with a 90% bootstrap interval, as a forest plot.
#          Also: does the key covariate hold inside each onset phenotype (slope per phenotype, interaction test)?
# Input:   training patients of each arm, via load_arm(). The test set is not used.
# Finding: see README.
here <- getwd(); source("_helpers.R"); suppressMessages(library(ggplot2))   # _helpers.R moves to the analysis root; outputs go back here
key   <- c(Mexiletine = "myotonia_severity", Oligonucleotide = "ctg_repeats", Tideglusib = "cognitive_function")
extra <- list(Mexiletine = "ctg_repeats", Oligonucleotide = character(0), Tideglusib = character(0))
B <- 500; out <- list(); slopes <- list()

for (nm in arms$name) {
  arm <- load_arm(nm); tr <- arm$train; k <- key[[nm]]; y <- arm$info$outcome
  rhs <- c(k, extra[[nm]], "phenotype")
  f_cls <- reformulate(rhs, ".resp")
  # Reference patient: median of each numeric covariate, adult onset.
  ref <- tr[1, rhs, drop = FALSE]
  for (v in intersect(rhs, num_cov)) ref[[v]] <- median(tr[[v]])
  ref$phenotype <- factor("adult_onset", levels = levels(tr$phenotype))
  q <- quantile(tr[[k]], c(0.1, 0.9))
  scen <- list(`Reference patient (median, adult onset)` = ref)
  s <- ref; s[[k]] <- q[[1]]; scen[[sprintf("%s at 10th percentile (%.2g)", k, q[[1]])]] <- s
  s <- ref; s[[k]] <- q[[2]]; scen[[sprintf("%s at 90th percentile (%.2g)", k, q[[2]])]] <- s
  for (ph in c("juvenile_onset", "late_onset")) { s <- ref; s$phenotype <- factor(ph, levels = levels(tr$phenotype)); scen[[paste(ph, "(other covariates at reference)")]] <- s }
  S <- do.call(rbind, scen)
  pred <- function(d) predict(glm(f_cls, binomial, d), S, type = "response")
  est <- pred(tr); set.seed(SEED)
  bs <- replicate(B, { i <- sample(nrow(tr), replace = TRUE); tryCatch(pred(tr[i, ]), error = function(e) rep(NA, nrow(S))) })
  out[[nm]] <- data.frame(arm = nm, scenario = names(scen), responder_prob = est,
                          lo90 = apply(bs, 1, quantile, 0.05, na.rm = TRUE), hi90 = apply(bs, 1, quantile, 0.95, na.rm = TRUE), row.names = NULL)
  # Does the key covariate hold within each phenotype? Slope of the continuous outcome per phenotype, and the interaction test.
  m1 <- lm(reformulate(c(k, "phenotype"), y), tr); m2 <- lm(reformulate(paste(k, "* phenotype"), y), tr)
  sl <- sapply(levels(tr$phenotype), function(ph) { d <- tr[tr$phenotype == ph, ]; if (nrow(d) < 10) NA else coef(lm(reformulate(k, y), d))[[2]] })
  slopes[[nm]] <- data.frame(arm = nm, key = k, phenotype = names(sl), n = as.integer(table(tr$phenotype)[names(sl)]),
                             slope_per_unit = round(sl, 3), interaction_p = round(anova(m1, m2)$`Pr(>F)`[2], 3), row.names = NULL)
}
res <- do.call(rbind, out); sl <- do.call(rbind, slopes)
write.csv(res, file.path(here, "forest_scenarios.csv"), row.names = FALSE); write.csv(sl, file.path(here, "key_covariate_within_phenotype.csv"), row.names = FALSE)
cat("Predicted responder probability by scenario (training patients, 90% bootstrap interval):\n")
print(transform(res, responder_prob = round(responder_prob, 2), lo90 = round(lo90, 2), hi90 = round(hi90, 2)), row.names = FALSE)
cat("\nKey covariate within each onset phenotype (slope of the continuous outcome per unit of the covariate):\n"); print(sl, row.names = FALSE)
res$scenario <- factor(res$scenario, rev(unique(res$scenario)))
ggsave(file.path(here, "fig_covariate_forest.png"),
  ggplot(res, aes(responder_prob, scenario)) + geom_vline(data = subset(res, grepl("Reference", scenario)), aes(xintercept = responder_prob), linetype = 2, colour = "grey40") +
    geom_pointrange(aes(xmin = lo90, xmax = hi90)) + facet_wrap(~arm, scales = "free_y", ncol = 1) + xlim(0, 1) +
    labs(x = "Predicted probability of response (point = estimate, line = 90% bootstrap interval)", y = NULL,
         title = "Covariate scenarios vs the reference patient, per arm (training patients)"), width = 9, height = 8, dpi = 150)
