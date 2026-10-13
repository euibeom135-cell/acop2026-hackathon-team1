"""Step 1 page: Understand (TRAIN-ONLY EDA per arm). No covariate-outcome relationships here (that is selection, Step 4/5)."""
from data import *
from traits import corr, pairs, vif
from scipy import stats

def structure():
    sp = split(); rows = []
    for a in ARMS:
        d = train(a); y, dirn = OUTCOME[a]
        rows.append({"Arm": a, "Train patients": len(d), "Continuous outcome": y, "Better means": dirn, "Responders (train)": f"{int(d.label.sum())} ({d.label.mean():.0%})",
                     "Numeric covariates": len(numcols(a)), "0/1 dummy columns": len(dummies(a))})
    uniq = sp.patient_id.is_unique
    return pd.DataFrame(rows), uniq

def summary_tables():
    cols = list(dict.fromkeys(sum([numcols(a) for a in ARMS], [])))
    A = pd.DataFrame(index=[nice(c) for c in cols]); B = []
    for a in ARMS:
        d = train(a); A[a] = [f"{d[c].mean():.2f} ({d[c].std():.2f})" if c in d else "constant in train: dropped" for c in cols]
        for c in numcols(a):
            x = d[c]; q1, q3 = x.quantile([.25, .75]); iqr = q3 - q1; nout = int(((x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)).sum())
            B.append({"Arm": a, "Covariate": nice(c), "Min": x.min(), "Median": x.median(), "Max": x.max(), "Skew": stats.skew(x), "Outliers (1.5 IQR)": nout})
    return A.reset_index().rename(columns={"index": "Covariate (mean (SD), train)"}), pd.DataFrame(B)

def dummy_table():
    ds = list(dict.fromkeys(sum([dummies(a) for a in ARMS], []))); T = pd.DataFrame({"Column": [nice(c) for c in ds]})
    for a in ARMS: T[a] = [f"{train(a)[c].mean():.0%}" for c in ds]
    return T

def fig_dist(arm):
    d = train(arm); cs = numcols(arm); fig, ax = plt.subplots(3, 4, figsize=(11, 6.2))
    for k, a_ in enumerate(ax.ravel()):
        if k < len(cs): a_.hist(d[cs[k]], bins=18, color=ARMC[arm], alpha=.85); a_.set_title(f"{nice(cs[k])} (skew {stats.skew(d[cs[k]]):.2f})", fontsize=8); a_.tick_params(labelsize=7)
        else: a_.axis("off")
    fig.suptitle(f"{arm}: numeric covariates, train n={len(d)}", fontsize=10); fig.tight_layout(); return fig_html(fig, f"s1_dist_{arm}")

def fig_outcome():
    fig, ax = plt.subplots(1, 3, figsize=(11, 2.8))
    for a_, a in zip(ax, ARMS):
        d = train(a); a_.hist([d.y[d.label == 1], d.y[d.label == 0]], bins=16, stacked=True, color=[ARMC[a], "#bbbbbb"], label=["Responder", "Non-responder"])
        a_.set_title(f"{a}: {OUTCOME[a][0]}", fontsize=8); a_.legend(fontsize=7); a_.tick_params(labelsize=7)
    fig.tight_layout(); return fig_html(fig, "s1_outcome")

def fig_corr():
    fig, ax = plt.subplots(1, 3, figsize=(17, 5.4))
    for a_, a in zip(ax, ARMS):
        c = corr(a); n = len(c); im = a_.imshow(c.values, vmin=-1, vmax=1, cmap="RdBu_r"); a_.set_xticks(range(n)); a_.set_yticks(range(n))
        a_.set_xticklabels([nice(x) for x in c.columns], rotation=90, fontsize=7); a_.set_yticklabels([nice(x) for x in c.columns], fontsize=7); a_.set_title(a, fontsize=10)
        for i in range(n):
            for j in range(n):
                if i != j and abs(c.values[i, j]) >= .3: a_.text(j, i, f"{c.values[i, j]:.1f}", ha="center", va="center", fontsize=6)
    fig.subplots_adjust(wspace=.75)
    fig.colorbar(im, ax=ax, shrink=.7, label="Pearson r"); return fig_html(fig, "s1_corr")

