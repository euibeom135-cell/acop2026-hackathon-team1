# DM1 covariate analysis — 7-slide deck

*Rehearsal, Mon 12 Oct 2026. Every number scores **fold 5** (pseudo-test); the locked **fold 1** (n = 101, sha256 `8b3fb2cb…`, seed 2026) is **not** opened. All numbers trace to `outputs/report/slide_tables.md` and the files it points to.*

---

## 1 · Finding DM1 responders is a covariate problem — and the hard part is telling real signal from a lucky split

- **500 simulated DM1 patients, 3 therapies** (Mexiletine, Oligonucleotide, Tideglusib), **18 baseline covariates** each.
- One question per arm: *which baseline covariates predict who responds?* — asked on **two endpoints**, a continuous improvement score and a binary responder label.
- The trap: on data this size, a single train/test split can crown a different "answer" every time. So the real question is which signals are **real** versus an artifact of who landed in the test set.
- Our claim: ask it the right way and the answer is **reproducible**; trust one leaderboard and it is **misleading**.

**Visual:** `scoreboard_continuous_Mexiletine.png` — 14 methods clustered, bootstrap CIs all overlapping zero: *which of these, if any, is real?*

---

## 2 · Rigor is the method: 14 models × 2 endpoints × 3 arms, every one scored on the same held-out patients through one locked pipeline

- **14 methods per task** — 8 inference (OLS/logistic, stepwise AIC, stepwise BIC, best subset, LASSO, elastic net, ridge, GAM) + 6 prediction (random forest, gradient boosting untuned/tuned, SVM, kNN, MLP).
- Gradient boosting = scikit-learn **HistGradientBoosting**, filling XGBoost's role (no OpenMP runtime here) — same job, fully reproducible (`docs/LOG.md`).
- All 14 scored on the **same held-out rows**, so a score gap is the *method*, not the *sample*.
- The real test set — **fold 1, 101 patients, sha256 `8b3fb2cb…`, hash recorded Oct 11** — opens **exactly once** at the final run (G3). Everything today is rehearsal on fold 5; the discipline was fixed before we looked (`docs/hypothesis_sheet.md`).

**Visual:** `scoreboard_binary_Tideglusib.png` — the second endpoint, 14 methods, overlapping CIs.

---

## 3 · The honest headline: the train/test split moves the scores, not the covariates

- Across **20 reseeded splits**, the median per-method test-R² SD is **0.131** (`outputs/compare/verdict.md`) — any ranking **inside that band is a tie**, not a winner.
- Same arm, different split, the leading R² swings: **Tideglusib +0.26 / +0.30 / +0.35; Mexiletine +0.19 / −0.01 / +0.14** (fold5 / single80 / single75).
- Yet the covariates barely move: across all 20 seeds, **Tideglusib cognition 100%, Oligonucleotide CTG repeats 90%, Mexiletine myotonia 85%**.
- So we never crown a model. We identify the **covariate signal that survives resampling** — that is the reproducible object.

**Visual:** `stability_continuous_Oligonucleotide.png` — CTG repeats selected in ~90% of half-subsamples, above the null.

---

## 4 · A shuffled-outcome null plus stability selection separates real signal from a field of noise

- Pre-registered bar, **fixed before scoring**: a covariate is **"real signal"** only if it is stable in **≥60% of 100 half-subsamples AND beats the 95th percentile of a shuffled-outcome RF null** (`docs/hypothesis_sheet.md`).
- **Replicating real signals:** **Tideglusib cognition** (both endpoints) and **Oligonucleotide CTG repeats** (both endpoints).
- **Honesty on display:** Mexiletine's severity trio (myotonia, CTG, duration) is **stable but inside the RF null** on the relative target → **"suggestive," not real** (`slide_tables.md`, real-signal section).
- **A flag we kept, not hid:** Oligo `insulin_resistance` beats the null on one fold but survives only **17% of cross-seed splits** → **downgraded**, not claimed.

**Visual:** `stability_continuous_Tideglusib.png` — cognition clears the shuffled null; everything else sits inside it.

