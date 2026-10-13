# Signal-vs-noise evidence from the R covariate track (TRAIN rows only). usage: Rscript r_signal.R <arm> <reg|bin>
# Per covariate (all numerics z-scored with the fit's own training rows, dummies left 0/1):
#   full-train lm/glm standardised coefficient + t/z; selection by LASSO / elastic net (lambda.min) / stepwise-BIC(both) on full train and in B=200 bootstrap resamples (cv.glmnet folds keep duplicate rows together);
#   sign of the lm/glm coefficient in each of 5 train subsamples (80%, leave-one-fold-out); GAM (mgcv s(k=5), REML, select=TRUE) edf and p; shuffled-outcome null of |t|/|z| (B=500 permutations).
source(file.path(dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE)[1]))), "r_common.R"))
a <- commandArgs(TRUE); arm <- a[1]; task <- a[2]; B <- 200; BNULL <- 500
tr <- read.csv(file.path(RES, paste0("features_train_", arm, ".csv"))); yname <- if (task == "reg") "y" else "label"; tr$.t <- tr[[yname]]; FIT <- make_fit(task); n <- nrow(tr); fam <- if (task == "reg") gaussian() else binomial()
pp <- scale_fit(tr, tr); d <- pp$d; fs <- fnames(d)
tz <- function(m) { s <- summary(m)$coefficients; s <- s[rownames(s) != "(Intercept)", , drop = FALSE]; list(b = s[, 1], t = s[, 3], p = s[, 4]) }
full <- suppressWarnings(FIT(rhs(fs), d)); fz <- tz(full)
# a fixed foldid is passed inside the bootstrap, so no RNG reset there (a set.seed inside the loop would freeze the resampling)
pick_gn <- function(dd, alpha, foldid = NULL) { if (is.null(foldid)) set.seed(1); cvm <- gn_fit(dd, task, alpha, foldid); cf <- as.matrix(coef(cvm, s = "lambda.min"))[-1, 1]; names(cf)[cf != 0] }
pick_step <- function(dd) { m <- suppressWarnings(FIT(rhs(fnames(dd)), dd)); m2 <- suppressWarnings(stepAIC(m, direction = "both", trace = 0, k = log(nrow(dd)))); setdiff(names(coef(m2)), "(Intercept)") }
sel_full <- list(lasso = pick_gn(d, 1), enet = pick_gn(d, 0.5), step = pick_step(d))
# GAM on full train
dm <- fs[sapply(d[fs], isdum)]; ct <- setdiff(fs, dm)
g <- gam(as.formula(paste(".t ~", paste(c(sprintf("s(%s, k=5)", ct), dm), collapse = " + "))), data = d, family = fam, method = "REML", select = TRUE); sg <- summary(g)
gam_edf <- setNames(rep(NA_real_, length(fs)), fs); gam_p <- gam_edf; rn <- gsub("^s\\(|\\)$", "", rownames(sg$s.table)); gam_edf[rn] <- sg$s.table[, "edf"]; gam_p[rn] <- sg$s.table[, ncol(sg$s.table)]
pt <- sg$p.table; pt <- pt[rownames(pt) != "(Intercept)", , drop = FALSE]; gam_p[rownames(pt)] <- pt[, ncol(pt)]; gam_edf[rownames(pt)] <- 1
# subsample sign consistency
set.seed(42); sf <- sample(rep(1:5, length.out = n)); sgn_full <- sign(fz$b[fs]); same <- setNames(rep(0, length(fs)), fs)
for (k in 1:5) { p2 <- scale_fit(tr[sf != k, ], tr[sf != k, ]); m <- suppressWarnings(FIT(rhs(fnames(p2$d)), p2$d)); b <- coef(m); for (v in intersect(fs, names(b))) same[v] <- same[v] + (sign(b[v]) == sgn_full[v]) }
# bootstrap selection frequency
set.seed(43); cnt <- list(lasso = setNames(rep(0, length(fs)), fs), enet = setNames(rep(0, length(fs)), fs), step = setNames(rep(0, length(fs)), fs))
for (bi in 1:B) {
  ids <- sample(n, n, TRUE); pf <- sample(rep(1:10, length.out = n)); p2 <- scale_fit(tr[ids, ], tr[ids, ]); db <- p2$d
  s <- list(lasso = pick_gn(db, 1, pf[ids]), enet = pick_gn(db, 0.5, pf[ids]), step = pick_step(db))
  for (nm in names(s)) { v <- intersect(s[[nm]], fs); cnt[[nm]][v] <- cnt[[nm]][v] + 1 } }
# shuffled-outcome null for |t| or |z| (outcome permuted, design fixed)
set.seed(44); nullt <- matrix(NA_real_, BNULL, length(fs), dimnames = list(NULL, fs))
for (i in 1:BNULL) { dd <- d; dd$.t <- sample(d$.t); m <- suppressWarnings(FIT(rhs(fs), dd)); z <- tz(m); nullt[i, names(z$t)] <- abs(z$t) }
out <- data.frame(covariate = fs, coef_std = fz$b[fs], tstat = fz$t[fs], p_value = fz$p[fs], abs_t_null95 = apply(nullt, 2, quantile, 0.95, na.rm = TRUE), abs_t_null_max = apply(nullt, 2, max, na.rm = TRUE),
  selfreq_lasso = cnt$lasso[fs] / B, selfreq_enet = cnt$enet[fs] / B, selfreq_step_bic = cnt$step[fs] / B, sel_full_lasso = fs %in% sel_full$lasso, sel_full_enet = fs %in% sel_full$enet, sel_full_step_bic = fs %in% sel_full$step,
  sign_same_k_of_5 = same[fs], gam_edf = gam_edf[fs], gam_p = gam_p[fs], row.names = NULL)
write.csv(out, file.path(RES, sprintf("signal_r_%s_%s.csv", arm, task)), row.names = FALSE); cat("done", arm, task, "\n")
