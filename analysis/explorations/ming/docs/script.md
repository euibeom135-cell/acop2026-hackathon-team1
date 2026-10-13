# Spoken script — DM1 covariate analysis (5-minute pitch)

**Total budget: 4:45 (≤ 5:00) at ~145 wpm (~660 spoken words).** Rehearsal, Mon 12 Oct 2026 — fold 5 pseudo-test; locked fold 1 not opened. Numbers trace to `outputs/report/slide_tables.md`.

*Kept in sync with the built deck's speaker notes (`docs/presentation.html`, NOTES array). The two most-pressable numbers — the Tideglusib **8.3 vs 3.5** enrichment and the Mexiletine **0.29 → 0.54** prevalence — are voiced with their in-sample / on-treatment, prognostic caveats. Slide 5 is the pinch; rehearse against a timer to land ≤ 4:50 with buffer.*

| Slide | Clock | Length |
| --- | --- | --- |
| 1 — The question | 0:00 – 0:30 | 0:30 |
| 2 — Rigor as the method | 0:30 – 1:10 | 0:40 |
| 3 — Split moves scores, not covariates | 1:10 – 1:55 | 0:45 |
| 4 — Signal vs noise | 1:55 – 2:35 | 0:40 |
| 5 — Showcase (Tideglusib) | 2:35 – 3:30 | 0:55 |
| 6 — The other two arms | 3:30 – 4:15 | 0:45 |
| 7 — What this means / close | 4:15 – 4:45 | 0:30 |

---

## Slide 1 — The question  `[0:00 – 0:30]`

Here's the problem. Five hundred simulated DM1 patients, three therapies, eighteen baseline covariates each. For each arm: which baseline covariates predict who responds? On data this size, a single split can hand you a different answer every time. So the real question isn't only *which* covariates predict response — it's which signals are **real**, and which are just the luck of who landed in the test set. That's the whole talk.

## Slide 2 — Rigor as the method  `[0:30 – 1:10]`

Our method is rigor. Fourteen models per task — eight inference methods, from OLS and stepwise through LASSO, elastic net, and a spline GAM, plus six prediction methods: random forest, gradient boosting, SVM, kNN, and an MLP. Gradient boosting is scikit-learn's HistGradientBoosting standing in for XGBoost — same role, no native dependency. Every one is scored on the *exact same* held-out patients — two endpoints, three arms, one pipeline. And the real test set — fold one, 101 patients, hash recorded October 11th — stays sealed until the final run. Everything today is rehearsal.

## Slide 3 — Split moves scores, not covariates  `[1:10 – 1:55]`

Now the honest headline. We reran the whole thing across twenty reseeded splits. The median per-method test-R-squared standard deviation is **0.131** — that's large, so any ranking inside that band is a **tie**, not a winner. The top score swings with the split — Tideglusib runs point-two-six to point-three-five — yet the covariates barely move: across all twenty seeds, Tideglusib cognition is selected **100%**, Oligo CTG repeats **90%**, Mexiletine myotonia **85%**. So we never crown a model — we find the covariate signal that survives.

## Slide 4 — Signal vs noise  `[1:55 – 2:35]`

How do we separate signal from noise? We fixed the bar *before* we looked: a covariate counts as real only if it's stable in at least sixty percent of a hundred half-subsamples **and** beats a shuffled-outcome null. Two signals replicate cleanly on both endpoints — Tideglusib cognition, and Oligonucleotide CTG repeats. And here's the honesty judges should want: Mexiletine's severity trio is stable but sits *inside* the null on the relative target, so we call it suggestive — not real. And one Oligo covariate, insulin_resistance, met the bar on a single fold but failed cross-seed — 17% — so we downgraded it.

## Slide 5 — The showcase: Tideglusib  `[2:35 – 3:30]`

This is the showcase — Tideglusib. Machine learning found it: random forest's twenty-seed mean R-squared is point-four-nine, versus roughly point-two-nine to point-three-six for the linear models — a nonlinearity. The shape is a **step**, not a slope: a high plateau near eight at low baseline cognition, then a four-point cliff, then flat. So we let the data pick one threshold — cognitive function at or below **minus zero-point-five-oh-five** — and that single indicator lifts held-out R-squared from point-two-three to **point-three-eight**, beating even the spline. One fold, so it corroborates the twenty-seed and cross-seed evidence rather than standing alone. Biology explains it: the composite is cognition-weighted, so impaired patients have the most head-room. In-sample the rule enriches mean improvement to **eight-point-three versus three-point-five** — but with **no placebo arm**, that's on-treatment, **prognostic** enrichment to confirm against a control.

## Slide 6 — The other two arms, honestly  `[3:30 – 4:15]`

The other two arms, honestly. Mexiletine: we can't predict improvement magnitude — best R-squared about point-one-nine, CI through zero. But the responder *label* is predictable: stepwise logistic hits ROC-AUC **point-seven-seven**, CI point-five-nine to point-nine-three. And a CTG cut above four-forty-eight roughly doubles responder prevalence, point-two-nine to point-five-four — a prognostic cut to pre-specify, *in-sample over folds 2–5*, not held-out. Oligonucleotide: CTG repeats is a real, stable axis — ninety percent — but per-patient QMT change is unpredictable out of sample, R-squared point-oh-six, CI through zero. So use CTG to **stratify, not predict individuals**. And we flagged a direction surprise for the locked run.

## Slide 7 — What this means / close  `[4:15 – 4:45]`

So what do you walk away with? Three pre-registered enrichment rules. Tideglusib — enroll cognition z below minus zero-point-five: adopted as **prognostic** enrichment, to confirm against a control. Mexiletine — CTG above four-forty-eight, a prognostic cut. Oligonucleotide — CTG to stratify only; no magnitude threshold survived. Every score carries a bootstrap interval; every signal a cross-seed frequency. Nothing rests on one lucky split. Tomorrow the locked fold opens once and refreshes every number. Thank you.
