"""Step 5 page: Train (fit + tune on TRAIN only). One compact table per track per outcome type + CV scoreboard figure + retained terms. Train CV only; no test number appears here."""
from data import *

WATCH = {
 "lm / glm (all covariates)": "Assumes linear effects; sensitive to outliers; will not capture non-linear effects.",
 "Stepwise both (BIC)": "Unstable: a slightly different dataset can select a very different set; do not treat the final model as the truth.",
 "Best subset (leaps, BIC, nvmax=10)": "Costly beyond about 20-25 covariates; choose by BIC, not R2.",
 "Ridge (glmnet)": "Needs CV for lambda; keeps every covariate (shrunk, never zero).",
 "LASSO (glmnet, lambda.min)": "Can arbitrarily drop one of two highly correlated covariates; important variables may vanish.",
 "Elastic net (glmnet, alpha=.5)": "Needs CV for lambda; mixes the ridge and LASSO behaviour.",
 "GAM (mgcv, s(k=5), REML, select)": "Harder to interpret; k too small misses patterns, too large overfits.",
 "PCR (prcomp, k by 5-fold CV)": "Components are hard to interpret clinically; PCA is unsupervised.",
 "Mean only": "Reference: predicts the training mean for everyone.", "Prevalence only": "Reference: predicts the training responder share (AUC 0.5)."}
SET = {
 "lm / glm (all covariates)": "lm (continuous) / binomial glm (label), all columns",
 "Stepwise both (BIC)": "MASS::stepAIC, direction both, penalty log(n)", "Best subset (leaps, BIC, nvmax=10)": "leaps::regsubsets, exhaustive, nvmax 10, lowest BIC (continuous only)",
 "Ridge (glmnet)": "glmnet alpha=0, lambda by 10-fold CV", "LASSO (glmnet, lambda.min)": "glmnet alpha=1, lambda.min by 10-fold CV", "Elastic net (glmnet, alpha=.5)": "glmnet alpha=0.5, lambda.min by 10-fold CV",
 "GAM (mgcv, s(k=5), REML, select)": "mgcv: s(x, k=5) per numeric covariate, dummies linear, REML, select=TRUE", "PCR (prcomp, k by 5-fold CV)": "prcomp on the design, number of components (max 12) by 5-fold CV",
 "Mean only": "-", "Prevalence only": "-"}
MLW = {"Logistic regression": ("max_iter 2000", "C in {0.01, 0.1, 1, 10, 100}", "Assumes straight-line effects; can miss interactions."),
       "Decision tree": ("max_depth 3", "max_depth {2,3,5,None} x min_samples_leaf {1,5,10}", "A deep tree memorises noise; limit the depth."),
       "Random forest": ("300 trees", "same grid as tree", "Harder to read; the vote hides the individual rules."),
       "SVM (RBF)": ("RBF kernel, defaults", "C {0.1,1,10} x gamma {scale,0.01,0.1}", "Hard to explain to clinicians."),
       "KNN": ("k = 7", "k {3,5,7,11,15,21} x weights {uniform,distance}", "Noise covariates dilute similarity and can mislead the neighbours."),
       "XGBoost": ("200 trees, depth 3", "depth {2,3,4} x trees {100,300} x lr {0.03,0.1}, subsample 0.8", "Many settings; with few patients it overfits quickly."),
       "MLP (16,)": ("one hidden layer of 16", "hidden {8,16,32} x alpha {1e-4,1e-2,1}", "Least transparent; small arms limit what it can learn.")}

def cvv(c, a, t, m, met):
    x = c[(c.arm == a) & (c.task == t) & (c.method == m)]
    return None if x.empty else (x.iloc[0][met], x.iloc[0][met + "_sd"])

def cov_table(c, t):
    met = "RMSE" if t == "reg" else "AUC"; ms = [m for m in c[(c.task == t) & (c.family == "Covariate")].method.unique()]
    base = "Mean only" if t == "reg" else "Prevalence only"; ms = [m for m in WATCH if m in ms] + [base]; rows = []
    best = {a: min if t == "reg" else max for a in ARMS}
    vals = {a: {m: cvv(c, a, t, m, met) for m in ms} for a in ARMS}
    for m in ms:
        row = {"Method": short(m), "Settings": SET[m]}
        for a in ARMS:
            v = vals[a][m]; row[a] = "n/a" if v is None else f"{v[0]:.3f} &plusmn; {v[1]:.3f}"
            if v is not None and m != base and v[0] == best[a](x[0] for k, x in vals[a].items() if x is not None and k != base): row[a] = f"<b>{row[a]}</b>"
        row["Watch out (kickoff)"] = WATCH[m]; rows.append(row)
    return pd.DataFrame(rows)

