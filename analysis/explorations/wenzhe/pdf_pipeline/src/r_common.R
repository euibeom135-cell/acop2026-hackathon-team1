# Shared R helpers for the covariate track: libraries, paths, per-fit scaling (numeric covariates only), model-matrix helpers.
.libPaths(c("~/R-lib", .libPaths())); suppressMessages({library(MASS); library(leaps); library(glmnet); library(splines); library(mgcv)})
.args <- commandArgs(FALSE); SRC <- dirname(normalizePath(sub("--file=", "", grep("--file=", .args, value = TRUE)[1]))); RES <- file.path(SRC, "..", "results")
TARGETS <- c("y", "label", ".t")
fnames <- function(d) setdiff(names(d), TARGETS)
isdum <- function(v) length(unique(v)) <= 2
# Scale ONLY the numeric (non-0/1) covariates with the mean/sd of `d` (the fit's own training rows); drop columns that are constant in `d`. Returns list(d, nd) with identical columns.
scale_fit <- function(d, nd) {
  fs <- fnames(d); fs <- fs[sapply(d[fs], function(v) sd(v) > 0)]; cont <- fs[!sapply(d[fs], isdum)]
  for (v in cont) { m <- mean(d[[v]]); s <- sd(d[[v]]); d[[v]] <- (d[[v]] - m) / s; nd[[v]] <- (nd[[v]] - m) / s }
  keep <- c(fs, intersect(TARGETS, names(d))); list(d = d[keep], nd = nd[intersect(keep, names(nd))])
}
rhs <- function(v) as.formula(paste(".t ~", paste(c(v, if (length(v) == 0) "1"), collapse = " + ")))
make_fit <- function(task) if (task == "reg") function(f, d) do.call("lm", list(f, data = d)) else function(f, d) do.call("glm", list(f, data = d, family = quote(binomial)))   # data embedded in the call so stepAIC can refit
prd <- function(m, nd) as.numeric(predict(m, newdata = nd, type = "response"))
terms_of <- function(m) { co <- coef(m); co[names(co) != "(Intercept)" & !is.na(co)] }
# glmnet on the prepared matrix: standardize = FALSE (numeric columns are already z-scored in-fold, 0/1 dummies are left on their natural scale, per the clean-build rule)
gn_fit <- function(d, task, alpha, foldid = NULL) { X <- as.matrix(d[fnames(d)]); cv.glmnet(X, d$.t, alpha = alpha, family = if (task == "reg") "gaussian" else "binomial", nfolds = 10, standardize = FALSE, foldid = foldid) }
