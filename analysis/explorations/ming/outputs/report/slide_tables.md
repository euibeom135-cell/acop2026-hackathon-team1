# Slide tables (numbers traced to pipeline outputs)

*mode: rehearsal — rehearsal scores fold 5; final scores the locked fold 1.*

## Compact models (consensus covariates, scored on held-out test)


### continuous


**Mexiletine**

|   n_terms | terms                                          |       R2 |     RMSE |      MAE |
|----------:|:-----------------------------------------------|---------:|---------:|---------:|
|         1 | ctg_repeats                                    | 0.162773 | 0.142815 | 0.115572 |
|         2 | ctg_repeats+myotonia_severity                  | 0.218727 | 0.13796  | 0.112235 |
|         3 | ctg_repeats+myotonia_severity+disease_duration | 0.24233  | 0.13586  | 0.110628 |

**Oligonucleotide**

|   n_terms | terms                                                |         R2 |    RMSE |     MAE |
|----------:|:-----------------------------------------------------|-----------:|--------:|--------:|
|         1 | ctg_repeats                                          | 0.00159487 | 1.61175 | 1.27668 |
|         2 | ctg_repeats+disease_duration                         | 0.057211   | 1.56621 | 1.26177 |
|         3 | ctg_repeats+disease_duration+somatic_mosaicism_index | 0.0314688  | 1.58745 | 1.2947  |

**Tideglusib**

|   n_terms | terms                                               |       R2 |    RMSE |     MAE |
|----------:|:----------------------------------------------------|---------:|--------:|--------:|
|         1 | cognitive_function                                  | 0.232896 | 2.53843 | 2.21679 |
|         2 | cognitive_function+disease_duration                 | 0.242781 | 2.52203 | 2.29243 |
|         3 | cognitive_function+disease_duration+muscle_strength | 0.215048 | 2.56779 | 2.29088 |

### binary


**Mexiletine**

|   n_terms | terms                                          |   cutoff |   ROC_AUC |   Recall |   Precision |   Accuracy |
|----------:|:-----------------------------------------------|---------:|----------:|---------:|------------:|-----------:|
|         1 | myotonia_severity                              | 0.246562 |  0.781818 |      0.9 |    0.529412 |    0.71875 |
|         2 | myotonia_severity+ctg_repeats                  | 0.239307 |  0.763636 |      0.9 |    0.45     |    0.625   |
|         3 | myotonia_severity+ctg_repeats+disease_duration | 0.257108 |  0.777273 |      0.9 |    0.5      |    0.6875  |

**Oligonucleotide**

|   n_terms | terms                                                |   cutoff |   ROC_AUC |   Recall |   Precision |   Accuracy |
|----------:|:-----------------------------------------------------|---------:|----------:|---------:|------------:|-----------:|
|         1 | ctg_repeats                                          | 0.362548 |  0.725    | 0.714286 |    0.555556 |   0.647059 |
|         2 | ctg_repeats+disease_duration                         | 0.344338 |  0.742857 | 0.714286 |    0.588235 |   0.676471 |
|         3 | ctg_repeats+disease_duration+somatic_mosaicism_index | 0.417293 |  0.75     | 0.642857 |    0.5625   |   0.647059 |

**Tideglusib**

|   n_terms | terms                                         |   cutoff |   ROC_AUC |   Recall |   Precision |   Accuracy |
|----------:|:----------------------------------------------|---------:|----------:|---------:|------------:|-----------:|
|         1 | cognitive_function                            | 0.504295 |  0.731481 | 0.733333 |    0.733333 |   0.757576 |
|         2 | cognitive_function+myotonia_severity          | 0.503021 |  0.681481 | 0.6      |    0.692308 |   0.69697  |
|         3 | cognitive_function+myotonia_severity+ck_level | 0.523724 |  0.714815 | 0.6      |    0.642857 |   0.666667 |


## Full scoreboards


**Mexiletine — continuous**

