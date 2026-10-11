# Purpose: <one line: the idea being tried>
# Input:   training patients of one arm, via load_arm(). The test set is not used here.
# Finding: <fill in after running>

# Load the shared code from wherever this file sits.
root <- normalizePath(getwd()); while (!file.exists(file.path(root, "dm1_analysis.R")) && dirname(root) != root) root <- dirname(root)
setwd(root); source("R/common.R")

arm   <- load_arm("Mexiletine")          # "Mexiletine", "Oligonucleotide" or "Tideglusib"
train <- arm$train
y     <- arm$info$outcome                # name of the continuous outcome; arm$info$better says which direction is good

# Example: does one extra idea beat a simple reference, judged by cross-validation inside the training set?
fold <- cv_folds(train)
cv_r2 <- function(formula) {
  pred <- numeric(nrow(train))
  for (k in sort(unique(fold))) pred[fold == k] <- predict(lm(formula, train[fold != k, ]), train[fold == k, ])
  reg_metrics(train[[y]], pred)[["R2"]]
}
cat("Reference (myotonia_severity):          CV R2 =", round(cv_r2(reformulate("myotonia_severity", y)), 3), "\n")
cat("Idea (+ interaction with ctg_repeats):  CV R2 =", round(cv_r2(reformulate("myotonia_severity * log(ctg_repeats)", y)), 3), "\n")
