"""N08: builds reports/summary_split1to3.html. Per method: the code that was run, results (CV + test), predicted-vs-observed / ROC figures and the per-patient test predictions.
No model fitting here (reads results/ from s01-s07)."""
import io, base64, pickle, re, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, statsmodels.api as sm
from scipy import stats as st
from sklearn.metrics import roc_curve
from scommon import *
from metrics import *
SRC = Path(__file__).parent
img = lambda f, dpi=85: (lambda b: (f.savefig(b, format="png", dpi=dpi, bbox_inches="tight"), plt.close(f), f'<img src="data:image/png;base64,{base64.b64encode(b.getvalue()).decode()}" style="max-width:100%">')[2])(io.BytesIO())
png = lambda p: f'<img src="data:image/png;base64,{base64.b64encode(open(p, "rb").read()).decode()}" style="max-width:100%">'
esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
tbl = lambda t, **k: t.to_html(classes="t", border=0, index=False, float_format=lambda v: f"{v:.3f}", na_rep="", **k)
cv = pd.read_csv(ARES / "cv_scoreboard.csv"); ts = pd.read_csv(ARES / "test_scoreboard.csv"); tp = pd.read_csv(ARES / "test_predictions.csv"); sc = pd.read_csv(ARES / "sum_cov_vs_ml.csv")
TERMS = pd.read_csv(ARES / "r_test_terms_all.csv"); sp = split_table(); IDS = {a: sp[(sp.arm == a) & (sp.set == "test")].patient_id.tolist() for a in ARMS}
OLD = MAIN / "all_methods" / "results"; PAL = ["#1f77b4", "#d95f02", "#2ca02c", "#9467bd", "#8c564b", "#e377c2"]
rsrc = open(SRC / "r_covariate.R").read().split("\n"); blocks = []
for ln in rsrc:
    if ln and not ln[0].isspace() and not ln.startswith("}") and not ln.startswith("#") or not blocks: blocks.append([ln])
    else: blocks[-1].append(ln)
def rcode(keys):
    out = [b for b in blocks if any(k in b[0] for k in keys)]; return "\n".join("\n".join(b) for b in out)
def pycode(names, path="ml_models.py"):
    L = open(SRC / path).read().split("\n"); return "\n".join(l.strip() for l in L if any(f'add("{n}"' in l for n in names))