def build():
    S, uniq = structure(); A, B = summary_tables(); D = dummy_table()
    P = []
    for a in ARMS:
        p = pairs(a, .5, numeric_only=False); P += [{"Arm": a, "Pair": f"{nice(x)} / {nice(y)}", "r": r_} for x, y, r_ in p.itertuples(index=False)]
    P = pd.DataFrame(P) if P else pd.DataFrame(columns=["Arm", "Pair", "r"])
    R = req([("Structure: each patient belongs to one arm; the outcome exists only for that arm", f"Arms analysed separately; split file has one row per patient (no patient appears in two arms: {uniq}); each arm's own outcome only", "1.1"),
             ("Distributions: ranges, skew, outliers of the numeric covariates", "Histograms, min/median/max, skew and 1.5-IQR outlier counts per arm (12 numeric columns; the kickoff slide says 13, see 1.2)", "1.3"),
             ("Covariate variation: summarise every covariate within each arm", "Mean (SD) per arm side by side, plus 0/1 dummy prevalences", "1.3"),
             ("Relationships: correlated covariates and class balance of the responder label", "Covariate-covariate correlation heatmap and |r| >= 0.5 pairs; responder share per arm", "1.4"),
             ("Once split, explore the training data only", "Every number and figure here is computed from the TRAIN rows (features_train_*.csv); test rows are never opened", "all")])
    body = f"""{R}<h2>1.1 Structure and outcomes</h2>{tbl(S)}
<p>Each patient is in exactly one treatment arm and has an outcome only for that arm, so the three arms are three separate problems with their own outcome, units and direction of benefit. RMSE and MAE are therefore never compared across arms.</p>
<h3>Which outcome is modelled, and why</h3>
<p>Both outcomes the kickoff names are modelled per arm. The <b>continuous efficacy outcome</b> is the primary target: it keeps all the information, and the kickoff recommends it as the natural first step for the linear methods. The <b>responder label</b> (binary) is modelled in parallel because the kickoff asks for classification metrics; it is a dichotomised version of the same response, so it carries less information. Train outcome distributions, coloured by label:</p>{fig_outcome()}
<h2>1.2 Covariate set (12 numeric columns, not 13)</h2>
<p>The kickoff slide speaks of 13 numeric covariates. Age is dropped because <code>age = age_at_onset + disease_duration</code> holds exactly in the data (verified, max absolute difference 0; see compute_notes), so keeping it would add an exactly collinear column. CTG repeat count enters as log10. That leaves <b>12 numeric columns</b>; in Mexiletine albumin is constant in the train rows and is dropped too (11 numeric). The 0/1 dummies (8 columns) are sex, cataracts, family history (Yes / Unknown), smoking (Former / Current) and phenotype (adult / juvenile onset).</p>
<h2>1.3 Distributions and variation per arm (train)</h2>{tbl(A, dec=2, cap="Mean (SD) per arm")}{tbl(D, cap="Dummy prevalence in train")}
{''.join(fig_dist(a) for a in ARMS)}
<details><summary>Min / median / max, skew and outlier counts per arm</summary>{tbl(B, dec=2)}</details>
{note("Skew ranges from about -0.7 to +1.3 (disease duration is the most right-skewed); the 1.5 IQR rule flags 12-16 values per arm. These are plausible clinical values, so nothing is removed (Step 3).")}
<h2>1.4 Relationships among covariates and class balance</h2>{fig_corr()}
{tbl(P, dec=2, cap="Pairs with |r| >= 0.5 across the full design (numeric + dummy columns), train") if len(P) else note("No pair of covariates reaches |r| &gt;= 0.5 in any arm.")}
{tbl(S[["Arm", "Train patients", "Responders (train)"]], cap="Responder-label class balance (train)")}
{note("Collinearity is real: log10 CTG and myotonia severity correlate at r = 0.84-0.90 in every arm, and disease duration with muscle strength at r = -0.76 to -0.79. Class balance: responders are the minority in every arm (29%, 41%, 48%); this is why Step 6 pairs accuracy with recall and precision. No covariate-outcome relationships are shown on this page: that would be selection, which belongs to Steps 4-5.")}"""
    return page(0, "Understand the data (train only)", "Explore structure, distributions, correlations and class balance on the <b>training rows only</b>, before any model is chosen.", body)
