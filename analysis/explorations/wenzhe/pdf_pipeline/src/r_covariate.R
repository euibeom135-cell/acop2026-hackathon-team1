# Covariate-modelling methods from the kickoff PDF (PDF-example scope, in the PDF's own R libraries):
#   lm/glm, MASS::stepAIC both-direction with BIC, leaps::regsubsets best subset (BIC, nvmax<=10; continuous outcome only), glmnet ridge / LASSO (lambda.min) / elastic net (alpha=.5),
#   mgcv::gam (s(k=5), REML, select=TRUE) as the single nonlinear representative, PCA + PCR (k by CV).  Polynomial / piecewise / regression-spline / smoothing-spline are dropped: the GAM represents curvature.
# usage: Rscript r_covariate.R <arm> <reg|bin> <cv|test>   cv: repeated 5-fold CV on TRAIN with shared folds, scaler re-fitted on each fold's training rows; test: fit on TRAIN, predict TEST (only called by s07)
source(file.path(dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE)[1]))), "r_common.R"))
a <- commandArgs(TRUE); arm <- a[1]; task <- a[2]; stage <- a[3]
tr <- read.csv(file.path(RES, paste0("features_train_", arm, ".csv"))); yname <- if (task == "reg") "y" else "label"; fam <- if (task == "reg") gaussian() else binomial(); FIT <- make_fit(task)
mk <- function(d) { d$.t <- d[[yname]]; d }

M <- list()   # every method takes prepared (scaled, constant-dropped) d, nd
M[["lm / glm (all covariates)"]] <- function(d, nd) { m <- FIT(rhs(fnames(d)), d); list(pred = prd(m, nd), terms = terms_of(m)) }
M[["Stepwise both (BIC)"]] <- function(d, nd) {
  full <- FIT(rhs(fnames(d)), d); m <- stepAIC(full, direction = "both", trace = 0, k = log(nrow(d))); list(pred = prd(m, nd), terms = terms_of(m)) }
if (task == "reg") M[["Best subset (leaps, BIC, nvmax=10)"]] <- function(d, nd) {
  fs <- fnames(d); rs <- regsubsets(x = as.matrix(d[fs]), y = d$.t, nvmax = 10, really.big = TRUE, method = "exhaustive"); s <- summary(rs); id <- which.min(s$bic)
  co <- coef(rs, id); xn <- cbind(1, as.matrix(nd[names(co)[-1]])); list(pred = as.numeric(xn %*% co), terms = co[-1]) }
gn <- function(alpha) function(d, nd) {
  set.seed(1); cvm <- gn_fit(d, task, alpha); fs <- fnames(d); s <- "lambda.min"
  p <- as.numeric(predict(cvm, as.matrix(nd[fs]), s = s, type = "response")); cf <- as.matrix(coef(cvm, s = s))[-1, 1]; list(pred = p, terms = cf[cf != 0]) }
M[["Ridge (glmnet)"]] <- gn(0); M[["LASSO (glmnet, lambda.min)"]] <- gn(1); M[["Elastic net (glmnet, alpha=.5)"]] <- gn(0.5)
M[["GAM (mgcv, s(k=5), REML, select)"]] <- function(d, nd) {
  fs <- fnames(d); dm <- fs[sapply(d[fs], isdum)]; ct <- setdiff(fs, dm)
  m <- gam(as.formula(paste(".t ~", paste(c(sprintf("s(%s, k=5)", ct), dm), collapse = " + "))), data = d, family = fam, method = "REML", select = TRUE)
  st <- summary(m)$s.table; pt <- summary(m)$p.table; sel <- c(gsub("^s\\(|\\)$", "", rownames(st)[st[, ncol(st)] < 0.05]), rownames(pt)[pt[, ncol(pt)] < 0.05 & rownames(pt) != "(Intercept)"])
  list(pred = as.numeric(predict(m, nd, type = "response")), terms = setNames(rep(1, length(sel)), sel)) }
M[["PCR (prcomp, k by 5-fold CV)"]] <- function(d, nd) {
  fs <- fnames(d); pc <- prcomp(d[fs], center = TRUE, scale. = FALSE); S <- pc$x; set.seed(1); idx <- sample(rep(1:5, length.out = nrow(d))); kmax <- min(12, ncol(S))
  lmf <- function(dd) if (task == "reg") lm(.t ~ ., dd) else glm(.t ~ ., dd, family = binomial)
  err <- sapply(1:kmax, function(k) mean(sapply(1:5, function(i) { mm <- lmf(data.frame(.t = d$.t[idx != i], S[idx != i, 1:k, drop = FALSE]))
    p <- predict(mm, data.frame(S[idx == i, 1:k, drop = FALSE]), type = "response"); mean((d$.t[idx == i] - p)^2) })))
  k <- which.min(err); mm <- lmf(data.frame(.t = d$.t, S[, 1:k, drop = FALSE])); Sn <- predict(pc, nd[fs])
  list(pred = as.numeric(predict(mm, data.frame(Sn[, 1:k, drop = FALSE]), type = "response")), terms = setNames(rep(1, k), paste0("PC", 1:k))) }

tr <- mk(tr)
safe <- function(fn, d, nd) tryCatch({ pp <- scale_fit(d, nd); fn(pp$d, pp$nd) }, error = function(e) list(pred = rep(NA_real_, nrow(nd)), terms = numeric(0), err = conditionMessage(e)))
P <- list(); Tm <- list()
if (stage == "cv") {
  fo <- read.csv(file.path(RES, paste0("folds_", arm, ".csv")))
  for (nm in names(M)) for (r in unique(fo$rep)) for (k in sort(unique(fo$fold[fo$rep == r]))) {
    te <- fo$row[fo$rep == r & fo$fold == k] + 1; out <- safe(M[[nm]], tr[-te, ], tr[te, ])
    P[[length(P) + 1]] <- data.frame(method = nm, rep = r, row = te - 1, pred = out$pred)
    if (length(out$terms)) Tm[[length(Tm) + 1]] <- data.frame(method = nm, fit = paste(r, k), term = names(out$terms), coef = as.numeric(out$terms)) }
} else {
  te <- mk(read.csv(file.path(RES, paste0("features_test_", arm, ".csv"))))
  for (nm in names(M)) { out <- safe(M[[nm]], tr, te); P[[length(P) + 1]] <- data.frame(method = nm, rep = 0, row = seq_len(nrow(te)) - 1, pred = out$pred)
    if (length(out$terms)) Tm[[length(Tm) + 1]] <- data.frame(method = nm, fit = "train", term = names(out$terms), coef = as.numeric(out$terms)) }
}
write.csv(do.call(rbind, P), file.path(RES, sprintf("r_%s_%s_%s_preds.csv", arm, task, stage)), row.names = FALSE)
write.csv(do.call(rbind, Tm), file.path(RES, sprintf("r_%s_%s_%s_terms.csv", arm, task, stage)), row.names = FALSE)
cat("done", arm, task, stage, "NA preds:", sum(is.na(do.call(rbind, P)$pred)), "\n")