SHARED_R = rcode(["fitfun <-", "prd <-", "rhs <-", "terms_of <-", "curvesel <-"]); STAGE_R = "\n".join(l for l in rsrc if l.startswith(("safe <-", "if (stage", "  fo <-", "  for (nm in names(M)) for (r", "    te <- fo$row", "    P[[length", "} else {", "  te <- mk")))
VAR = lambda *n: list(n)
ML = lambda base, reg_ok=True, bin_ok=True: [f"{base} (untuned)", f"{base} (tuned, GridSearchCV)"]
METHODS = [
 dict(id="lm", grp="Covariate", title="Linear / logistic regression (lm, glm)", why="Straight-line effect per covariate; the starting point. glm(binomial) for the responder label.", var=VAR("lm / glm (all covariates)"), rkeys=['M[["lm'], tp="R: stats::lm / glm"),
 dict(id="step", grp="Covariate", title="Stepwise selection: forward, backward, both (MASS::stepAIC)", why="Adds/drops covariates by AIC (BIC variant: k=log n). Unstable by design - see selection frequencies in section 6.", var=VAR("Stepwise forward (AIC)", "Stepwise backward (AIC)", "Stepwise both (AIC)", "Stepwise both (BIC)"), rkeys=["step_m <-", 'M[["Stepwise'], tp="R: MASS::stepAIC"),
 dict(id="subset", grp="Covariate", title="Best subset selection (leaps::regsubsets)", why="Exhaustive search over all subsets up to 10 covariates, best by BIC. Continuous outcome only (leaps has no logistic version).", var=VAR("Best subset (leaps, BIC, nvmax=10)"), rkeys=["Best subset"], tp="R: leaps::regsubsets"),
 dict(id="pen", grp="Covariate", title="Ridge, LASSO, elastic net (glmnet)", why="Penalised regression; lambda by 10-fold CV (lambda.min, plus the 1-SE LASSO). Same code for both outcome types (family argument).", var=VAR("Ridge (glmnet)", "LASSO (glmnet, lambda.min)", "LASSO (glmnet, lambda.1se)", "Elastic net (glmnet, alpha=.5)"), rkeys=["gn <-", 'M[["Ridge', 'M[["LASSO'], tp="R: glmnet::cv.glmnet"),
 dict(id="poly", grp="Covariate", title="Polynomial regression (poly, degree 2)", why="Curved effects on the arm's 4 most outcome-correlated covariates (chosen inside every training fit, so no leakage).", var=VAR("Polynomial deg-2 (top-4 covariates)"), rkeys=["Polynomial"], tp="R: stats::poly"),
 dict(id="piece", grp="Covariate", title="Piecewise model (cut at train tertiles)", why="Step function per covariate; cut points are train-tertiles, re-used unchanged on new patients.", var=VAR("Piecewise: cut() tertile bins (top-4 covariates)"), rkeys=["Piecewise"], tp="R: stats::cut"),
 dict(id="bs", grp="Covariate", title="Regression splines (splines::bs, df=4)", why="Cubic B-splines per covariate (4 df); knots from the training rows.", var=VAR("Regression spline bs(df=4) (top-4 covariates)"), rkeys=["Regression spline"], tp="R: splines::bs"),
 dict(id="ss", grp="Covariate", title="Smoothing spline (smooth.spline, cv=TRUE)", why="Univariate by construction: fitted to the single strongest covariate; shows what one smooth curve can do.", var=VAR("Smoothing spline (top-1 covariate, cv=TRUE)"), rkeys=["Smoothing spline"], tp="R: stats::smooth.spline"),
 dict(id="gam", grp="Covariate", title="Generalised additive model (mgcv::gam)", why="Penalised smooth s(x,k=5) for every continuous covariate + linear dummies; REML with automatic term removal.", var=VAR("GAM (mgcv, s(k=5), REML, select)"), rkeys=["GAM"], tp="R: mgcv::gam"),
 dict(id="pca", grp="Covariate", title="PCA and principal-component regression (prcomp)", why="Unsupervised summary of correlated covariates (figures in section 7); PCR regresses the outcome on the first k components, k by 5-fold CV.", var=VAR("PCR (prcomp, k by 5-fold CV)"), rkeys=["PCR"], tp="R: stats::prcomp"),
 dict(id="logit", grp="ML", title="Logistic regression (scikit-learn)", why="Weighted scorecard for the responder label (the continuous-outcome counterpart is lm). Untuned C=1 vs tuned C.", var=ML("Logistic regression"), names=["Logistic regression"], tp="Python: sklearn LogisticRegression"),
 dict(id="tree", grp="ML", title="Decision tree", why="Yes/no splits; untuned depth 3, tuned depth x min leaf.", var=ML("Decision tree"), names=["Decision tree"], tp="Python: sklearn tree"),
 dict(id="rf", grp="ML", title="Random forest", why="300 trees on random slices; tuned depth x min leaf.", var=ML("Random forest"), names=["Random forest"], tp="Python: sklearn ensemble"),
 dict(id="svm", grp="ML", title="Support vector machine (RBF)", why="Max-margin kernel model (SVR for the continuous outcome); tuned C x gamma.", var=ML("SVM (RBF)"), names=["SVM (RBF)"], tp="Python: sklearn SVC / SVR"),
 dict(id="knn", grp="ML", title="K-nearest neighbours", why="Averages the k most similar training patients; untuned k=7, tuned k x weights.", var=ML("KNN"), names=["KNN"], tp="Python: sklearn neighbors"),
 dict(id="xgb", grp="ML", title="XGBoost", why="Boosted shallow trees; untuned 200 x depth 3, tuned depth x trees x learning rate.", var=ML("XGBoost"), names=["XGBoost"], tp="Python: xgboost"),
 dict(id="mlp", grp="ML", title="Neural network (MLP, one hidden layer)", why="Deliberately tiny network (16 units); tuned hidden size x L2.", var=ML("MLP (16,)"), names=["MLP (16,)"], tp="Python: sklearn neural_network")]
SHARED_PY = "\n".join(l for l in open(SRC / "ml_models.py").read().split("\n") if l.startswith(("def variants", "    out = []", "    for r in registry", "        from sklearn.base", "        out.append", "        cv = ", "    return out")))
FIT_PY = "\n".join(l.strip() for l in open(SRC / "s02_ml_cv.py").read().split("\n") if "m = build().fit" in l or "permutation_importance" in l)
SHAP_PY = "\n".join(l.strip() for l in open(SRC / "s06_test_scoring.py").read().split("\n") if "shap.TreeExplainer" in l or "def fit_pred" in l or "nm, build, tuned, r = variants" in l)

