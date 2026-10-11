# Shared foundation for the main analysis and for every exploration. Source this file; do not copy it.
# It reads and cleans the dataset and makes the one train/test split that everyone uses, so that
# results from different people (and different AI assistants) are comparable.
#
# In an exploration:   arm <- load_arm("Mexiletine")      # training patients only
# The test set is locked. Only dm1_analysis.R asks for it, once, at the end.

SEED <- 20261011

# Find the analysis folder from wherever the calling script is run.
ANALYSIS_DIR <- local({ d <- normalizePath(getwd())
  repeat { if (file.exists(file.path(d, "dm1_analysis.R"))) break
           if (file.exists(file.path(d, "analysis", "dm1_analysis.R"))) { d <- file.path(d, "analysis"); break }
           if (dirname(d) == d) stop("Run from inside the repository."); d <- dirname(d) }
  d })

# ---- Data ----
f <- Sys.getenv("DM1_DATA")
if (!nzchar(f)) {
  f <- list.files(file.path(ANALYSIS_DIR, "data"), pattern = "\\.(xlsx|csv)$", full.names = TRUE, ignore.case = TRUE)
  f <- f[grepl("dm1", basename(f), ignore.case = TRUE) & !grepl("dictionary|mock", basename(f), ignore.case = TRUE)][1]
}
if (is.na(f)) stop("Put the hackathon dataset (DM1*.xlsx or .csv) in analysis/data/")
raw <- if (grepl("\\.csv$", f, ignore.case = TRUE)) read.csv(f) else as.data.frame(readxl::read_excel(f))
names(raw) <- tolower(names(raw))

num_cov <- c("ctg_repeats", "somatic_mosaicism_index", "age", "age_at_onset", "disease_duration",
             "myotonia_severity", "muscle_strength", "pr_interval", "cognitive_function",
             "ck_level", "insulin_resistance", "albumin", "bmi")
cat_cov <- c("phenotype", "sex", "family_history", "cataracts", "smoking_status")
covs    <- c(num_cov, cat_cov)
stopifnot("Covariate names differ from the kickoff slides; edit num_cov / cat_cov" = all(covs %in% names(raw)))
lab <- grep("^responder", names(raw), value = TRUE)
arms <- data.frame(
  name    = c("Mexiletine", "Oligonucleotide", "Tideglusib"),
  outcome = c("myotonia_change_12wk", "qmt_change_26wk", "tideglusib_composite"),
  label   = c(grep("mex", lab, value = TRUE), grep("oligo", lab, value = TRUE), grep("tid", lab, value = TRUE)),
  better  = c("lower", "higher", "higher"))

# ---- Data checks and cleaning ----
# Only two things are fixed automatically, because they cannot change a real value: stray spaces
# and inconsistent capitalisation in category labels, and exact duplicate rows. Everything else
# is reported for the team to decide on, and each decision should be written here as code.
qc <- character(); note <- function(...) qc <<- c(qc, sprintf(...))
for (v in c(cat_cov, lab)) {
  x <- trimws(as.character(raw[[v]])); key <- tolower(gsub("[ _-]+", "_", x))
  canon <- tapply(x, key, function(z) names(which.max(table(z))))      # most common spelling wins
  if (any(x != canon[key], na.rm = TRUE) || any(x != as.character(raw[[v]]), na.rm = TRUE))
    note("FIXED  %s: unified label spellings (%s)", v, paste(unique(raw[[v]][!is.na(x) & as.character(raw[[v]]) != canon[key]]), collapse = ", "))
  raw[[v]] <- ifelse(is.na(x), NA, canon[key])
}
dup <- duplicated(raw[setdiff(names(raw), names(raw)[1])])
if (any(dup)) { note("FIXED  removed %d exact duplicate rows", sum(dup)); raw <- raw[!dup, ] }
for (v in c(num_cov, arms$outcome)) if (!is.numeric(raw[[v]])) {
  bad <- unique(raw[[v]][is.na(suppressWarnings(as.numeric(raw[[v]]))) & !is.na(raw[[v]])])
  note("CHECK  %s is stored as text; non-numeric entries: %s", v, paste(head(bad, 8), collapse = ", ")); raw[[v]] <- suppressWarnings(as.numeric(raw[[v]])) }
nmiss <- colSums(is.na(raw[covs])); if (any(nmiss > 0)) note("CHECK  missing values: %s", paste(sprintf("%s (%d)", names(nmiss)[nmiss > 0], nmiss[nmiss > 0]), collapse = ", "))
for (v in num_cov) { x <- raw[[v]]; q <- quantile(x, c(.25, .75), na.rm = TRUE); out <- which(x < q[1] - 3 * diff(q) | x > q[2] + 3 * diff(q))
  if (length(out)) note("CHECK  %s: %d extreme values (beyond 3 IQR), e.g. %s; range %s to %s", v, length(out), paste(head(signif(x[out], 4), 5), collapse = ", "), signif(min(x, na.rm = TRUE), 4), signif(max(x, na.rm = TRUE), 4))
  if (any(x < 0, na.rm = TRUE) && v != "cognitive_function") note("CHECK  %s: %d negative values", v, sum(x < 0, na.rm = TRUE))   # cognitive_function is a z-score
  for (edge in range(x, na.rm = TRUE)) if (mean(x == edge, na.rm = TRUE) > 0.10)
    note("CHECK  %s: %.0f%% of patients sit exactly at %s (a floor, ceiling or detection limit)", v, 100 * mean(x == edge, na.rm = TRUE), signif(edge, 4)) }