def ml_table(c, t):
    met = "RMSE" if t == "reg" else "AUC"; rows = []
    for k, (u, g, w) in MLW.items():
        if k == "Logistic regression" and t == "reg": continue
        row = {"Method": k, "Untuned": u, "Tuned grid (inner 3-fold)": g}
        for a in ARMS:
            vu = cvv(c, a, t, f"{k} (untuned)", met); vt = cvv(c, a, t, f"{k} (tuned, GridSearchCV)", met); row[a] = f"{vu[0]:.3f} &rarr; {vt[0]:.3f}"
        row["Watch out (kickoff)"] = w; rows.append(row)
    return pd.DataFrame(rows)

def terms_table():
    rows = []
    for t in ["reg", "bin"]:
        for a in ARMS:
            tt = r(f"r_{a}_{t}_test_terms.csv"); sg = r(f"signal_r_{a}_{t}.csv"); row = {"Outcome": TASKN[t], "Arm": a}
            for m, key in [("LASSO (glmnet, lambda.min)", "LASSO"), ("Elastic net (glmnet, alpha=.5)", "Elastic net"), ("Stepwise both (BIC)", "Stepwise (BIC)"), ("Best subset (leaps, BIC, nvmax=10)", "Best subset")]:
                x = tt[tt.method == m]; row[key] = "; ".join(f"{nice(q)} ({v:+.2f})" for q, v in zip(x.term, x.coef)) if len(x) else ("n/a (continuous only)" if t == "bin" else "none")
            g = tt[tt.method.str.startswith("GAM")]; row["GAM terms (p&lt;0.05)"] = "; ".join(nice(q) for q in g.term) or "none"
            p = tt[tt.method.str.startswith("PCR")]; row["PCR components"] = f"{len(p)}"; rows.append(row)
    return pd.DataFrame(rows)

def fig_cv(c):
    fig, ax = plt.subplots(2, 3, figsize=(15, 8.6))
    for i, t in enumerate(["reg", "bin"]):
        met = "RMSE" if t == "reg" else "AUC"
        for j, a in enumerate(ARMS):
            x = c[(c.arm == a) & (c.task == t)].sort_values(met, ascending=(t == "reg")); y = np.arange(len(x))[::-1]
            col = [FC.get(f, "#777") for f in x.family]; ax[i, j].errorbar(x[met], y, xerr=x[met + "_sd"], fmt="none", ecolor="#999", lw=.8); ax[i, j].scatter(x[met], y, c=col, s=22, zorder=3)
            ax[i, j].set_yticks(y); ax[i, j].set_yticklabels([short(m) for m in x.method], fontsize=6.5); ax[i, j].set_title(f"{a}: CV {met} ({'lower' if t == 'reg' else 'higher'} is better)", fontsize=9)
            bl = x[x.family == "Baseline"][met]; ax[i, j].axvline(bl.iloc[0], color="#777", ls="--", lw=.8) if len(bl) else None; ax[i, j].tick_params(axis="x", labelsize=7)
    h = [plt.Line2D([], [], marker="o", ls="", color=v, label=k) for k, v in FC.items()]; fig.legend(handles=h, loc="lower center", ncol=3, fontsize=8); fig.tight_layout(rect=[0, .03, 1, 1])
    return fig_html(fig, "s5_cv_scoreboard")

def prim_table():
    p = prim(); rows = []
    for (a, t), g in p.groupby(["arm", "task"], sort=False):
        cv_ = g[g.track == "Covariate"].iloc[0]; ml = g[g.track == "ML"].iloc[0]
        rows.append({"Arm": a, "Outcome": TASKN[t], "CV metric": cv_.cv_metric, "Primary covariate model": f"{short(cv_.primary_method)} ({cv_.cv_value:.3f})", "Primary ML model": f"{short(ml.primary_method)} ({ml.cv_value:.3f})",
                     "Baseline": f"{short(cv_.baseline_method)} ({cv_.baseline_cv_value:.3f})", "Both beat baseline in CV": "yes" if cv_.beats_baseline_in_cv and ml.beats_baseline_in_cv else "no"})
    return pd.DataFrame(rows)