| method                      | tier       |     R2 |   R2_lo |   R2_hi |
|:----------------------------|:-----------|-------:|--------:|--------:|
| SVM (tuned)                 | prediction |  0.193 |  -0.11  |   0.334 |
| Stepwise AIC                | inference  |  0.19  |  -0.128 |   0.337 |
| OLS all                     | inference  |  0.183 |  -0.118 |   0.369 |
| Elastic net                 | inference  |  0.166 |  -0.043 |   0.239 |
| Stepwise BIC                | inference  |  0.163 |  -0.101 |   0.281 |
| Best subset                 | inference  |  0.163 |  -0.101 |   0.281 |
| Random forest               | prediction |  0.135 |  -0.174 |   0.27  |
| LASSO                       | inference  |  0.13  |  -0.068 |   0.187 |
| Ridge                       | inference  |  0.126 |  -0.09  |   0.191 |
| GAM                         | inference  |  0.122 |  -0.13  |   0.208 |
| kNN (tuned)                 | prediction |  0.101 |  -0.176 |   0.212 |
| Gradient boosting (tuned)   | prediction |  0.055 |  -0.447 |   0.329 |
| MLP (tuned)                 | prediction |  0.036 |  -0.524 |   0.341 |
| Gradient boosting (untuned) | prediction | -0.047 |  -0.678 |   0.277 |

**Oligonucleotide — continuous**

| method                      | tier       |     R2 |   R2_lo |   R2_hi |
|:----------------------------|:-----------|-------:|--------:|--------:|
| Stepwise BIC                | inference  |  0.057 |  -0.29  |   0.253 |
| Best subset                 | inference  |  0.057 |  -0.29  |   0.253 |
| Elastic net                 | inference  |  0.051 |  -0.274 |   0.245 |
| LASSO                       | inference  |  0.048 |  -0.283 |   0.247 |
| Ridge                       | inference  |  0.037 |  -0.228 |   0.195 |
| kNN (tuned)                 | prediction |  0.029 |  -0.26  |   0.215 |
| OLS all                     | inference  |  0.022 |  -0.473 |   0.288 |
| GAM                         | inference  |  0.02  |  -0.301 |   0.207 |
| SVM (tuned)                 | prediction |  0.014 |  -0.247 |   0.141 |
| Stepwise AIC                | inference  | -0.02  |  -0.538 |   0.246 |
| Random forest               | prediction | -0.028 |  -0.417 |   0.238 |
| Gradient boosting (tuned)   | prediction | -0.115 |  -0.62  |   0.173 |
| MLP (tuned)                 | prediction | -0.162 |  -0.668 |   0.15  |
| Gradient boosting (untuned) | prediction | -0.169 |  -0.73  |   0.162 |

**Tideglusib — continuous**

| method                      | tier       |     R2 |   R2_lo |   R2_hi |
|:----------------------------|:-----------|-------:|--------:|--------:|
| Random forest               | prediction |  0.255 |  -0.399 |   0.606 |
| Gradient boosting (tuned)   | prediction |  0.251 |  -0.29  |   0.539 |
| Stepwise BIC                | inference  |  0.17  |  -0.372 |   0.416 |
| Best subset                 | inference  |  0.17  |  -0.372 |   0.416 |
| Gradient boosting (untuned) | prediction |  0.167 |  -0.491 |   0.505 |
| SVM (tuned)                 | prediction |  0.148 |  -0.187 |   0.343 |
| GAM                         | inference  |  0.119 |  -0.28  |   0.363 |
| Stepwise AIC                | inference  |  0.103 |  -0.499 |   0.409 |
| Elastic net                 | inference  |  0.092 |  -0.492 |   0.371 |
| LASSO                       | inference  |  0.09  |  -0.496 |   0.372 |
| Ridge                       | inference  |  0.087 |  -0.438 |   0.336 |
| OLS all                     | inference  | -0.011 |  -0.714 |   0.348 |
| kNN (tuned)                 | prediction | -0.092 |  -0.59  |   0.212 |
| MLP (tuned)                 | prediction | -0.394 |  -1.243 |   0.034 |

**Mexiletine — binary**

