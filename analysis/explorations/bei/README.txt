DM1 COVARIATE CORRELATIONS BY TREATMENT ARM
ACoP 2026 hackathon, simulated data. Analysis date: 11 October 2026.

Scope
-----
All 18 baseline covariates are assessed. Numeric baseline correlations are
reported for pooled training patients and separately for each treatment arm.
Covariate-outcome associations use each arm's own continuous endpoint.
Categorical predictors remain nominal; no arbitrary numeric level coding.
No predictive model has been fit or evaluated in this analysis.

Analysis population
-------------------
The supplied dataset has 500 simulated patients: Mexiletine 161,
Oligonucleotide 170, Tideglusib 169. Following kickoff guidance, a fixed 80/20
split was made independently within each arm using sklearn train_test_split,
stratified on the assigned arm's responder label with random_state=20261011.
Training sizes: 128, 136, 135 (399 total). Reserved test sizes: 33, 34, 34
(101 total). All correlations, group comparisons, confidence intervals,
covariate summaries and figures use training patients only. Full-sample
checks are limited to identifiers, completeness, endpoint structure and the
age/duration identity. No test-set outcome statistics or model scores were
computed. The patient partition CSV is authoritative for downstream work.

Endpoint direction
------------------
Mexiletine improvement_score = -myotonia_change_12wk.
Oligonucleotide improvement_score = qmt_change_26wk.
Tideglusib improvement_score = tideglusib_composite.
Higher improvement_score therefore always means more improvement, while
the original units and outcome scales still differ across arms. The outcome
table provides Spearman correlations for both original and oriented outcomes.

Methods
-------
Numeric predictor/outcome associations: Spearman rank correlation (primary),
Pearson correlation (linear sensitivity analysis), and 95% percentile
bootstrap intervals for Spearman rho using 2,000 patient resamples. Bootstrap
intervals are exploratory, pointwise and not multiplicity adjusted.

Categorical predictor/outcome associations: Kruskal-Wallis H and an adjusted
eta-squared (H) rank effect size:
    eta2_H = max(0, (H - k + 1)/(n - k)).
Here k is the number of observed groups and n the number of training patients.
This unsigned effect size cannot be compared directly to a signed rho.
Definition follows rstatix kruskal_effsize documentation:
https://rpkgs.datanovia.com/rstatix/reference/kruskal_effsize.html

Primary outcome p-values are adjusted jointly across all evaluable numeric
and categorical predictors within each arm using Benjamini-Hochberg FDR.
Mexiletine has 17 evaluable predictors because albumin is constant. The other
arms each have 18. The additional Q_all_evaluable column adjusts across all
53 evaluable arm/covariate tests. FDR_0_05 refers to within-arm q < 0.05.
Pearson sensitivity p-values are not used for the primary FDR screen.

Numeric baseline/baseline associations: Spearman and Pearson for all 78
unique numeric pairs in each cohort. Spearman FDR adjustment is within each
cohort, excluding undefined constant-variable pairs.

Mixed baseline associations: Kruskal-Wallis eta-squared (H) for categorical
versus numeric predictors. Categorical/categorical associations use ordinary,
uncorrected Cramer's V and asymptotic Pearson chi-square p-values (without
Yates correction). FDR is within cohort and association type. Minimum expected
cell counts are supplied for assessment of sparse contingency tables.

Source-data checks and limitations
---------------------------------
No baseline covariate values are missing. Blanks in nonassigned-arm outcome
and responder columns are structural and are never imputed. Albumin is
4.18 g/dL for every Mexiletine patient. Undefined correlations and effect
sizes remain NA, rather than zero. Disease duration equals age minus age at
onset in all 500 source rows, so all three unrestricted linear terms cannot
be estimated together.

Baseline CTG repeats and myotonia severity are strongly correlated within
arms. Age and age at onset are also strongly correlated. Multiple marginal
signals can therefore reflect shared biology or correlated surrogate
variables. A joint model and training-only cross-validation are needed to
establish independent predictive value. Simple correlations may miss
nonlinear effects and interactions.

The data dictionary states that arm assignment was a weighted random draw
informed by each patient's relative fit, rather than uniform randomization.
These arm-specific associations do not establish causal treatment-effect
modifiers or enable a direct efficacy ranking of the therapies.

Files
-----
code/analyze_dm1.py: calculations and reproducible split.
code/plot_dm1.py: all scientific figures and the report.
code/build_workbook.mjs: original workbook builder using @oai/artifact-tool.
inputs/: unchanged supplied CSV and data dictionary.
results/tables/: all numeric results, mixed results, summaries and partitions.
results/analysis_metadata.json: source hash, definitions and dependency versions.
results/analysis_results.json: machine-readable values behind the workbook.
figures/: individual plots in PNG, SVG and vector PDF formats.
work/dictionary.json: dictionary extraction used by the workbook builder.

Reproduce calculations and figures
----------------------------------
From the package directory, with Python packages numpy, pandas, scipy,
scikit-learn, matplotlib, reportlab and pypdf available:

    python code/analyze_dm1.py --input inputs/dm1_clinical_trial_dataset.csv --out results
    python code/plot_dm1.py --out results

The saved metadata records exact versions used. Existing saved patient
partitions can be reused when combining this analysis with other methods.
The JavaScript workbook builder requires @oai/artifact-tool, supplied in the
ChatGPT/Codex artifact runtime. Its command accepts project root and results
directory as positional arguments:

    node code/build_workbook.mjs /absolute/package/path /absolute/package/path/results

The statistical results in Excel are snapshots of the Python analysis.
Sample-count formulas recalculate from delivered patient tables. Rerun the
Python calculations and workbook builder to refresh statistical results.

Sources and AI disclosure
-------------------------
dm1_clinical_trial_dataset.csv; DM1_Data_Dictionary_Participant.xlsx;
Kick-offSession_final_participants.pdf, especially pages 39, 41, 44-46.
The source materials explicitly describe simulated patients and treatments.
Analysis code and report preparation used ChatGPT/Codex assistance. Numerical
results were checked against independent rank calculations and SciPy's BH
implementation. This disclosure can be adapted for the hackathon submission.
