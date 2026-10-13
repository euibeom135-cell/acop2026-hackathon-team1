"""Step 4 page: let the data traits choose the methods (four-row trait table from TRAIN numbers) + decision + small PDF-scope catalogue."""
from data import *
from traits import pairs, vif

def traits_table():
    rows = {k: [] for k in ["Sample size", "Covariates", "Relationships", "Outcome type"]}
    for a in ARMS:
        d = train(a); n = len(d); p = len(numcols(a)) + len(dummies(a)); pn = pairs(a, .5, numeric_only=True); pa = pairs(a, .5); v = vif(a); nres = int(d.label.sum())
        rows["Sample size"].append(f"n = {n} train patients per arm")
        rows["Covariates"].append(f"p = {p} columns ({len(numcols(a))} numeric + {len(dummies(a))} dummies); n/p = {n / p:.1f}; responders/p = {nres / p:.1f}")
        rows["Relationships"].append(f"{len(pn)} numeric pairs and {len(pa)} design pairs with |r| >= 0.5; max VIF {v.max():.1f} ({nice(v.idxmax())}); {int((v > 5).sum())} columns with VIF > 5")
        rows["Outcome type"].append(f"continuous ({OUTCOME[a][0]}, SD {d.y.std():.2f}) and binary label ({d.label.mean():.0%} responders)")
    T = pd.DataFrame([[k] + v for k, v in rows.items()], columns=["Data trait"] + ARMS)
    ask = {"Sample size": "How many patients per arm?", "Covariates": "How many, of what types?", "Relationships": "Correlations or interactions?", "Outcome type": "Continuous or binary?"}
    imp = {"Sample size": "Small: simpler or penalised models; small tuning grids", "Covariates": "Plan encoding and variable selection", "Relationships": "Methods that tolerate collinearity", "Outcome type": "Match metrics to outcome"}
    T.insert(1, "Kickoff asks", T["Data trait"].map(ask)); T["Kickoff implication"] = T["Data trait"].map(imp); return T

def fig_pca():
    fig, ax = plt.subplots(figsize=(4.6, 2.8))
    for a in ARMS:
        v = r(f"pca_{a}_var.csv"); ax.plot(range(1, len(v) + 1), v.cum, "o-", ms=3, color=ARMC[a], label=a)
    ax.axhline(.8, color="#999", lw=.7, ls="--"); ax.set_xlabel("principal component"); ax.set_ylabel("cumulative variance"); ax.legend(fontsize=7); ax.tick_params(labelsize=7); fig.tight_layout()
    return fig_html(fig, "s4_pca")

def pca_k():
    out = {}
    for a in ARMS:
        v = r(f"pca_{a}_var.csv"); out[a] = int((v.cum < .8).sum() + 1)
    return out

CAT = pd.DataFrame([
 ("Covariate", "lm / glm (all covariates)", "Baseline effect sizes, all covariates in"), ("Covariate", "Stepwise, both directions, BIC", "Narrow to a manageable set per arm"),
 ("Covariate", "Best subset (BIC, nvmax 10; continuous only)", "Exhaustive search at p of about 20"), ("Covariate", "Ridge / LASSO / elastic net", "Correlated covariates, small n; sparse or shrunk"),
 ("Covariate", "GAM (smooths, k=5, REML)", "Curvature (represents polynomial / piecewise / splines)"), ("Covariate", "PCA / PCR", "Collapse correlated covariates"),
 ("ML", "Logistic regression (label only)", "Transparent baseline"), ("ML", "Decision tree", "Readable cut-offs"), ("ML", "Random forest", "Interactions without specifying them"),
 ("ML", "SVM (RBF)", "Curved boundaries"), ("ML", "KNN", "Patients like you; sensitive to noise covariates"), ("ML", "XGBoost", "Strong on tabular data; overfits small n"), ("ML", "MLP (16,)", "Does a tiny network add value?")],
 columns=["Track", "Method used", "Why it fits"])

def build():
    T = traits_table(); k = pca_k()
    R = req([("Let the data characteristics drive the choice (sample size, covariates, relationships, outcome type)", "Four-row trait table filled from train numbers", "4.1"),
             ("Simpler or penalised models suit small samples; plan encoding and variable selection", "Decision paragraph and the method catalogue below", "4.2, 4.3"),
             ("Covariate modelling and machine learning are two tracks", "Both tracks run in parallel on the same folds", "4.2")])
    body = f"""{R}<h2>4.1 Data traits (train rows)</h2>{tbl(T)}
{note(f"p counts the model columns after dummy coding. VIF comes from the correlation matrix of the full train design. The unsupervised PCA (no outcome; full design) needs {k['Mexiletine']}, {k['Oligonucleotide']} and {k['Tideglusib']} components to reach 80% of the variance (Mexiletine, Oligonucleotide, Tideglusib), so the design is not low-dimensional even though individual pairs are strongly correlated.")}{fig_pca()}
<h2>4.2 Decision</h2>
<div class=box><ul>
<li><b>Small n (128-136) and p of 19-20</b>: n/p is about 7 and the label has only 1.9 to 3.2 responders per column, so unpenalised or flexible models will overfit. The covariate track therefore leads with penalised regression (ridge, LASSO, elastic net), BIC stepwise selection, best subset and a GAM, with lm/glm as the reference. The ML track uses only small tuning grids, because a large grid on a small arm mostly finds noise.</li>
<li><b>Correlated covariates</b>: log10 CTG and myotonia severity correlate at 0.84-0.90 in every arm. LASSO may arbitrarily drop one of a correlated pair, so ridge/elastic net, PCR and several selectors are run side by side and agreement across methods is read as evidence (Step 6.5).</li>
<li><b>Both tracks run in parallel</b> on identical folds and identical test patients. The covariate track answers 'which covariates matter and how'; the ML track is the predictive comparison that answers 'can ML improve beyond covariate modelling?'.</li>
<li><b>Outcome</b>: the continuous outcome is primary (metrics RMSE, MAE, R2); the responder label is the parallel classification task (ROC-AUC, recall, precision, accuracy at a stated cutoff).</li></ul></div>
<h2>4.3 Methods used (kickoff scope only)</h2>{tbl(CAT)}
{note("Polynomial, piecewise, regression-spline and smoothing-spline models are represented by the single GAM (smooth terms with k=5), which covers curved effects in one fit. Forward/backward stepwise and AIC variants are not run separately; stepwise uses both directions with BIC. Every ML method appears as an untuned row (kickoff snippet settings) and a tuned row (small GridSearchCV).")}"""
    return page(3, "Select methods from the data traits", "Sample size, covariates, relationships and outcome type decide which methods are worth running.", body)