def pred_fig(m):
    fig, ax = plt.subplots(2, 3, figsize=(15, 8.2))
    for j, arm in enumerate(ARMS):
        for i, task in enumerate(("reg", "bin")):
            a = ax[i][j]; any_ = False
            for k, v in enumerate(m["var"]):
                g = tp[(tp.arm == arm) & (tp.task == task) & (tp.method == v)].sort_values("row")
                if g.empty: continue
                any_ = True; short = v.replace(" (tuned, GridSearchCV)", " [tuned]").replace(" (untuned)", " [untuned]")[:34]
                if task == "reg": a.scatter(g.pred, g.obs, s=18, alpha=.75, c=PAL[k % 6], label=short)
                else: f, t_, _ = roc_curve(g.obs, g.pred); a.plot(f, t_, c=PAL[k % 6], lw=1.8, label=f"{short} AUC={roc_auc_score(g.obs, g.pred):.2f}")
            if not any_: a.text(.5, .5, "not applicable for this outcome type", ha="center", transform=a.transAxes); a.set_xticks([]); a.set_yticks([])
            elif task == "reg":
                g0 = tp[(tp.arm == arm) & (tp.task == "reg")]; lo, hi = g0.obs.min(), g0.obs.max(); a.plot([lo, hi], [lo, hi], "k--", lw=.8); a.set_xlabel("predicted (test)"); a.set_ylabel("observed"); a.legend(fontsize=6)
            else: a.plot([0, 1], [0, 1], "k--", lw=.8); a.set_xlabel("false-positive rate"); a.set_ylabel("recall"); a.legend(fontsize=6, loc="lower right")
            a.set_title(f"{arm}: {'continuous outcome, observed vs predicted' if task == 'reg' else 'responder label, ROC'}", fontsize=8)
    return img(fig, 75)

def method_tables(m):
    out = []
    r = ts[(ts.task == "reg") & ts.method.isin(m["var"])].merge(cv[(cv.task == "reg")][["arm", "method", "RMSE", "R2"]].rename(columns={"RMSE": "CV RMSE", "R2": "CV R2"}), on=["arm", "method"])
    if len(r): r["test RMSE [95% CI]"] = [f"{a:.3f} [{b:.3f}, {c:.3f}]" for a, b, c in zip(r.RMSE, r.RMSE_lo, r.RMSE_hi)]; out.append("<b>Continuous outcome</b>" + tbl(r[["arm", "method", "CV RMSE", "CV R2", "test RMSE [95% CI]", "MAE", "R2", "AUC_derived"]].rename(columns={"MAE": "test MAE", "R2": "test R2 (vs test mean)", "AUC_derived": "responder AUC from prediction"})))
    b = ts[(ts.task == "bin") & ts.method.isin(m["var"])].merge(cv[(cv.task == "bin")][["arm", "method", "AUC"]].rename(columns={"AUC": "CV AUC"}), on=["arm", "method"])
    if len(b): b["test AUC [95% CI]"] = [f"{a:.3f} [{c:.3f}, {d:.3f}]" for a, c, d in zip(b.AUC, b.AUC_lo, b.AUC_hi)]; out.append("<b>Responder label</b>" + tbl(b[["arm", "method", "CV AUC", "test AUC [95% CI]", "recall", "precision", "accuracy", "cutoff"]]))
    return "".join(out)

def pred_tables(m):
    out = []
    for arm in ARMS:
        for task, ttl in (("reg", "continuous outcome (observed, predicted)"), ("bin", "responder label (1 = responder; predicted probability)")):
            G = tp[(tp.arm == arm) & (tp.task == task) & tp.method.isin(m["var"])]
            if G.empty: continue
            W = G.pivot(index="row", columns="method", values="pred"); W.insert(0, "observed", G.groupby("row").obs.first()); W.insert(0, "patient_id", [IDS[arm][i] for i in W.index]); W.columns = [c.replace(" (tuned, GridSearchCV)", " [tuned]").replace(" (untuned)", " [untuned]") for c in W.columns]
            out.append(f"<details><summary>Per-patient test predictions: {arm}, {ttl} - {len(W)} patients</summary>{tbl(W)}</details>")
    return "".join(out)

