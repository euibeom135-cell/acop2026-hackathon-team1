# DM1 hackathon: agentic workflow and orchestration plan

*Drafted Monday, October 12, 2026. Covers the deck's six-step pipeline (understand → split → preprocess → select → train → evaluate), the per-arm scoreboards and covariate-agreement tables the judges ask for, and the "genuine innovation" criteria: mechanism, stratification, decision-relevant visuals.*

## 1. What the workflow has to produce

| Judges' ask (deck) | Artifact | Produced by |
| --- | --- | --- |
| Explore before modeling | `docs/data_report.html` (done Oct 11), `docs/DM1_Covariate_Dictionary_and_Correlations.pdf` | data-steward |
| Split once per arm, stratified, seeded, locked | `data/folds_5fold_seed2026.csv`, `outputs/splits/*.csv`, hash in `summary.json` | split-designer |
| All listed methods, covariate and ML, same test patients | `outputs/runs/<task>/<scheme>/.../scoreboard.csv` | covariate-modeler + ml-modeler (one runner) |
| One scoreboard per arm, untuned and tuned rows, bootstrap intervals | `outputs/report/results_report.html`, `slide_tables.md` | scoreboard-builder |
| Compare the covariates, not only the scores | agreement matrix, `consensus.csv`, `selection_frequency.csv` | stability-auditor |
| Separate real signal from noise | `stability.csv` (stability selection + shuffled-outcome null), verdicts | stability-auditor |
| Mechanism, stratification, trial-design implication | `docs/interpretation_<arm>.md`, `outputs/stratify/*/rule.txt`, `compact_scoreboard.csv` | biologist + scoreboard-builder |
| Clear, decision-relevant visuals | 7-slide deck, script, Q&A sheet | communicator |

Primary analysis: the **continuous** outcome per arm (R², RMSE, MAE); for mexiletine the *relative* change, because the 45 % responder rule is built on it and absolute change is trivially explained by baseline severity. Secondary: the **binary** responder label (ROC-AUC, recall, precision, accuracy) with cutoffs chosen on training out-of-fold predictions.

## 2. The agents and the DAG

```
                 ┌────────────────┐
                 │  data-steward  │  (done; re-runs only if data changes)
                 └───────┬────────┘
                         ▼
                 ┌────────────────┐
                 │ split-designer │  02_make_splits.py  → outputs/splits/
                 └───────┬────────┘
                         ▼
          ┌──────────────┴──────────────┐
          ▼                             ▼
 ┌─────────────────┐           ┌─────────────────┐
 │covariate-modeler│           │   ml-modeler    │   one runner: 03_run_models.py (continuous, then binary)
 └────────┬────────┘           └────────┬────────┘   agents split the *reading*, not the compute
          └──────────────┬──────────────┘
                         ▼
               ┌───────────────────┐
               │ stability-auditor │  05_stability.py, 03 on repeat20/single80/single75, 06_compare_splits.py
               └─────────┬─────────┘
          ┌──────────────┴──────────────┐
          ▼                             ▼
 ┌─────────────────┐           ┌─────────────────┐
 │    biologist    │ ◄───────► │scoreboard-builder│  08_compact_and_stratify.py, 07_build_report.py, slide_tables.md
 └────────┬────────┘           └────────┬────────┘
          └──────────────┬──────────────┘
                         ▼
                 ┌────────────────┐
                 │  communicator  │  deck, script, Q&A
                 └────────────────┘
```

Each agent is a Claude Code subagent in `.claude/agents/<name>.md` with its commands, inputs, outputs, rules and done-criteria. The orchestrator (the main session, briefed by `CLAUDE.md`) delegates, holds the gates, and keeps `docs/LOG.md`. Humans map onto the same roles: whoever owns the biology on the team *is* the biologist agent's reviewer, and so on.

## 3. Gates (human decisions, in order)

| Gate | Decision | Who | When |
| --- | --- | --- | --- |
| G1 | Ratify the six data decisions (albumin, age, collinear axis, mexiletine target, locked partition, family_history/cataracts adjudication) | whole team | done Oct 11 / confirm Mon AM |
| G2 | Accept the rehearsal results: method list final, consensus covariates per arm, compact models, stratification rules; freeze `config.py` | team lead | Mon evening |
| G3 | Flip `MODE = 'final'`; one person runs `bash run_all.sh final` once; hash of fold 1 confirmed against the Oct 11 record | test-set custodian | Tue morning |
| G4 | Slides: assertion titles, numbers traced to `slide_tables.md`, timed read-through under 5:00 | team | Tue evening, before 11:59 PM ET |

Between G2 and G3 the slides are drafted on rehearsal numbers; at G3 only the numbers change. This is what makes a Tuesday-night deadline safe.

## 4. Splitting strategy and the question "does the split matter on a dataset this small?"

