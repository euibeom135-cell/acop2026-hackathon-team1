"""S05: which covariates does each method use? (PDF 'compare the covariates, not only the scores'). TRAIN/CV only.
Selection-type methods: fraction of the 15 CV fits that kept the covariate. Ridge: mean |coef| / max. ML: held-out permutation importance (rep-0 folds) / max, clipped at 0.
Outputs results/cov_matrix_<arm>_<task>.csv + results/cov_matrix_<arm>_<task>.png"""
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, re
from scommon import *
SEL = ["Stepwise forward (AIC)", "Stepwise backward (AIC)", "Stepwise both (AIC)", "Stepwise both (BIC)", "Best subset (leaps, BIC, nvmax=10)", "LASSO (glmnet, lambda.min)",
       "LASSO (glmnet, lambda.1se)", "Elastic net (glmnet, alpha=.5)", "GAM (mgcv, s(k=5), REML, select)"]
main_sig = json.load(open(MAIN / "results" / "step3_summary.json"))
for arm in ARMS:
    cols = list(get_arm(arm)["Ztr"].columns)
    for task in ("reg", "bin"):
        T = pd.read_csv(ARES / f"r_{arm}_{task}_cv_terms.csv"); nfit = 15; M = {}
        for m in SEL:
            t = T[T.method == m]; 
            if t.empty: continue
            t = t.assign(term=t.term.map(lambda s: re.sub(r"\d+$", "", s) if s not in cols else s)); M[m] = pd.Series({c: t[(t.term == c)].fit.nunique() / nfit for c in cols})
        t = T[T.method == "Ridge (glmnet)"]; r = t.assign(a=t.coef.abs()).groupby("term").a.mean().reindex(cols).fillna(0); M["Ridge |coef| (rel.)"] = r / r.max()
        I = pd.read_csv(ARES / f"ml_{arm}_{task}_cv_importance.csv"); I = I[I.method.str.contains("tuned") & ~I.method.str.contains("untuned")]
        for m, g in I.groupby("method"):
            v = g.groupby("term").importance.mean().reindex(cols).clip(lower=0).fillna(0); M[m.replace(" (tuned, GridSearchCV)", " [perm. imp.]")] = v / max(v.max(), 1e-12)
        D = pd.DataFrame(M).T; D = D[D.mean().sort_values(ascending=False).index]; D.to_csv(ARES / f"cov_matrix_{arm}_{task}.csv")
        fig, ax = plt.subplots(figsize=(0.55 * D.shape[1] + 3, 0.34 * D.shape[0] + 1.6)); im = ax.imshow(D.values, cmap="viridis", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(D.shape[1])); ax.set_xticklabels(D.columns, rotation=60, ha="right", fontsize=8); ax.set_yticks(range(D.shape[0])); ax.set_yticklabels(D.index, fontsize=8)
        sig = {c.replace("=", "_") for c in main_sig.get(arm, {})}
        for i, c in enumerate(D.columns):
            if c in sig: ax.get_xticklabels()[i].set_color("red"); ax.get_xticklabels()[i].set_fontweight("bold")
        plt.colorbar(im, ax=ax, fraction=.03); ax.set_title(f"{arm} - {'continuous outcome' if task=='reg' else 'responder label'}: covariate use per method (red = main-analysis SIGNAL covariate)", fontsize=9)
        fig.savefig(ARES / f"cov_matrix_{arm}_{task}.png", dpi=110, bbox_inches="tight"); plt.close(fig)
        print(arm, task, "top covariates by mean use:", list(D.columns[:5]))