def method_block(mf, m, step=5):
    """One collapsible per-method block: rationale, code, CV row, characteristic figure, uniform CV prediction grid, retained terms."""
    s = mf.slug(m); nm = "Baselines" if m == "Baseline" else m
    return (f"<details><summary><b>{esc(nm)}</b></summary><h4>{esc(nm)}</h4><p>{mf.rationale(m)}</p>{mf.code_excerpt(m)}"
            f"{tbl(mf.cv_rows(m), cap='CV result (train, repeated 5-fold x3; mean &plusmn; SD)')}"
            f"<p class=cap>Characteristic figure</p>{mf.characteristic(m, step) if m != 'Baseline' else note('Baselines have no fitted structure.')}"
            f"<p class=cap>Out-of-fold prediction: continuous outcome obs vs pred (top), responder-label ROC (bottom)</p>{mf.pred_grid(mf.cv_get, m, f's5_{s}_pred')}{mf.retained_line(m)}</details>")

def sec56():
    import method_figs as mf
    cov = "".join(method_block(mf, m) for m in mf.COV + ["Baseline"]); ml = "".join(method_block(mf, m) for m in MLW)
    return f"""<h2>5.6 Method-by-method (training diagnostics)</h2>
<p>One collapsible block per method. All figures use TRAIN only: the fitted-model diagnostics come from the full-train fit, and every prediction panel is the out-of-fold CV prediction (averaged over the 3 CV repeats; observed = the training patient's own value). ML blocks show the untuned and tuned variants together. No test number appears here.</p>
<h3>Covariate track</h3>{cov}<h3>ML track</h3>{ml}"""

def build():
    c = cv(); R = req([("Fit and tune using the training set only", "Every number on this page is repeated 5-fold x3 CV on TRAIN; the test set is not read", "5.1-5.4"),
        ("Show untuned and tuned results", "Each ML method has an untuned and a tuned (small GridSearchCV) row; table 5.2 shows untuned &rarr; tuned", "5.2"),
        ("Keep grids small / coarse on small arms", "Grids of 5-12 combinations, inner 3-fold", "5.2"),
        ("Stepwise lists selected terms; LASSO and elastic net list non-zero coefficients", "Retained terms of each selector (full-train fit)", "5.3"),
        ("Per-method 'watch out'", "One line per method taken from the kickoff method slides", "5.1, 5.2")])
    body = f"""{R}<h2>5.1 Covariate track: CV scoreboard</h2>
<p>Metric: repeated 5-fold x3 CV on TRAIN (mean &plusmn; SD over the 3 repeats; the SD is small because the folds repeat the same patients, it is not a confidence interval). Bold = best covariate model of that arm.</p>
{tbl(cov_table(c, 'reg'), cap="Continuous outcome: CV RMSE (original units; lower is better)")}{tbl(cov_table(c, 'bin'), cap="Responder label: CV ROC-AUC (higher is better)")}
<h2>5.2 ML track: untuned &rarr; tuned</h2>
<p>Each cell shows CV untuned &rarr; tuned. Tuning is an inner 3-fold grid search inside each outer fold. Support-vector and MLP regressors standardise the target internally and predict in original units.</p>
{tbl(ml_table(c, 'reg'), cap="Continuous outcome: CV RMSE (lower is better)")}{tbl(ml_table(c, 'bin'), cap="Responder label: CV ROC-AUC (higher is better)")}
{note("Tuning helped most continuous-outcome rows (largest for XGBoost and the MLP) but was mixed for the label, where several tuned rows are no better or worse (for example Tideglusib SVM 0.767 &rarr; 0.682).")}
<h2>5.3 CV scoreboard figure</h2>{fig_cv(c)}
<h2>5.4 Retained terms (selection methods, full-train fit)</h2>
{tbl(terms_table(), cap="Non-zero coefficients (z-scored numeric, 0/1 dummies; sign on the raw outcome scale) or selected terms. PCR: number of components kept")}
{note("For Mexiletine the continuous outcome is a change where more negative is better, so a negative coefficient means a better response. Different selectors keep different sets: this is expected with correlated covariates and is why Step 6.5 asks several selectors, resampling and a shuffled-outcome null before calling a covariate signal.")}
<h2>5.5 Primary models chosen by CV only</h2>
<p>Per arm and outcome the best covariate model and the best ML model (tuned and untuned rows pooled) are picked by TRAIN CV alone, before any test row exists in the analysis. These are the models carried into Step 6.</p>{tbl(prim_table())}
{sec56()}"""
    return page(4, "Fit and tune on the training set only", "Covariate methods and ML methods are fitted and compared by repeated CV on TRAIN. Nothing here uses the test set.", body)
