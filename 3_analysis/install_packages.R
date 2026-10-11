# One-off install of the packages dm1_analysis.R needs. Run once: Rscript install_packages.R
pkgs <- c("readxl", "dplyr", "tidyr", "ggplot2", "glmnet", "MASS", "ranger", "xgboost",
          "Boruta", "shapviz", "rpart", "rpart.plot")
miss <- setdiff(pkgs, rownames(installed.packages()))
if (length(miss)) install.packages(miss, repos = "https://cloud.r-project.org") else cat("All packages already installed.\n")
