# Covariate-modelling methods from the kickoff PDF, in the PDF's own R libraries:
#   lm/glm, MASS::stepAIC (fwd/bwd/both), leaps::regsubsets (best subset), glmnet (ridge/LASSO/elastic net), poly(), cut(), splines::bs, smooth.spline, mgcv::gam, prcomp (PCR)
# usage: Rscript r_covariate.R <arm> <reg|bin> <cv|test>     cv: repeated 5-fold CV on TRAIN with shared folds; test: fit on TRAIN, predict TEST (only called by s06)
.libPaths(c("~/R-lib", .libPaths())); suppressMessages({library(MASS); library(leaps); library(glmnet); library(splines); library(mgcv)})
a <- commandArgs(TRUE); arm <- a[1]; task <- a[2]; stage <- a[3]
res <- file.path("..", "results"); tr <- read.csv(file.path(res, paste0("train_", arm, ".csv")))
yname <- if (task == "reg") "y" else "label"; feats <- setdiff(names(tr), c("y", "label")); fam <- if (task == "reg") gaussian() else binomial()
isdum <- sapply(tr[feats], function(v) length(unique(v)) <= 2); cont <- feats[!isdum]; dums <- feats[isdum]
mk <- function(d) { d$.t <- d[[yname]]; d }
fitfun <- function(d) if (task == "reg") function(f) do.call("lm", list(f, data = d)) else function(f) do.call("glm", list(f, data = d, family = quote(binomial)))   # data embedded in call so stepAIC can refit
prd <- function(m, nd) as.numeric(predict(m, newdata = nd, type = "response"))
rhs <- function(v) as.formula(paste(".t ~", paste(c(v, if (length(v) == 0) "1"), collapse = " + ")))
terms_of <- function(m) { co <- coef(m); co <- co[names(co) != "(Intercept)"]; co }

M <- list()
M[["lm / glm (all covariates)"]] <- function(d, nd) { f <- fitfun(d); m <- f(rhs(feats)); list(pred = prd(m, nd), terms = terms_of(m)) }
step_m <- function(dir, k = 2) function(d, nd) {
  f <- fitfun(d); full <- f(rhs(feats)); nul <- f(rhs(character(0)))
  m <- switch(dir, forward = stepAIC(nul, scope = list(lower = ~1, upper = formula(full)), direction = "forward", trace = 0, k = k),
              backward = stepAIC(full, direction = "backward", trace = 0, k = k), both = stepAIC(full, direction = "both", trace = 0, k = k))
  list(pred = prd(m, nd), terms = terms_of(m)) }
M[["Stepwise forward (AIC)"]] <- step_m("forward"); M[["Stepwise backward (AIC)"]] <- step_m("backward"); M[["Stepwise both (AIC)"]] <- step_m("both")
M[["Stepwise both (BIC)"]] <- function(d, nd) step_m("both", k = log(nrow(d)))(d, nd)
if (task == "reg") M[["Best subset (leaps, BIC, nvmax=10)"]] <- function(d, nd) {
  X <- d[feats]; rs <- regsubsets(x = as.matrix(X), y = d$.t, nvmax = 10, really.big = TRUE, method = "exhaustive"); s <- summary(rs); id <- which.min(s$bic)
  co <- coef(rs, id); xn <- cbind(1, as.matrix(nd[names(co)[-1]])); list(pred = as.numeric(xn %*% co), terms = co[-1]) }
gn <- function(alpha, s = "lambda.min") function(d, nd) {
  set.seed(1); X <- as.matrix(d[feats]); cvm <- cv.glmnet(X, d$.t, alpha = alpha, family = if (task == "reg") "gaussian" else "binomial", nfolds = 10)
  p <- as.numeric(predict(cvm, as.matrix(nd[feats]), s = s, type = "response")); cf <- as.matrix(coef(cvm, s = s))[-1, 1]; list(pred = p, terms = cf[cf != 0]) }
M[["Ridge (glmnet)"]] <- gn(0); M[["LASSO (glmnet, lambda.min)"]] <- gn(1); M[["LASSO (glmnet, lambda.1se)"]] <- gn(1, "lambda.1se"); M[["Elastic net (glmnet, alpha=.5)"]] <- gn(0.5)
curvesel <- function(d, k = 4) cont[order(-abs(sapply(cont, function(v) cor(d[[v]], d$.t))))[seq_len(k)]]   # curve covariates chosen INSIDE each fit (train rows only): top-4 continuous by |cor| with the target
M[["Polynomial deg-2 (top-4 covariates)"]] <- function(d, nd) { cv_ <- curvesel(d); f <- fitfun(d); m <- f(as.formula(paste(".t ~", paste(sprintf("poly(%s, 2)", cv_), collapse = " + ")))); list(pred = prd(m, nd), terms = terms_of(m)) }
M[["Piecewise: cut() tertile bins (top-4 covariates)"]] <- function(d, nd) {
  cv_ <- curvesel(d); f <- fitfun(d); br <- lapply(cv_, function(v) c(-Inf, quantile(d[[v]], c(1/3, 2/3)), Inf)); names(br) <- cv_
  cutd <- function(x) { for (v in cv_) x[[paste0(v, "_bin")]] <- cut(x[[v]], br[[v]]); x }
  dd <- cutd(d); nn <- cutd(nd); m <- fitfun(dd)(as.formula(paste(".t ~", paste(paste0(cv_, "_bin"), collapse = " + ")))); list(pred = prd(m, nn), terms = terms_of(m)) }