| method                      | tier       |   ROC_AUC |   ROC_AUC_lo |   ROC_AUC_hi |
|:----------------------------|:-----------|----------:|-------------:|-------------:|
| Logistic stepwise AIC       | inference  |     0.773 |        0.587 |        0.928 |
| Logistic stepwise BIC       | inference  |     0.773 |        0.587 |        0.928 |
| Logistic best subset        | inference  |     0.773 |        0.587 |        0.928 |
| LASSO logistic              | inference  |     0.755 |        0.564 |        0.907 |
| Random forest               | prediction |     0.752 |        0.555 |        0.917 |
| Ridge logistic              | inference  |     0.75  |        0.567 |        0.902 |
| Elastic net logistic        | inference  |     0.745 |        0.565 |        0.901 |
| SVM (tuned)                 | prediction |     0.723 |        0.55  |        0.879 |
| GAM logistic                | inference  |     0.718 |        0.537 |        0.875 |
| Logistic all                | inference  |     0.705 |        0.514 |        0.875 |
| kNN (tuned)                 | prediction |     0.705 |        0.493 |        0.879 |
| Gradient boosting (tuned)   | prediction |     0.695 |        0.502 |        0.869 |
| Gradient boosting (untuned) | prediction |     0.645 |        0.42  |        0.844 |
| MLP (tuned)                 | prediction |     0.559 |        0.319 |        0.818 |

**Oligonucleotide — binary**

| method                      | tier       |   ROC_AUC |   ROC_AUC_lo |   ROC_AUC_hi |
|:----------------------------|:-----------|----------:|-------------:|-------------:|
| Logistic stepwise AIC       | inference  |     0.764 |        0.601 |        0.919 |
| LASSO logistic              | inference  |     0.754 |        0.583 |        0.913 |
| Logistic stepwise BIC       | inference  |     0.743 |        0.573 |        0.912 |
| Logistic best subset        | inference  |     0.743 |        0.573 |        0.912 |
| Elastic net logistic        | inference  |     0.743 |        0.579 |        0.903 |
| SVM (tuned)                 | prediction |     0.729 |        0.538 |        0.892 |
| kNN (tuned)                 | prediction |     0.721 |        0.547 |        0.882 |
| Logistic all                | inference  |     0.714 |        0.542 |        0.881 |
| Ridge logistic              | inference  |     0.714 |        0.535 |        0.876 |
| GAM logistic                | inference  |     0.654 |        0.453 |        0.836 |
| Random forest               | prediction |     0.648 |        0.454 |        0.835 |
| MLP (tuned)                 | prediction |     0.632 |        0.417 |        0.83  |
| Gradient boosting (untuned) | prediction |     0.621 |        0.431 |        0.816 |
| Gradient boosting (tuned)   | prediction |     0.589 |        0.386 |        0.789 |

**Tideglusib — binary**

| method                      | tier       |   ROC_AUC |   ROC_AUC_lo |   ROC_AUC_hi |
|:----------------------------|:-----------|----------:|-------------:|-------------:|
| Random forest               | prediction |     0.704 |        0.496 |        0.89  |
| Logistic stepwise BIC       | inference  |     0.681 |        0.47  |        0.865 |
| Logistic best subset        | inference  |     0.681 |        0.47  |        0.865 |
| Ridge logistic              | inference  |     0.681 |        0.462 |        0.864 |
| MLP (tuned)                 | prediction |     0.678 |        0.462 |        0.858 |
| LASSO logistic              | inference  |     0.674 |        0.457 |        0.862 |
| GAM logistic                | inference  |     0.674 |        0.467 |        0.867 |
| Gradient boosting (tuned)   | prediction |     0.674 |        0.467 |        0.869 |
| SVM (tuned)                 | prediction |     0.67  |        0.474 |        0.865 |
| Elastic net logistic        | inference  |     0.667 |        0.449 |        0.857 |
| Gradient boosting (untuned) | prediction |     0.659 |        0.456 |        0.856 |
| Logistic stepwise AIC       | inference  |     0.656 |        0.446 |        0.847 |
| Logistic all                | inference  |     0.63  |        0.423 |        0.819 |
| kNN (tuned)                 | prediction |     0.609 |        0.393 |        0.806 |


## Real signal vs noise (stability selection + shuffled null)