def terms_note(m):
    T = TERMS[TERMS.method.isin(m["var"])]
    if T.empty: return ""
    rows = [f"<li><b>{arm}</b> / {'continuous' if task=='reg' else 'responder'} / {meth.split(' (')[0]}: {', '.join(sorted(g.term.map(lambda s: re.sub(r'(\\d)$', '', s) if m['id'] in ('poly','piece','bs') else s)))[:260]}</li>" for (arm, task, meth), g in T.groupby(["arm", "task", "method"]) if len(g)]
    return "<details><summary>Terms kept in the final train fit</summary><ul>" + "".join(rows) + "</ul></details>"

def section(m):
    if "rkeys" in m: code = rcode(m["rkeys"]); lang = "R"
    else: code = pycode(m["names"]); lang = "Python"
    return (f"<h3 id='{m['id']}'>{m['title']} <small>({m['grp']} track; {m['tp']})</small></h3><p>{m['why']}</p><details open><summary>Code that ran ({lang}; shared helpers in section 5)</summary><pre>{esc(code)}</pre></details>"
            f"<details open><summary>Results (CV on train; test scored once)</summary>{method_tables(m)}</details><details open><summary>Prediction results</summary>{pred_fig(m)}</details>{pred_tables(m)}{terms_note(m)}")

# ---- split section
B = pd.read_csv(ARES / "split_balance.csv"); C = pd.read_csv(ARES / "split_candidates.csv")
def split_fig():
    fig, ax = plt.subplots(2, 3, figsize=(16, 7.5))
    for j, arm in enumerate(ARMS):
        c = C[C.arm == arm]; sd = c[c.accepted].seed.iloc[0]; ch = c[c.seed == sd].iloc[0]; ax[0][j].hist(c.M, bins=60, color="#bbb"); ax[0][j].axvline(ch.M, c="r", label=f"chosen (seed {sd})"); ax[0][j].axvline(c[c.accepted].M.max(), c="b", ls="--", label="acceptance threshold (lowest 2%)"); ax[0][j].set_xlabel("Mahalanobis distance of train-test covariate means"); ax[0][j].set_title(f"{arm}: 5000 candidate splits", fontsize=9); ax[0][j].legend(fontsize=7)
        b = B[(B.arm == arm) & ~B["var"].str.startswith(("OUTCOME", "LABEL"))].pivot(index="var", columns="split", values="smd"); o = b.abs().max(axis=1).sort_values().index; b = b.loc[o]; y = np.arange(len(b)); ax[1][j].barh(y - .2, b["old 80/20 (main project)"], height=.4, label="old 80/20", color="#999"); ax[1][j].barh(y + .2, b["new 1:3 re-randomised"], height=.4, label="new 1:3 re-randomised", color="#d95f02"); ax[1][j].set_yticks(y); ax[1][j].set_yticklabels(b.index, fontsize=6); ax[1][j].axvline(0, c="k", lw=.6)
        for v in (-.1, .1): ax[1][j].axvline(v, c="g", ls=":", lw=.8)
        ax[1][j].set_xlabel("standardised mean difference (test - train)"); ax[1][j].legend(fontsize=7)
    return img(fig, 85)
bal = B.groupby(["arm", "split"]).apply(lambda g: pd.Series(dict(max_abs_SMD=g[~g["var"].str.startswith(("OUTCOME", "LABEL"))].smd.abs().max(), n_features_p_lt_05=int((g[~g["var"].str.startswith(("OUTCOME", "LABEL"))].p < .05).sum()), outcome_SMD=g[g["var"].str.startswith("OUTCOME")].smd.iloc[0], outcome_KS_p=g[g["var"].str.startswith("OUTCOME")].p.iloc[0], responder_share_diff=g[g["var"].str.startswith("LABEL")].smd.iloc[0]))).reset_index()
nsplit = sp.groupby(["arm", "set"]).size().unstack().reset_index()
# ---- master scoreboard + old-vs-new
def master(task, key, fmt):
    t = ts[ts.task == task].pivot(index="method", columns="arm", values=key); c = cv[cv.task == task].pivot(index="method", columns="arm", values=key); fam = ts[ts.task == task].drop_duplicates("method").set_index("method").family
    M = pd.concat({"test": t, "train CV": c}, axis=1); M.columns = [f"{b} - {a}" for a, b in M.columns]; M.insert(0, "family", fam); return M.sort_values(f"Mexiletine - test", ascending=(task == "reg")).reset_index()