**Design.** Per arm, one stratified 5-fold partition (seed 2026; strata = responder label × within-label median of the continuous outcome, so both regression and classification views are balanced). Fold 1 is the locked test (33/34/34 patients), scored once at the end. Folds 2–5 are the training set; inside it, 5×3 repeated CV does tuning, stepwise scoring, cutoff choice and stability selection. **Rehearsal mode** (fold 5 as pseudo-test, folds 2–4 as training) lets the whole pipeline, the interpretation and the slide drafts be built without ever opening fold 1.

**Sensitivity schemes**, each written to its own manifest: `single80` and `single75` (the classic one-shot splits, seed 2026) and `repeat20` (20 seeds). Every scheme runs through the same runner, so the comparison is apples to apples.

**The honest answer.** It matters for the *scores* and barely for the *covariates*, and the pipeline measures both:

- With 33 test patients, a test R² has a bootstrap interval of roughly ±0.2 and one patient moves recall by about 10 points; across the 20 repeated splits the SD of a method's test R² is on the order of 0.1. Rankings of methods inside that band are noise; the scoreboard must present them as ties.
- Which covariates are selected is driven by the \~130 training patients, not the 33 held out; in rehearsal the three dominant drivers (baseline myotonia; repeat length; baseline cognition) and disease duration were selected in essentially every resample, while the weak candidates (BMI, muscle strength in tideglusib, the repeats × strength interaction) flipped between p = 0.02 and p = 0.6 with a 20 % change of training rows. That is the argument for stability selection rather than for a cleverer split.
- 80/20 vs 75/25 is a judgment call with a small, real trade-off (about 12 vs 9 test responders in the mexiletine arm, against \~8 fewer training patients). `repeat20` answers whether it changes any conclusion; the agent reports that number instead of arguing the preference.

The slide sentence, if rehearsal holds in the final run: *"Which 33 patients are held out moves the scores; it does not move the covariates."*

## 5. Methods and how they are compared

Fourteen methods per task, all behind one interface (`pipeline/models.py`), all scored on the same test rows:

| Tier | Continuous | Binary | What it contributes |
| --- | --- | --- | --- |
| Inference | OLS all; stepwise AIC; stepwise BIC; best subset (BIC, ≤5 terms); LASSO; elastic net; ridge; GAM | logistic equivalents | the covariate lists, signs, shapes (GAM) |
| Prediction | random forest; XGBoost untuned; XGBoost tuned; SVM tuned; kNN tuned; small MLP tuned | classifier equivalents | the ceiling, importance ranking, non-linearity and interactions |
| Bridge | stability selection (fixed penalty path, 100 half-subsamples); shuffled-outcome null (RF importance, 50 permutations); cross-method agreement; cross-seed selection frequency | same | the "real signal vs noise" verdicts |

Every method yields the same selection record: kept terms (covariate methods) or top-5 permutation importance on the test rows (ML), plus standardized coefficients and SHAP where meaningful. Categorical covariates are permuted as a block, so `phenotype` is one term, not two dummies.

**The mix step** (`08_compact_and_stratify.py`): the consensus covariates go into a 2–3-term model, with a data-chosen threshold on the top term when the random-forest partial dependence bends. In rehearsal this is where the story lives: tideglusib's cognition effect is a step near z = −0.5; the forest reached R² 0.54 where linear models reached 0.25, and a single indicator *1\[cognition ≤ −0.48\]* matched the forest. "ML found it; a one-term rule captures it; the biology explains it; here is the enrichment rule" is the arc the innovation criteria describe.

## 6. Timeline

| When | Work | Agents |
| --- | --- | --- |
| Mon Oct 12, morning | `bash run_all.sh rehearsal` (≈45 min of compute); covariate and ML modelers read the headline outputs | split-designer, covariate-modeler, ml-modeler |
| Mon afternoon | stability + split sensitivity + compare; compact models + rules; first report | stability-auditor, scoreboard-builder |
| Mon evening | interpretation paragraphs; prior-vs-data table; G2 freeze | biologist, team |
| Tue Oct 13, morning | G3: final run, once; report and slide tables regenerate | custodian, scoreboard-builder |
| Tue afternoon | deck, script, Q\&A; timed read-through; G4 | communicator, team |
| Tue 11:59 PM ET | submit slides + code (`pipeline/`, `outputs/report/`, `docs/`) | orchestrator |
| Wed Oct 14, 9:00 AM | 5-minute talk | presenter |

## 7. Compute budget (one laptop, 4 cores)

Headline continuous + binary, all 14 methods, 3 arms (4 arm-targets): \~15 min. Stability (3 arm-targets × \~4 min): \~12 min. `repeat20` cheap methods (20 × 4 × \~25 s): \~35 min; run it in the background while people read. `single80`/`single75`: \~6 min. Everything is restartable at the script boundary and nothing downstream needs more than the CSVs.

## 8. What goes in the submission

`pipeline/` (code), `data/folds_5fold_seed2026.csv` (the split), `outputs/report/results_report.html` and `slide_tables.md`, `outputs/compare/`, `outputs/stability/`, `outputs/stratify/`, `docs/hypothesis_sheet.md` (pre-registration, dated), `docs/data_report.html`, `docs/interpretation_*.md`, the deck, the script, the Q&A sheet, `docs/LOG.md`.