M[["Regression spline bs(df=4) (top-4 covariates)"]] <- function(d, nd) { cv_ <- curvesel(d); f <- fitfun(d); m <- f(as.formula(paste(".t ~", paste(sprintf("bs(%s, df=4)", cv_), collapse = " + ")))); list(pred = prd(m, nd), terms = terms_of(m)) }
M[["Smoothing spline (top-1 covariate, cv=TRUE)"]] <- function(d, nd) {
  cr <- abs(sapply(cont, function(v) cor(d[[v]], d$.t))); v <- cont[which.max(cr)]; ss <- smooth.spline(d[[v]], d$.t, cv = TRUE)
  p <- predict(ss, nd[[v]])$y; if (task == "bin") p <- pmin(pmax(p, 0), 1); list(pred = as.numeric(p), terms = setNames(ss$df, v)) }
M[["GAM (mgcv, s(k=5), REML, select)"]] <- function(d, nd) {
  fr <- as.formula(paste(".t ~", paste(c(sprintf("s(%s, k=5)", cont), dums), collapse = " + "))); m <- gam(fr, data = d, family = fam, method = "REML", select = TRUE)
  st <- summary(m)$s.table; sel <- rownames(st)[st[, ncol(st)] < 0.05]; list(pred = as.numeric(predict(m, nd, type = "response")), terms = setNames(rep(1, length(sel)), gsub("^s\\(|\\)$", "", sel))) }
M[["PCR (prcomp, k by 5-fold CV)"]] <- function(d, nd) {
  pc <- prcomp(d[feats], center = TRUE, scale. = FALSE); S <- pc$x; set.seed(1); idx <- sample(rep(1:5, length.out = nrow(d))); kmax <- min(12, ncol(S))
  err <- sapply(1:kmax, function(k) mean(sapply(1:5, function(i) { dd <- data.frame(.t = d$.t[idx != i], S[idx != i, 1:k, drop = FALSE]); mm <- if (task == "reg") lm(.t ~ ., dd) else glm(.t ~ ., dd, family = binomial)
    p <- predict(mm, data.frame(S[idx == i, 1:k, drop = FALSE]), type = "response"); mean((d$.t[idx == i] - p)^2) })))
  k <- which.min(err); dd <- data.frame(.t = d$.t, S[, 1:k, drop = FALSE]); mm <- if (task == "reg") lm(.t ~ ., dd) else glm(.t ~ ., dd, family = binomial)
  Sn <- predict(pc, nd[feats]); list(pred = as.numeric(predict(mm, data.frame(Sn[, 1:k, drop = FALSE]), type = "response")), terms = setNames(rep(1, k), paste0("PC", 1:k))) }

tr <- mk(tr)
safe <- function(fn, d, nd) tryCatch(fn(d, nd), error = function(e) list(pred = rep(NA_real_, nrow(nd)), terms = numeric(0), err = conditionMessage(e)))
P <- list(); Tm <- list()
if (stage == "cv") {
  fo <- read.csv(file.path(res, paste0("folds_", arm, ".csv")))
  for (nm in names(M)) for (r in unique(fo$rep)) for (k in sort(unique(fo$fold[fo$rep == r]))) {
    te <- fo$row[fo$rep == r & fo$fold == k] + 1; out <- safe(M[[nm]], tr[-te, ], tr[te, ])
    P[[length(P) + 1]] <- data.frame(method = nm, rep = r, row = te - 1, pred = out$pred)
    if (length(out$terms)) Tm[[length(Tm) + 1]] <- data.frame(method = nm, fit = paste(r, k), term = names(out$terms), coef = as.numeric(out$terms)) }
} else {
  te <- mk(read.csv(file.path(res, paste0("test_", arm, ".csv")))); te$.t <- te[[yname]]
  for (nm in names(M)) { out <- safe(M[[nm]], tr, te); P[[length(P) + 1]] <- data.frame(method = nm, rep = 0, row = seq_len(nrow(te)) - 1, pred = out$pred)
    if (length(out$terms)) Tm[[length(Tm) + 1]] <- data.frame(method = nm, fit = "train", term = names(out$terms), coef = as.numeric(out$terms)) }
}
write.csv(do.call(rbind, P), file.path(res, sprintf("r_%s_%s_%s_preds.csv", arm, task, stage)), row.names = FALSE)
write.csv(do.call(rbind, Tm), file.path(res, sprintf("r_%s_%s_%s_terms.csv", arm, task, stage)), row.names = FALSE)
cat("done", arm, task, stage, "NA preds:", sum(is.na(do.call(rbind, P)$pred)), "\n")