def old_vs_new():
    o = pd.read_csv(OLD / "test_scoreboard.csv"); oc = pd.read_csv(OLD / "cv_scoreboard.csv"); r = []
    for arm in ARMS:
        for task, key in (("reg", "RMSE"), ("bin", "AUC")):
            a = ts[(ts.arm == arm) & (ts.task == task)].set_index("method")[key]; b = o[(o.arm == arm) & (o.task == task)].set_index("method")[key]; a2 = cv[(cv.arm == arm) & (cv.task == task)].set_index("method")[key]; b2 = oc[(oc.arm == arm) & (oc.task == task)].set_index("method")[key]
            j = a.index.intersection(b.index); j2 = a2.index.intersection(b2.index)
            r.append(dict(arm=arm, task=task, n_methods=len(j), spearman_test_old_vs_new=st.spearmanr(a[j], b[j]).statistic, spearman_CV_old_vs_new=st.spearmanr(a2[j2], b2[j2]).statistic, best_test_old=b[j].idxmin() if task == "reg" else b[j].idxmax(), best_test_new=a[j].idxmin() if task == "reg" else a[j].idxmax()))
    return pd.DataFrame(r)
ovn = old_vs_new()
def cov_consensus(arm, task):
    D = pd.read_csv(ARES / f"cov_matrix_{arm}_{task}.csv", index_col=0); n = (D >= .5).sum(); return pd.DataFrame({"covariate": n.index, "methods using it (>=0.5)": n.values, "of": len(D)}).sort_values("methods using it (>=0.5)", ascending=False).head(5)
def shap_fig(arm):
    pk = pickle.load(open(ARES / "shap_pack.pkl", "rb")); fig, ax = plt.subplots(1, 2, figsize=(14, 4.4))
    for a, task in zip(ax, ("reg", "bin")):
        M = {}
        for (ar, tk, nm), (sv, Z) in pk.items():
            if ar == arm and tk == task: v = np.abs(sv).mean(0); M[nm.replace(" (tuned, GridSearchCV)", "")] = pd.Series(v / v.max(), index=Z.columns)
        D = pd.DataFrame(M); D = D.loc[D.mean(1).sort_values(ascending=False).index[:10]]; D.plot.barh(ax=a, width=.8); a.invert_yaxis(); a.set_title(f"{arm}: mean |SHAP| (train rows, rel. to max) - {'regression' if task=='reg' else 'classification'}", fontsize=9); a.tick_params(labelsize=8)
    return img(fig)
def pca_fig(arm):
    d = get_arm(arm); v = pd.read_csv(ARES / f"pca_{arm}_var.csv"); L = pd.read_csv(ARES / f"pca_{arm}_loadings.csv", index_col=0); from sklearn.decomposition import PCA; S = PCA(2).fit_transform(d["Ztr"]); fig, ax = plt.subplots(1, 3, figsize=(16, 3.6))
    ax[0].bar(range(1, len(v) + 1), v.var_ratio); ax[0].plot(range(1, len(v) + 1), v.cum, "ko-"); ax[0].set_title(f"{arm}: scree + cumulative variance", fontsize=9)
    s = ax[1].scatter(S[:, 0], S[:, 1], c=d["ytr"].values, cmap="coolwarm", s=14); plt.colorbar(s, ax=ax[1], label="outcome (colour only)"); ax[1].set_xlabel("PC1"); ax[1].set_ylabel("PC2")
    ax[2].barh(L.index, L.PC1, alpha=.7, label="PC1"); ax[2].barh(np.arange(len(L)), L.PC2, alpha=.5, label="PC2", height=.4); ax[2].tick_params(labelsize=7); ax[2].legend(fontsize=7); ax[2].set_title("loadings", fontsize=9); return img(fig)