arm_col <- intersect(c("treatment_arm", "arm", "treatment"), names(raw))[1]
if (!is.na(arm_col)) for (v in covs) for (g in unique(raw[[arm_col]])) if (length(unique(raw[[v]][raw[[arm_col]] == g])) < 2)
  note("CHECK  %s has a single value (%s) for every %s patient: no information in that arm; dropped there", v, raw[[v]][raw[[arm_col]] == g][1], g)
if (any(raw$age_at_onset > raw$age, na.rm = TRUE)) note("CHECK  %d patients have onset after current age", sum(raw$age_at_onset > raw$age, na.rm = TRUE))
gap <- abs(raw$age - raw$age_at_onset - raw$disease_duration)
if (any(gap > 1, na.rm = TRUE)) note("CHECK  %d patients where age - age_at_onset differs from disease_duration by more than 1 year", sum(gap > 1, na.rm = TRUE))
nout <- rowSums(!is.na(raw[arms$outcome])); if (any(nout != 1)) note("CHECK  %d patients do not have exactly one arm outcome", sum(nout != 1))
for (a in seq_len(nrow(arms))) { has <- !is.na(raw[[arms$outcome[a]]])
  if (any(has & is.na(raw[[arms$label[a]]]))) note("CHECK  %s: %d patients with an outcome but no responder label", arms$name[a], sum(has & is.na(raw[[arms$label[a]]]))) }
if (!length(qc)) qc <- "No issues found by the automatic checks."


# Team cleaning decisions go here, one line each with the reason, e.g.
# raw <- raw[raw$age_at_onset <= raw$age, ]          # onset after current age is impossible

for (v in cat_cov) raw[[v]] <- factor(raw[[v]])

# ---- Small helpers ----
is_resp <- function(x) { x <- tolower(as.character(x)); as.integer(x %in% c("1", "true", "yes") | grepl("^resp", x)) }
auc <- function(y, p) { r <- rank(p); n1 <- sum(y == 1); n0 <- sum(y == 0); (sum(r[y == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0) }
reg_metrics <- function(y, p) c(RMSE = sqrt(mean((y - p)^2)), MAE = mean(abs(y - p)), R2 = 1 - sum((y - p)^2) / sum((y - mean(y))^2))
cls_metrics <- function(y, p, cut = 0.5) { h <- as.integer(p >= cut)
  c(AUC = auc(y, p), Recall = sum(h & y) / sum(y), Precision = if (sum(h)) sum(h & y) / sum(h) else NA, Accuracy = mean(h == y)) }
# Median / most-frequent imputation learned on training data (no effect if nothing is missing).
impute <- function(df, ref) { for (v in names(df)) if (anyNA(df[[v]]))
  df[[v]][is.na(df[[v]])] <- if (is.numeric(ref[[v]])) median(ref[[v]], na.rm = TRUE) else names(which.max(table(ref[[v]])))
  df }
# ---- The split: one per arm, made here and nowhere else ----
# 75/25, fixed seed, stratified by responder label and onset phenotype. Imputation (if any value
# were missing) is learned from the training patients. By default only the training set is returned.
load_arm <- function(name, include_test = FALSE) {
  a <- match(name, arms$name); if (is.na(a)) stop("Arm must be one of: ", paste(arms$name, collapse = ", "))
  A <- arms[a, ]
  d <- raw[!is.na(raw[[A$outcome]]), ]
  d$.resp <- is_resp(d[[A$label]])
  set.seed(SEED + a)
  test_id <- unlist(lapply(split(seq_len(nrow(d)), interaction(d$.resp, d$phenotype, drop = TRUE)),
                           function(i) sample(i, round(0.25 * length(i)))))
  tr <- d[-test_id, ]; te <- d[test_id, ]
  tr[covs] <- impute(tr[covs], tr[covs]); te[covs] <- impute(te[covs], tr[covs])
  # Covariates that do not vary among this arm's training patients cannot predict anything there.
  varies <- covs[sapply(tr[covs], function(x) length(unique(x)) > 1)]
  out <- list(info = A, train = tr, covs = varies, dropped = setdiff(covs, varies))
  if (include_test) out$test <- te
  out
}

# Cross-validation folds inside the training set, for comparing ideas without touching the test set.
cv_folds <- function(train, k = 5) { set.seed(SEED)
  f <- integer(nrow(train)); for (g in split(seq_len(nrow(train)), train$.resp)) f[g] <- sample(rep(seq_len(k), length.out = length(g))); f }
