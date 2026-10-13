# Presenter checklist — DM1 covariate analysis

*Rehearsal, Mon 12 Oct 2026 · fold 5 pseudo-test · locked fold 1 NOT opened. All numbers trace to `outputs/report/slide_tables.md`.*

## Before you start (60 seconds)
- [ ] Open **`docs/presentation.html`** in Chrome/Safari (double-click; it is fully self-contained — all 7 figures are embedded, works offline).
- [ ] Press **F** → fullscreen. Press **N** → toggle speaker notes (per-slide script + pace cue appears at the bottom).
- [ ] Navigate with **→ / Space** (next), **← ** (prev), **Home/End** (first/last). Counter is bottom-right ("1 / 8").
- [ ] Have a timer visible. **Target 4:45, hard cap 5:00.** Pace **~145 wpm**; 667 spoken words ≈ 4:36 + transitions.
- [ ] PDF backup: `docs/presentation.pdf` (if present) or **Cmd/Ctrl-P → Save as PDF** (prints one slide per page).
- [ ] One-line thesis to open and close on: **"the split moves the scores, not the covariates."**

## Per-slide: timing cue + the one number to nail

| # | Slide | Clock (end-by) | The ONE thing to land |
| --- | --- | --- | --- |
| 1 | The question | **0:30** | Setup: 500 patients × 3 arms × **18 covariates**, 2 endpoints — then the trap (one split lies). |
| 2 | Rigor as the method | **1:10** | **14 models** scored on the *same* held-out rows; fold 1 sealed until the final run. |
| 3 | Split moves scores | **1:55** | **0.131** = median per-method R² SD across 20 seeds → anything inside that band is a **tie**. Covariates hold: cognition **100%**, CTG **90%**, myotonia **85%**. |
| 4 | Signal vs noise | **2:35** | Pre-registered bar: **≥60% stable AND beats the shuffled null**. Honesty: insulin_resistance cleared on one fold but **17%** cross-seed → downgraded. |
| 5 | Showcase (Tideglusib) | **3:30** *(pinch — keep brisk)* | Step at **−0.505**: indicator **+0.377 > +0.233** linear, OOS. Enrichment **8.28 vs 3.46 (2.4×)** — SAY **"in-sample, on-treatment, no placebo → prognostic, confirm vs control."** |
| 6 | The other two arms | **4:15** | Mexiletine label **AUC 0.773** (CI 0.587–0.928) clears 0.5; Oligo magnitude **R² 0.057** (CI through 0) → stratify, don't predict. CTG direction flipped → flagged. |
| 7 | Deliverable / close | **4:45** | Three pre-registered rules; Tideglusib adopted **as prognostic**. Every score has a CI; every signal a cross-seed frequency. Fold 1 opens tomorrow. |

> If you are behind at the end of slide 5, drop the number-asides on slide 6 (keep AUC 0.773 and "stratify not predict"); never cut the fold-1 close.

## Top 3 anticipated questions (one-line answers)

1. **Is the Tideglusib result predictive, or just regression-to-the-mean / head-room?** (qa.md Q13)
   Concede the composite is cognition-weighted so impaired patients have head-room — but it is a **step, not a slope** (indicator beats linear *and* the spline OOS; a ~4-pt PD cliff; cognition selected 100%/20 seeds), which pure RTM would not produce. It is **prognostic** (no placebo arm = on-treatment response); confirm on fold 1 and ultimately **against a control arm**.

2. **You call rankings "ties," yet random forest is your hero — contradiction?** (qa.md Q2)
   On one fold it *is* a tie (RF R² 0.255, CI −0.40–0.61). The non-tie evidence is the **20-seed mean R² 0.491 vs 0.29–0.36** linear and a one-term step beating the linear term **OOS by +0.144**. The claim is the **nonlinearity/threshold**, not a leaderboard position.

3. **How do you know this isn't p-hacking / data-dredging?** (qa.md Q9)
   Everything decision-relevant was **pre-registered before scoring** (endpoints, 14 methods, the real-signal rule, stratification rules; `docs/hypothesis_sheet.md`). The **shuffled-outcome null is the dredging control** — e.g. Mexiletine's severity trio is stable yet inside the null, so we **decline to claim it**.

*Also prep (likely follow-ups): Q10 trial savings (3.46→8.28, ~5–6× ceiling — hedged: no placebo, ~33 pts, fold 1 sealed); Q4 Oligo direction flip (flagged surprise, pre-specify the sign); Q5 gradient boosting = HistGradientBoosting standing in for XGBoost.*
