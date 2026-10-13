# Seed-sensitivity R side: fit every covariate-track method on TRAIN, predict TEST, and return per-covariate evidence (p-value or non-zero coefficient).
# Same method definitions as ../../src/r_covariate.R (copy, extended with evidence). usage: Rscript r_seed.R <arm> <reg|bin> <dir with train_<arm>.csv / test_<arm>.csv>
.libPaths(c("~/R-lib", .libPaths())); suppressMessages({library(MASS); library(leaps); library(glmnet); library(splines); library(mgcv)})
a <- commandArgs(TRUE); arm <- a[1]; task <- a[2]; dir <- a[3]
tr <- read.csv(file.path(dir, paste0("train_", arm, ".csv"))); te <- read.csv(file.path(dir, paste0("test_", arm, ".csv")))
yname <- if (task == "reg") "y" else "label"; feats <- setdiff(names(tr), c("y", "label")); fam <- if (task == "reg") gaussian() else binomial()
isdum <- sapply(tr[feats], function(v) length(unique(v)) <= 2); cont <- feats[!isdum]; dums <- feats[isdum]
tr$.t <- tr[[yname]]; te$.t <- te[[yname]]
fitfun <- function(d) if (task == "reg") function(f) do.call("lm", list(f, data = d)) else function(f) do.call("glm", list(f, data = d, family = quote(binomial)))
prd <- function(m, nd) as.numeric(predict(m, newdata = nd, type = "response"))
rhs <- function(v) as.formula(paste(".t ~", paste(c(v, if (length(v) == 0) "1"), collapse = " + ")))
ev_lm <- function(m) { cf <- summary(m)$coefficients; cf <- cf[rownames(cf) != "(Intercept)", , drop = FALSE]; data.frame(term = rownames(cf), coef = cf[, 1], p = cf[, ncol(cf)]) }
ev_drop <- function(m) { dr <- suppressWarnings(drop1(m, test = if (task == "reg") "F" else "Chisq")); dr <- dr[rownames(dr) != "<none>", , drop = FALSE]; data.frame(term = rownames(dr), coef = NA, p = dr[, ncol(dr)]) }
curvesel <- function(d, k = 4) cont[order(-abs(sapply(cont, function(v) cor(d[[v]], d$.t))))[seq_len(k)]]
M <- list()
M[["lm / glm (all covariates)"]] <- function(d, nd) { m <- fitfun(d)(rhs(feats)); list(pred = prd(m, nd), ev = ev_lm(m)) }
step_m <- function(dir_, k = 2) function(d, nd) { f <- fitfun(d); full <- f(rhs(feats)); nul <- f(rhs(character(0)))
  m <- switch(dir_, forward = stepAIC(nul, scope = list(lower = ~1, upper = formula(full)), direction = "forward", trace = 0, k = k), backward = stepAIC(full, direction = "backward", trace = 0, k = k), both = stepAIC(full, direction = "both", trace = 0, k = k))
  list(pred = prd(m, nd), ev = ev_lm(m)) }
M[["Stepwise forward (AIC)"]] <- step_m("forward"); M[["Stepwise backward (AIC)"]] <- step_m("backward"); M[["Stepwise both (AIC)"]] <- step_m("both"); M[["Stepwise both (BIC)"]] <- function(d, nd) step_m("both", k = log(nrow(d)))(d, nd)
if (task == "reg") M[["Best subset (leaps, BIC, nvmax=10)"]] <- function(d, nd) { rs <- regsubsets(x = as.matrix(d[feats]), y = d$.t, nvmax = 10, really.big = TRUE); id <- which.min(summary(rs)$bic); co <- coef(rs, id)
  m <- lm(as.formula(paste(".t ~", paste(names(co)[-1], collapse = " + "))), data = d); list(pred = as.numeric(cbind(1, as.matrix(nd[names(co)[-1]])) %*% co), ev = ev_lm(m)) }
gn <- function(alpha, s = "lambda.min") function(d, nd) { set.seed(1); cvm <- cv.glmnet(as.matrix(d[feats]), d$.t, alpha = alpha, family = if (task == "reg") "gaussian" else "binomial", nfolds = 10)
  p <- as.numeric(predict(cvm, as.matrix(nd[feats]), s = s, type = "response")); cf <- as.matrix(coef(cvm, s = s))[-1, 1]; cf <- cf[cf != 0]; list(pred = p, ev = if (length(cf)) data.frame(term = names(cf), coef = as.numeric(cf), p = NA) else NULL) }
