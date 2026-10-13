# TRAIN-ONLY diagnostics figures for the report: glmnet coefficient paths (alpha 1 / 0 / .5) and mgcv GAM partial smooths. Same scaling (scale_fit: z-score non-0/1 columns, dummies raw, constants dropped)
# and same model specs as r_covariate.R (glmnet standardize=FALSE; gam s(x,k=5), dummies linear, REML, select=TRUE). Never reads any held-out data.
# usage: Rscript r_diag.R <arm> <reg|bin>   -> results/diag_figs/{glmnet_path,gam}_<arm>_<task>.png (on error: _FAILED_<what>_<arm>_<task>.txt)
source(file.path(dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE)[1]))), "r_common.R"))
a <- commandArgs(TRUE); arm <- a[1]; task <- a[2]; yname <- if (task == "reg") "y" else "label"; fam <- if (task == "reg") gaussian() else binomial()
OUT <- file.path(RES, "diag_figs"); dir.create(OUT, showWarnings = FALSE, recursive = TRUE)
d0 <- read.csv(file.path(RES, paste0("features_train_", arm, ".csv"))); d0$.t <- d0[[yname]]; d <- scale_fit(d0, d0)$d; fs <- fnames(d)   # scale on train itself
fail <- function(what, e) writeLines(conditionMessage(e), file.path(OUT, sprintf("_FAILED_%s_%s_%s.txt", what, arm, task)))
nm <- c("LASSO (alpha=1)", "Ridge (alpha=0)", "Elastic net (alpha=0.5)"); al <- c(1, 0, 0.5)

# 1) glmnet paths + lambda.min (cv.glmnet as in gn_fit, seed 1)
tryCatch({
  X <- as.matrix(d[fs]); fm <- if (task == "reg") "gaussian" else "binomial"
  png(file.path(OUT, sprintf("glmnet_path_%s_%s.png", arm, task)), width = 2400, height = 800, res = 150); par(mfrow = c(1, 3), mar = c(4.5, 4.5, 4.2, 1), cex.main = 1.3, cex.lab = 1.2, cex.axis = 1.1)
  # plot the cv object's own path fit (same lambda grid as lambda.min) so the dashed lambda.min line is in range on every panel; lift the title above the top (nonzero-count) axis
  for (i in 1:3) { set.seed(1); cvm <- gn_fit(d, task, al[i])
    plot(cvm$glmnet.fit, xvar = "lambda", label = FALSE, main = ""); abline(v = -log(cvm$lambda.min), lty = 2, lwd = 1.5); title(main = nm[i], line = 2.8) }   # this glmnet build plots the x-axis as -log(lambda), so the lambda.min marker is at -log(lambda.min)
  invisible(dev.off())
}, error = function(e) { while (dev.cur() > 1) dev.off(); fail("glmnet", e) })

# 2) GAM partial smooths (spec identical to r_covariate.R)
tryCatch({
  dm <- fs[sapply(d[fs], isdum)]; ct <- setdiff(fs, dm)
  m <- gam(as.formula(paste(".t ~", paste(c(sprintf("s(%s, k=5)", ct), dm), collapse = " + "))), data = d, family = fam, method = "REML", select = TRUE)
  pdf(NULL); pl <- plot(m, pages = 0, residuals = FALSE); invisible(dev.off()); pl <- Filter(function(p) !is.null(p$fit) && !is.null(p$se), pl)   # smooth curves + se (mgcv's own shade= is not honoured on this build, so shading is drawn here)
  np <- length(pl); nc <- min(4, max(np, 1)); nr <- ceiling(max(np, 1) / nc)
  png(file.path(OUT, sprintf("gam_%s_%s.png", arm, task)), width = 600 * nc, height = 500 * nr, res = 120); par(mfrow = c(nr, nc), mar = c(4.5, 4.5, 2, 1), cex.lab = 1.2, cex.axis = 1.1)
  for (p in pl) { f <- as.numeric(p$fit); se <- as.numeric(p$se); lo <- f - se; hi <- f + se   # p$se is already se*se.mult (=2)
    plot(p$x, f, type = "n", ylim = range(lo, hi, 0), xlab = p$xlab, ylab = p$ylab); polygon(c(p$x, rev(p$x)), c(lo, rev(hi)), col = "lightsteelblue", border = NA)   # shaded +-2 SE
    abline(h = 0, col = "grey60", lty = 3); lines(p$x, f, lwd = 2); rug(p$raw) }
  invisible(dev.off())
}, error = function(e) { while (dev.cur() > 1) dev.off(); fail("gam", e) })
cat("r_diag OK", arm, task, "\n")