---

## 5 · Tideglusib is the showcase: ML found a cognition threshold, a one-term rule captures it, and biology explains it

- **ML found it:** random forest's **20-seed mean R² = 0.491** vs **~0.29 (OLS) – 0.36 (LASSO)** for the linear models (`outputs/compare/repeat20_r2.csv`) — a nonlinearity linear fits miss.
- **It's a step, not a slope:** partial dependence holds a high plateau (~8) for low baseline cognition, then **cliffs ~3.7 points** and flattens — a spline GAM (R² 0.119) underfits it.
- **One term captures it:** the data-chosen cut **`1[cognitive_function ≤ −0.505]`** lifts single-term test R² from **+0.233 (linear) to +0.377 (indicator)** (`outputs/stratify/Tideglusib/rule.txt`).
- **Biology explains it:** cognition-weighted composite + GSK-3β target → a head-room/floor effect; **in-sample** the rule enriches mean improvement to **8.28 vs 3.46 (2.4×)** while keeping **~47% (48/102)** of patients — but with **no placebo arm this is on-treatment response, i.e. prognostic enrichment** to confirm against a control (regression-to-the-mean / floor not yet excluded). Marginal rho **−0.647** (q = 4e-16); the pre-registered "step near z ≈ −0.5" landed on **−0.505**.

**Visual:** `pd_Tideglusib.png` — the step centered at −0.505.

---

## 6 · The other two arms, told honestly: Mexiletine's responder label is predictable; Oligonucleotide's repeat axis is real but its magnitude is not

- **Mexiletine — label yes, magnitude no:** the responder *label* is cleanly separable (stepwise logistic **ROC-AUC 0.773, 95% CI 0.587–0.928**) even though relative-improvement *magnitude* is not (best R² ≈ 0.19, CI through 0). The target divides severity back out, so the residual magnitude is weak.
- **Mexiletine enrichment:** **CTG > 448** roughly **doubles responder prevalence, 0.289 → 0.543** on training folds — a **prognostic** cut to pre-specify, not a validated effect-modifier.
- **Oligonucleotide — axis yes, prediction no:** CTG repeats is a **real, stable axis (90% on the continuous endpoint — half-subsample + cross-seed; 76% binary)** but per-patient QMT change is **unpredictable out-of-sample (R² 0.057, CI [−0.29, +0.25])**. Use CTG to **stratify, not predict individuals**.
- **Flag for the locked run:** the Oligo repeat-burden direction is **positive** here (ρ +0.42), **opposite** the mechanistic ceiling prior — pre-specify the sign, confirm on fold 1.

**Visual:** `scoreboard_binary_Mexiletine.png` (label AUC 0.773) + `pd_Oligonucleotide.png` (monotone rise, no exploitable step).

---

## 7 · The deliverable is three pre-registered enrichment rules — and the discipline that makes them trustworthy before the locked run

| Arm | Rule (data-chosen) | Effect (in-sample, on-treatment) | Status |
| --- | --- | --- | --- |
| **Tideglusib** | enroll `cognition z ≤ −0.5` | 8.28 vs 3.46, keeps ~47% | **Adopted (prognostic)** — recovers the forest's gain (+0.377 > +0.233); no placebo → confirm vs control on fold 1 |
| **Mexiletine** | `CTG > 448` | responder prevalence 0.289 → 0.543 | **Prognostic** cut — pre-specify, don't over-claim |
| **Oligonucleotide** | CTG as **stratifier only** | orders patients (2.03 vs 0.38) | **No magnitude threshold** (indicator R² went negative OOS) |

- Nothing in this story rests on a single lucky split: scores carry **bootstrap CIs** and a **20-seed SD (0.131)**; signals carry a **cross-seed frequency**.
- **Next (G3):** open the locked **fold 1** once, confirm hash `8b3fb2cb…`, refresh every number. The rules and the honesty are **already pre-registered**.

**Visual:** `pd_Tideglusib.png` — callback to Slide 5: the one rule we would pre-register today.