M[["Ridge (glmnet)"]] <- gn(0); M[["LASSO (glmnet, lambda.min)"]] <- gn(1); M[["LASSO (glmnet, lambda.1se)"]] <- gn(1, "lambda.1se"); M[["Elastic net (glmnet, alpha=.5)"]] <- gn(0.5)
M[["Polynomial deg-2 (top-4 covariates)"]] <- function(d, nd) { cv_ <- curvesel(d); m <- fitfun(d)(as.formula(paste(".t ~", paste(sprintf("poly(%s, 2)", cv_), collapse = " + ")))); list(pred = prd(m, nd), ev = ev_drop(m)) }
M[["Piecewise: cut() tertile bins (top-4 covariates)"]] <- function(d, nd) { cv_ <- curvesel(d); br <- lapply(cv_, function(v) c(-Inf, quantile(d[[v]], c(1/3, 2/3)), Inf)); names(br) <- cv_
  cutd <- function(x) { for (v in cv_) x[[paste0(v, "_bin")]] <- cut(x[[v]], br[[v]]); x }; dd <- cutd(d); nn <- cutd(nd); m <- fitfun(dd)(as.formula(paste(".t ~", paste(paste0(cv_, "_bin"), collapse = " + ")))); list(pred = prd(m, nn), ev = ev_drop(m)) }
M[["Regression spline bs(df=4) (top-4 covariates)"]] <- function(d, nd) { cv_ <- curvesel(d); m <- fitfun(d)(as.formula(paste(".t ~", paste(sprintf("bs(%s, df=4)", cv_), collapse = " + ")))); list(pred = prd(m, nd), ev = ev_drop(m)) }
M[["Smoothing spline (top-1 covariate, cv=TRUE)"]] <- function(d, nd) { cr <- abs(sapply(cont, function(v) cor(d[[v]], d$.t))); v <- cont[which.max(cr)]; ss <- smooth.spline(d[[v]], d$.t, cv = TRUE)
  p <- predict(ss, nd[[v]])$y; if (task == "bin") p <- pmin(pmax(p, 0), 1); list(pred = as.numeric(p), ev = data.frame(term = v, coef = NA, p = cor.test(d[[v]], d$.t)$p.value)) }
M[["GAM (mgcv, s(k=5), REML, select)"]] <- function(d, nd) { m <- gam(as.formula(paste(".t ~", paste(c(sprintf("s(%s, k=5)", cont), dums), collapse = " + "))), data = d, family = fam, method = "REML", select = TRUE); s <- summary(m)
  pt <- s$p.table[rownames(s$p.table) != "(Intercept)", , drop = FALSE]; st <- s$s.table
  list(pred = as.numeric(predict(m, nd, type = "response")), ev = rbind(data.frame(term = rownames(pt), coef = pt[, 1], p = pt[, ncol(pt)]), data.frame(term = gsub("^s\\(|\\)$", "", rownames(st)), coef = NA, p = st[, ncol(st)]))) }
M[["PCR (prcomp, k by 5-fold CV)"]] <- function(d, nd) { pc <- prcomp(d[feats], center = TRUE, scale. = FALSE); S <- pc$x; set.seed(1); idx <- sample(rep(1:5, length.out = nrow(d))); kmax <- min(12, ncol(S))
  err <- sapply(1:kmax, function(k) mean(sapply(1:5, function(i) { dd <- data.frame(.t = d$.t[idx != i], S[idx != i, 1:k, drop = FALSE]); mm <- if (task == "reg") lm(.t ~ ., dd) else glm(.t ~ ., dd, family = binomial)
    mean((d$.t[idx == i] - predict(mm, data.frame(S[idx == i, 1:k, drop = FALSE]), type = "response"))^2) }))); k <- which.min(err); dd <- data.frame(.t = d$.t, S[, 1:k, drop = FALSE]); mm <- if (task == "reg") lm(.t ~ ., dd) else glm(.t ~ ., dd, family = binomial)
  list(pred = as.numeric(predict(mm, data.frame(predict(pc, nd[feats])[, 1:k, drop = FALSE]), type = "response")), ev = NULL) }
P <- list(); E <- list()
for (nm in names(M)) { out <- tryCatch(M[[nm]](tr, te), error = function(e) list(pred = rep(NA_real_, nrow(te)), ev = NULL))
  P[[length(P) + 1]] <- data.frame(method = nm, row = seq_len(nrow(te)) - 1, pred = out$pred, obs = te[[yname]]); if (!is.null(out$ev) && nrow(out$ev)) E[[length(E) + 1]] <- cbind(method = nm, out$ev) }
write.csv(do.call(rbind, P), file.path(dir, sprintf("r_%s_%s_preds.csv", arm, task)), row.names = FALSE); write.csv(do.call(rbind, E), file.path(dir, sprintf("r_%s_%s_evidence.csv", arm, task)), row.names = FALSE)
cat("done", arm, task, "NA preds:", sum(is.na(do.call(rbind, P)$pred)), "\n")