tu = pd.read_csv(ARES / "sum_tuned_vs_untuned.csv"); tus = tu.groupby(["set", "task"]).agg(n=("tuned_better", "size"), share_tuned_better=("tuned_better", "mean")).reset_index(); ag = pd.read_csv(ARES / "sum_cv_test_agreement.csv"); cut = pd.read_csv(ARES / "sum_cutoff.csv")
cs = cut.groupby("arm")[["rec_youden", "prec_youden", "acc_youden", "rec_05", "prec_05", "acc_05"]].mean().reset_index()
sc2 = sc.copy(); sc2["95% CI"] = [f"[{a:.3f}, {b:.3f}]" for a, b in zip(sc2.diff_lo, sc2.diff_hi)]
imp_note = "<ul>" + "".join(f"<li><b>{a}</b>: " + "; ".join(f"{t} - " + ", ".join(f"{r.covariate} {r['methods using it (>=0.5)']}/{r['of']}" for _, r in cov_consensus(a, t).head(3).iterrows()) for t in ("reg", "bin")) + "</li>" for a in ARMS) + "</ul>"
svg = """<svg viewBox="0 0 980 230" style="max-width:100%;font:12px system-ui"><defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8z"/></marker></defs>
<g fill="#eef3fb" stroke="#3a6ea5"><rect x="10" y="85" width="190" height="60" rx="6"/><rect x="290" y="15" width="260" height="75" rx="6" fill="#e8f1fb"/><rect x="290" y="135" width="260" height="75" rx="6" fill="#fdeee3" stroke="#d95f02"/><rect x="650" y="85" width="190" height="60" rx="6" fill="#eef7ee" stroke="#2a8a2a"/></g>
<g text-anchor="middle"><text x="105" y="108">same 1:3 split, same train-only</text><text x="105" y="124">preprocessing, same CV folds</text><text x="420" y="38" font-weight="bold">Covariate track (R)</text><text x="420" y="56">lm, stepwise, best subset, glmnet,</text><text x="420" y="72">poly, cut, bs, smooth.spline, GAM, PCR</text>
<text x="420" y="158" font-weight="bold">ML track (Python)</text><text x="420" y="176">logistic, tree, RF, SVM, KNN,</text><text x="420" y="192">XGBoost, MLP (untuned + tuned)</text><text x="745" y="108">one scoreboard per arm:</text><text x="745" y="124">same test patients, same metrics</text></g>
<g stroke="#000" marker-end="url(#a)"><line x1="200" y1="105" x2="290" y2="60"/><line x1="200" y1="125" x2="290" y2="170"/><line x1="550" y1="60" x2="650" y2="105"/><line x1="550" y1="170" x2="650" y2="125"/></g>
<text x="420" y="225" text-anchor="middle" fill="#a00">no arrow between the tracks: each is fitted independently; they are only compared at the end</text></svg>"""
H = lambda rows, cols: "<table class=t><tr>" + "".join(f"<th>{c}</th>" for c in cols) + "</tr>" + "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in rows) + "</table>"
sec_cov = "".join(section(m) for m in METHODS if m["grp"] == "Covariate"); sec_ml = "".join(section(m) for m in METHODS if m["grp"] == "ML")
toc = "".join(f"<li><a href='#{m['id']}'>{m['title']}</a></li>" for m in METHODS)
support = (f"<h3 id='tuning'>Hyper-parameter tuning (GridSearchCV)</h3><p>Every ML model appears twice: untuned (settings from the PDF snippets) and tuned (coarse grid, inner 3-fold CV on the training rows only; scoring = neg-RMSE or ROC-AUC). Selected parameters per arm are in <code>ts.best_params</code> (test table CSV).</p><details open><summary>Code</summary><pre>{esc(SHARED_PY)}\n\n# fit inside every outer CV fold (and once on the full train for test scoring):\n{esc(FIT_PY)}</pre></details>{tbl(tus)}"
 f"<h3 id='perm'>Permutation importance</h3><p>Held-out-fold permutation importance (5 repeats) of every tuned ML model; code line is in the block above. Results are the lower rows of each heatmap in section 6.</p>"
 f"<h3 id='shap'>SHAP</h3><details open><summary>Code</summary><pre>{esc(SHAP_PY)}</pre></details>{''.join(shap_fig(a) for a in ARMS)}")