- **Mexiletine / continuous**: real = —; suggestive = ['ctg_repeats', 'myotonia_severity', 'disease_duration']
- **Oligonucleotide / continuous**: real = ['ctg_repeats', 'insulin_resistance']; suggestive = ['disease_duration', 'somatic_mosaicism_index']
- **Tideglusib / continuous**: real = ['cognitive_function']; suggestive = ['disease_duration', 'smoking_status', 'insulin_resistance', 'bmi', 'ck_level', 'cataracts', 'ctg_repeats', 'pr_interval', 'albumin', 'somatic_mosaicism_index']
- **Mexiletine / binary**: real = —; suggestive = ['family_history']
- **Oligonucleotide / binary**: real = ['disease_duration', 'ctg_repeats']; suggestive = ['bmi']
- **Tideglusib / binary**: real = ['cognitive_function', 'myotonia_severity', 'somatic_mosaicism_index']; suggestive = ['bmi', 'family_history', 'smoking_status', 'pr_interval', 'age_at_onset', 'insulin_resistance', 'albumin', 'ck_level', 'muscle_strength', 'ctg_repeats', 'disease_duration', 'sex']

> **Cross-seed override (not auto-computed):** a covariate can clear the per-fold real-signal bar above yet fail cross-seed replication. Oligonucleotide `insulin_resistance` (continuous) is such a case (17% cross-seed, non-consensus 0.42 < 0.5, q = 0.075 under FDR) and is **downgraded, not claimed** — the claimed Oligo/continuous signal is `ctg_repeats` only (`docs/interpretation_Oligonucleotide.md` §4). The locked fold-1 run re-evaluates every verdict.


## Stratification rules


**Mexiletine**

```
arm: Mexiletine
leading numeric consensus term: ctg_repeats
data-chosen threshold (depth-1 tree): ctg_repeats > 448.5
enriched subgroup mean improvement: 0.467  (other subgroup: 0.344)
subgroup size in training: 24/96
test R2, single linear term (ctg_repeats): +0.163
test R2, single indicator 1[ctg_repeats > 448]: +0.138
```

**Oligonucleotide**

```
arm: Oligonucleotide
leading numeric consensus term: ctg_repeats
data-chosen threshold (depth-1 tree): ctg_repeats > 346.5
enriched subgroup mean improvement: 2.026  (other subgroup: 0.384)
subgroup size in training: 41/102
test R2, single linear term (ctg_repeats): +0.002
test R2, single indicator 1[ctg_repeats > 346]: -0.071
```

**Tideglusib**

```
arm: Tideglusib
leading numeric consensus term: cognitive_function
data-chosen threshold (depth-1 tree): cognitive_function <= -0.505
enriched subgroup mean improvement: 8.277  (other subgroup: 3.457)
subgroup size in training: 48/102
test R2, single linear term (cognitive_function): +0.233
test R2, single indicator 1[cognitive_function <= -0.505]: +0.377
```


## Split sensitivity

# Split-sensitivity verdict

- Across 20 seeds, the median per-method SD of test R² is **0.131** — rankings inside this band are ties.
  - Mexiletine: R² SD ranges 0.074–0.260 (widest: Gradient boosting (untuned)).
  - Oligonucleotide: R² SD ranges 0.064–0.176 (widest: OLS all).
  - Tideglusib: R² SD ranges 0.093–0.181 (widest: OLS all).

- Cross-seed selection frequency (covariate stability):
  - Mexiletine: myotonia_severity 85%, disease_duration 75%, insulin_resistance 60%, ctg_repeats 56%, sex 42%
  - Oligonucleotide: ctg_repeats 90%, disease_duration 77%, family_history 65%, somatic_mosaicism_index 57%, myotonia_severity 40%
  - Tideglusib: cognitive_function 100%, disease_duration 93%, cataracts 40%, ctg_repeats 28%, muscle_strength 27%

- Leading R² by scheme (same arm, different split):
  - Mexiletine: fold5 +0.19, single80 -0.01, single75 +0.14
  - Oligonucleotide: fold5 +0.06, single80 +0.01, single75 +0.02
  - Tideglusib: fold5 +0.26, single80 +0.30, single75 +0.35