html = f"""<!doctype html><meta charset=utf-8><title>DM1 1:3 split all methods</title>
<style>body{{font-family:system-ui;max-width:1350px;margin:2em auto;line-height:1.45;padding:0 1em}}.t{{border-collapse:collapse;font-size:11.5px}}.t td,.t th{{border:1px solid #ccc;padding:2px 7px}}.box{{background:#f4f7fb;border-left:4px solid #3a6ea5;padding:.6em 1em;margin:1em 0}}code,pre{{background:#f0f0f0}}pre{{padding:8px;overflow:auto;font-size:11px}}details{{margin:.5em 0}}small{{color:#666;font-weight:normal}}</style>
<h1>DM1: every PDF method on a 1:3, covariate-re-randomised split</h1>
<p><i>Replication in <code>split_1to3/</code> of the all-methods analysis with a new split (25% test per arm; test:train = 1:3). The earlier analyses are untouched. Simulated data.</i></p>
<div class="box"><b>Bottom line</b><ol>
<li><b>New split:</b> stratified on outcome quartiles, then re-randomised on baseline covariates (first of 5000 stratified draws in the best 2% by Mahalanobis distance). Worst covariate imbalance is 0.21&ndash;0.27 SD (random 1:3 splits: median 0.35 SD; old 80/20 split: 0.30&ndash;0.45 SD on the same features). Train/test n = {', '.join(f"{r.arm[:3]} {r.train}/{r.test}" for r in nsplit.itertuples())}.</li>
<li><b>All PDF methods were run</b> (10 covariate-track, 7 ML-track, plus tuning, permutation importance, SHAP) for the continuous outcome and the responder label in each arm; every method has its code, CV and test results, and prediction plots/tables below.</li>
<li><b>Covariate and ML models are parallel alternatives, not a pipeline</b> (section 3). They share only the data, split, folds and metrics.</li>
<li>Results (sections 4-8) are in the tables below; robustness against the old split is in section 9.</li></ol></div>
<h2>1. The 1:3 re-randomised split</h2>
<p><b>Procedure</b> (fixed before looking at any model; the test outcomes are never used except to build 4 outcome-quantile strata, as the PDF suggests for continuous outcomes): per arm, draw K=5000 candidate splits with <code>train_test_split(test_size=0.25, stratify=outcome quartile, random_state=seed)</code>; score each by the Mahalanobis distance M between train and test covariate means; accept candidates in the best 2% of M; use the first accepted seed (Morgan &amp; Rubin re-randomisation, so the split stays random among balanced ones). Seed, M and the candidate list are in <code>results/split_candidates.csv</code>.</p>
{split_fig()}{tbl(bal)}<p>Outcome distribution and responder share stay matched (columns outcome_KS_p, responder_share_diff). Note that balance on <i>measured</i> traits does not guarantee balance on unmeasured ones, and re-randomisation does not remove the sampling noise of a test set of 41&ndash;43 patients.</p>
<h2>2. Setup common to all methods</h2><ul><li>Features: log10 CTG, mosaicism, age at onset, disease duration, myotonia severity, muscle strength, PR interval, cognition, CK, insulin resistance, albumin (not in Mexiletine: constant), BMI + dummies; age omitted (= onset + duration). z-scored with <em>train</em> mean/sd only, applied unchanged to test.</li>
<li>Repeated stratified 5-fold CV (3 repeats, same folds for every method) on train; test scored once (<code>results/test_scoreboard.csv</code>). Cutoff for recall/precision/accuracy = Youden J on the train out-of-fold scores.</li>
<li>'Top-4 covariates' rows (poly, piecewise, spline) choose their 4 covariates by |correlation with the target| <em>inside each training fit</em>, so no information from the test patients, or from the main project's older analyses, enters the new rows.</li>
<li>Metrics: RMSE, MAE, R&sup2; (relative to the test-set mean, as the PDF defines it); ROC-AUC, recall, precision, accuracy. 95% CIs: 2000 bootstrap resamples of the test patients.</li></ul>
<h2>3. Are covariate models and ML models parallel or dependent?</h2>{svg}
<p><b>Parallel.</b> The PDF presents them as two tracks that answer the same hackathon question ("can ML identify additional predictors and improve stratification beyond covariate modelling?"), so each track is fitted independently from the same training rows and judged on the same test patients. Neither needs the other's output. Differences in purpose: covariate models are chosen for <i>which variables matter and how</i> (coefficients, selection); ML models for <i>predictive accuracy</i> (importance is derived afterwards by permutation/SHAP).</p>
<p><b>Where they can be chained</b> (optional, not done here to keep the comparison clean): use LASSO/stepwise to pre-select covariates and feed those to a forest or XGBoost; or use ML importance to decide which covariates deserve a GAM or spline. Several methods straddle the line (LASSO selects and predicts, GAM is interpretable and flexible). If a chain is used, the selection step must happen inside each training fold, as the 'top-4 covariates' rows do here. The only dependence in this analysis is the final comparison of what each method selected (section 6).</p>
<h2>4. Methods: code and prediction results</h2><p>Contents: {''.join(f"<a href='#{m['id']}'>[{m['id']}]</a> " for m in METHODS)} <a href='#tuning'>[tuning]</a> <a href='#perm'>[perm]</a> <a href='#shap'>[shap]</a></p>
<details><summary>Shared R helpers used by every covariate method (model constructors, term extraction)</summary><pre>{esc(SHARED_R)}</pre></details><details><summary>R driver: CV loop (stage=cv) and test fit/predict (stage=test)</summary><pre>{esc(STAGE_R)}</pre></details>
<h2>4a. Covariate-modelling track (R)</h2>{sec_cov}<h2>4b. Machine-learning track (Python)</h2><details><summary>Shared Python helpers</summary><pre>{esc(SHARED_PY)}\n\n{esc(FIT_PY)}</pre></details>{sec_ml}
<h2>5. Supporting methods</h2>{support}
<h2>6. Scoreboards and covariate comparison</h2>
<h3>Test RMSE per arm (continuous outcome) and train CV RMSE - all methods</h3>{tbl(master('reg','RMSE',None))}<h3>Test ROC-AUC per arm (responder label) and train CV AUC - all methods</h3>{tbl(master('bin','AUC',None))}
<h3>Best covariate model vs best ML model, each chosen by TRAIN CV only (paired bootstrap on test)</h3>{tbl(sc2[["arm","task","cov_method","cov_cv","cov_test","ml_method","ml_cv","ml_test","test_diff_cov_better","95% CI"]])}
<h3>Which covariates did each method use?</h3><p>Methods (of 16) using a covariate with weight &ge;0.5, top 3 per arm: {imp_note}</p>{''.join(png(ARES / f'cov_matrix_{a}_{t}.png') for a in ARMS for t in ('reg','bin'))}
<h2>7. PCA (unsupervised)</h2>{''.join(pca_fig(a) for a in ARMS)}
<h2>8. Sensitivity analyses</h2><h3>8a. Tuned vs untuned</h3>{tbl(tus)}<h3>8b. Do train-CV ranks predict test ranks?</h3>{tbl(ag)}<h3>8c. Cutoff: train-OOF Youden J (used) vs 0.5</h3>{tbl(cs)}
<h2>9. Robustness against the old 80/20 split (all_methods analysis)</h2><p>Same methods, different patients in train/test and a different test size. Spearman correlation of method ranks (test and CV) between the two analyses; 'best' = best method on the test set of each analysis.</p>{tbl(ovn)}
<h2>10. Caveats</h2><ul><li>Test sets are 41&ndash;43 patients per arm: gaps below the bootstrap CIs are not evidence of a better method.</li>
<li><b>Not an independent confirmation of the main project.</b> The same 500 patients are used; the new test patients partly belonged to the old train set and the old test outcomes were seen earlier. Methods here are generic and no choice was tuned to old results, but treat this as a robustness check of the split, not new data.</li>
<li>Re-randomisation chose the split on covariates only; this does not make the resulting test metric optimistic, but it makes the test set more representative on the measured traits than a single random draw.</li>
<li>Importance (permutation, SHAP) explains models, not biology; correlated covariates (CTG vs myotonia severity) share credit.</li>
<li>Best subset is continuous-outcome only; logistic regression is classification only; the smoothing spline is univariate.</li></ul>
<h2>11. Reproduce and AI disclosure</h2><pre>bash split_1to3/run_split1to3.sh     # n00 split, s01 export, R CV, ML CV, PCA, CV scoreboard, covariate comparison, s06 test scoring (guarded), tables; then python split_1to3/src/n08_report.py</pre>
<p>AI use: Claude Code (Anthropic) wrote and ran all code and drafted this report; numbers are regenerated by the scripts; the analyst remains accountable for the results. Per-patient test predictions: <code>results/test_predictions.csv</code>.</p>"""
(AREP / "summary_split1to3.html").write_text(html); print("wrote", len(html) // 1024, "KB")
