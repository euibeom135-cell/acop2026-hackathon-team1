"""Per-method figure / table helpers shared by step5 (CV, train only) and step6 (locked test predictions).
Report layer only: reads results/*.csv, draws PNGs into reports/steps/figs/. Never recomputes a model or a test prediction."""
from data import *
import re, shutil
from functools import lru_cache
from sklearn.metrics import roc_curve, roc_auc_score
from step5 import WATCH, SET, MLW

COV = ["lm / glm (all covariates)", "Stepwise both (BIC)", "Best subset (leaps, BIC, nvmax=10)", "Ridge (glmnet)", "LASSO (glmnet, lambda.min)",
       "Elastic net (glmnet, alpha=.5)", "GAM (mgcv, s(k=5), REML, select)", "PCR (prcomp, k by 5-fold CV)"]
KIND = {COV[0]: "coef", COV[1]: "coef", COV[2]: "coef", COV[3]: "path", COV[4]: "path", COV[5]: "path", COV[6]: "gam", COV[7]: "pca",
        "Decision tree": "tree", "Random forest": "imp", "XGBoost": "imp"}                    # others: uniform prediction grid only
VAR = [("untuned", "(untuned)", "#f4a582"), ("tuned", "(tuned, GridSearchCV)", "#b2182b")]    # ML variants: label, suffix, colour
slug = lambda m: re.sub(r"[^a-z0-9]+", "_", short(m).lower()).strip("_")

# ---------- series: [(label, colour, {task: method name in CSVs})] ----------
def series(m):
    if m in COV: return [("", FC["Covariate"], {"reg": m, "bin": m})]
    if m == "Baseline": return [("", FC["Baseline"], {"reg": "Mean only", "bin": "Prevalence only"})]
    return [(lab, col, {t: f"{m} {suf}" for t in ("reg", "bin")}) for lab, suf, col in VAR]

# ---------- getters -> DataFrame(obs, pred) or None ----------
@lru_cache(None)
def _cvfile(pref, a, t): return r(f"{pref}_{a}_{t}_cv_preds.csv")
@lru_cache(None)
def _obs(a, t): return r(f"features_train_{a}.csv")["y" if t == "reg" else "label"].to_numpy()
def cv_get(a, t, m):
    """Out-of-fold prediction averaged over CV repeats; observed = train row (0-based positional index)."""
    for pref in ("r", "ml"):
        d = _cvfile(pref, a, t); d = d[d.method == m]
        if len(d):
            g = d.groupby("row").pred.mean(); return pd.DataFrame({"obs": _obs(a, t)[g.index.to_numpy()], "pred": g.to_numpy()})
    return None
@lru_cache(None)
def _tp(): return r("test_predictions.csv")            # the single locked test scoring; used as is
def test_get(a, t, m):
    d = _tp(); d = d[(d.arm == a) & (d.task == t) & (d.method == m)].sort_values("row")
    return d[["obs", "pred"]].reset_index(drop=True) if len(d) else None

def r2(o, p): return 1 - np.sum((o - p) ** 2) / np.sum((o - np.mean(o)) ** 2)

def pred_grid(getter, m, name):
    """2x3 grid: row 0 = continuous outcome obs-vs-pred, row 1 = responder-label ROC; cols = arms. One or two series (ML untuned/tuned)."""
    S = series(m); fig, ax = plt.subplots(2, 3, figsize=(14, 8.4))
    for i, t in enumerate(["reg", "bin"]):
        for j, a in enumerate(ARMS):
            x = ax[i, j]; got = [(lab, col, getter(a, t, mm[t])) for lab, col, mm in S]; got = [g for g in got if g[2] is not None]
            if not got:
                x.text(.5, .5, "not applicable for this outcome", ha="center", va="center", fontsize=9, color="#777"); x.set_xticks([]); x.set_yticks([]); x.set_title(f"{a}: {TASKN[t]}", fontsize=9); continue
            ttl = []
            for lab, col, d in got:
                d = d.dropna()
                if t == "reg":
                    x.scatter(d.obs, d.pred, s=16, color=col, alpha=.75, label=lab or None); ttl.append(f"{lab + ' ' if lab else ''}R2 {r2(d.obs.to_numpy(), d.pred.to_numpy()):.2f}")
                else:
                    f, tp, _ = roc_curve(d.obs, d.pred); au = roc_auc_score(d.obs, d.pred) if d.obs.nunique() > 1 else np.nan
                    x.plot(f, tp, color=col, lw=1.6, label=lab or None); ttl.append(f"{lab + ' ' if lab else ''}AUC {au:.2f}")
            if t == "reg":
                lo = min(min(g[2].obs.min(), g[2].pred.min()) for g in got); hi = max(max(g[2].obs.max(), g[2].pred.max()) for g in got)
                x.plot([lo, hi], [lo, hi], color="#888", ls="--", lw=.8); x.set_xlabel("observed", fontsize=8); x.set_ylabel("predicted", fontsize=8)
            else:
                x.plot([0, 1], [0, 1], color="#888", ls="--", lw=.8); x.set_xlabel("1 - specificity", fontsize=8); x.set_ylabel("sensitivity", fontsize=8)
            x.set_title(f"{a}: {TASKN[t]}  ({'; '.join(ttl)})", fontsize=8.5); x.tick_params(labelsize=7)
            if len(got) > 1 or got[0][0]: x.legend(fontsize=7, loc="lower right" if t == "bin" else "upper left")
    fig.tight_layout(); return fig_html(fig, name)

# ---------- characteristic figures ----------
@lru_cache(None)
def _terms(a, t): return r(f"r_{a}_{t}_test_terms.csv")
def full_terms(a, t, m):
    d = _terms(a, t); return d[(d.method == m) & (d.fit == "train")]

def coef_grid(m, name):
    """Full-train coefficients (z-scored numerics, 0/1 dummies; label = log-odds); selected / non-zero terms only. rows = outcome, cols = arm."""
    fig, ax = plt.subplots(2, 3, figsize=(14, 9))
    for i, t in enumerate(["reg", "bin"]):
        for j, a in enumerate(ARMS):
            x = ax[i, j]; d = full_terms(a, t, m).copy(); x.set_title(f"{a}: {TASKN[t]}", fontsize=9)
            if d.empty: x.text(.5, .5, "not applicable for this outcome" if t == "bin" and m == COV[2] else "no non-zero terms", ha="center", va="center", fontsize=9, color="#777"); x.set_xticks([]); x.set_yticks([]); continue
            d = d.reindex(d.coef.abs().sort_values().index); y = np.arange(len(d)); x.barh(y, d.coef, color=["#b2182b" if v < 0 else "#2166ac" for v in d.coef])
            x.set_yticks(y); x.set_yticklabels([nice(q) for q in d.term], fontsize=7); x.axvline(0, color="#444", lw=.7); x.tick_params(axis="x", labelsize=7)
    fig.suptitle("Full-train coefficients (blue positive, red negative)", fontsize=9); fig.tight_layout(); return fig_html(fig, name)

def imp_grid(m, name):
    """CV importance of the tuned model, mean over folds, top 10. Returns (html, caption with the top term's TRAIN signal verdict)."""
    fig, ax = plt.subplots(2, 3, figsize=(14, 8.4)); s = sig(); tops = []
    for i, t in enumerate(["reg", "bin"]):
        for j, a in enumerate(ARMS):
            d = r(f"ml_{a}_{t}_cv_importance.csv"); d = d[d.method == f"{m} (tuned, GridSearchCV)"].groupby("term").importance.mean().sort_values().tail(10)
            x = ax[i, j]; x.barh(np.arange(len(d)), d.values, color=FC["ML"]); x.set_yticks(np.arange(len(d))); x.set_yticklabels([nice(q) for q in d.index], fontsize=7)
            x.set_title(f"{a}: {TASKN[t]}", fontsize=9); x.tick_params(axis="x", labelsize=7)
            v = s[(s.arm == a) & (s.task == t) & (s.covariate == d.index[-1])].verdict; tops.append(f"{a} {TASKN[t]}: {nice(d.index[-1])} (train verdict {v.iloc[0] if len(v) else 'n/a'})")
    fig.suptitle(f"{m} (tuned): mean CV importance over folds", fontsize=9); fig.tight_layout()
    return fig_html(fig, name), note("Top term per panel: " + "; ".join(tops) + ".")

def pca_fig(name):
    """Scree + cumulative variance (row 0) and PC1-vs-PC2 loadings biplot (row 1) from the TRAIN PCA, one column per arm."""
    fig, ax = plt.subplots(2, 3, figsize=(14, 8.6))
    for j, a in enumerate(ARMS):
        v = r(f"pca_{a}_var.csv"); L = r(f"pca_{a}_loadings.csv", index_col=0); x = ax[0, j]; k = np.arange(len(v))
        x.bar(k, v.var_ratio, color=FC["Covariate"]); x2 = x.twinx(); x2.plot(k, v.cum, color="#b2182b", marker="o", ms=3); x2.set_ylim(0, 1.02); x2.tick_params(labelsize=7)
        x.set_xticks(k); x.set_xticklabels(v.PC, rotation=90, fontsize=6.5); x.set_title(f"{a}: scree (bars) and cumulative (line)", fontsize=9); x.tick_params(axis="y", labelsize=7)
        b = ax[1, j]
        for q, (p1, p2) in L[["PC1", "PC2"]].iterrows():
            b.arrow(0, 0, p1, p2, color="#555", lw=.8, head_width=.012, length_includes_head=True); b.text(p1 * 1.07, p2 * 1.07, nice(q), fontsize=6.5, ha="center")
        b.axhline(0, color="#ccc", lw=.6); b.axvline(0, color="#ccc", lw=.6); b.set_xlabel(f"PC1 ({v.var_ratio[0]:.0%})", fontsize=8); b.set_ylabel(f"PC2 ({v.var_ratio[1]:.0%})", fontsize=8); b.set_title(f"{a}: loadings biplot", fontsize=9); b.tick_params(labelsize=7)
        m = max(L[["PC1", "PC2"]].abs().max()) * 1.35; b.set_xlim(-m, m); b.set_ylim(-m, m)
    fig.tight_layout(); return fig_html(fig, name)

def diag_imgs(kind):
    """Copy the pre-rendered train-only diagnostic PNGs into figs/ (prefix diag_) and lay them out 3 per row (cols = arms; rows = outcomes)."""
    out = ""
    for t in ["reg", "bin"]:
        out += f"<p class=cap>{TASKN[t].capitalize()}</p><div style='display:flex;gap:6px;flex-wrap:wrap'>"
        for a in ARMS:
            fn = f"{kind}_{a}_{t}.png"; shutil.copy(RES / "diag_figs" / fn, FIGDIR / f"diag_{fn}")
            out += f'<img src="figs/diag_{fn}" alt="{fn}" style="width:32%;min-width:300px">'
        out += "</div>"
    return out

def gam_terms_line():
    parts = []
    for t in ["reg", "bin"]:
        for a in ARMS:
            d = full_terms(a, t, COV[6]); parts.append(f"{a} {TASKN[t]}: " + ("; ".join(nice(q) for q in d.term) or "none"))
    return note("Terms with p&lt;0.05 (smooth or dummy), full-train GAM. " + " | ".join(parts) + ".")

def pcr_k_line():
    return note("Components kept by 5-fold CV (full-train fit; maximum 12): " + "; ".join(f"{a} {TASKN[t]}: {len(full_terms(a, t, COV[7]))}" for t in ["reg", "bin"] for a in ARMS) + ". The PCA below is unsupervised; later components are not necessarily dropped.")

def retained_line(m):
    if m in (COV[0], COV[3]): return note("Retained terms: all covariates (no selection; " + ("ridge shrinks but never zeroes" if m == COV[3] else "full model") + ").")
    if m == COV[6]: return gam_terms_line()
    if m == COV[7]: return pcr_k_line()
    if m not in COV: return ""
    parts = []
    for t in ["reg", "bin"]:
        for a in ARMS:
            d = full_terms(a, t, m); parts.append(f"{a} {TASKN[t]}: " + (", ".join(f"{nice(q)} ({v:+.2f})" for q, v in zip(d.term, d.coef)) if len(d) else ("n/a" if t == "bin" and m == COV[2] else "none")))
    return "<p class=note><b>Retained terms (full-train):</b><br>" + "<br>".join(parts) + "</p>"

def characteristic(m, step):
    """Method-specific figure (train-only fits; step5 only)."""
    k, s = KIND.get(m), slug(m)
    if k == "coef": return coef_grid(m, f"s{step}_{s}_coef")
    if k == "path": return "<p class=cap>Coefficient path vs log(lambda), lambda.min marked (train-only fit)</p>" + diag_imgs("glmnet_path") + coef_grid(m, f"s{step}_{s}_coef")
    if k == "gam": return "<p class=cap>Partial smooths (train-only fit)</p>" + diag_imgs("gam")
    if k == "pca": return pca_fig(f"s{step}_pca")
    if k == "tree": return "<p class=cap>Fitted tree (train-only fit)</p>" + diag_imgs("tree")
    if k == "imp": h, cap = imp_grid(m, f"s{step}_{s}_imp"); return h + cap
    return note("No natural diagram for this method; see the prediction grid below.")

# ---------- code excerpts ----------
R_PAT = {COV[0]: ('M[["lm / glm', 1), COV[1]: ('M[["Stepwise', 2), COV[2]: ('M[["Best subset', 3), COV[3]: ("gn <- function", 4), COV[4]: ("gn <- function", 4), COV[5]: ("gn <- function", 4),
         COV[6]: ('M[["GAM', 5), COV[7]: ('M[["PCR', 7)}
def code_excerpt(m):
    if m in R_PAT:
        L = (ROOT / "src" / "r_covariate.R").read_text().splitlines(); pat, n = R_PAT[m]; i = next(k for k, l in enumerate(L) if pat in l); txt = "\n".join(L[i:i + n])
        if R_PAT[m][0] == "gn <- function": txt += '\n# ' + {COV[3]: 'M[["Ridge (glmnet)"]] <- gn(0)', COV[4]: 'M[["LASSO (glmnet, lambda.min)"]] <- gn(1)', COV[5]: 'M[["Elastic net (glmnet, alpha=.5)"]] <- gn(0.5)'}[m]
        src = "r_covariate.R"
    elif m == "Baseline": return ""
    else:
        L = (ROOT / "src" / "ml_models.py").read_text().splitlines(); keep = [l for l in L if f'add("{m}"' in l or l.startswith("TREE_GRID") and m in ("Decision tree", "Random forest")]
        keep += [l for l in L if "GridSearchCV(mk(r)" in l]; txt = "\n".join(x.strip() for x in keep); src = "ml_models.py"
    return f"<details><summary>Code that ran ({src}, excerpt)</summary><pre style='font-size:11px;background:#f6f8fa;padding:.5em;overflow-x:auto'>{esc(txt)}</pre></details>"

# ---------- CV result row ----------
def cv_rows(m):
    c = cv(); S = series(m); rows = []
    for lab, col, mm in S:
        for t in ["reg", "bin"]:
            met = "RMSE" if t == "reg" else "AUC"; row = {"Variant": lab or "-", "Outcome": f"{TASKN[t]} (CV {met})"}
            for a in ARMS:
                v = c[(c.arm == a) & (c.task == t) & (c.method == mm[t])]; row[a] = "n/a" if v.empty else f"{v.iloc[0][met]:.3f} &plusmn; {v.iloc[0][met + '_sd']:.3f}"
            rows.append(row)
    return pd.DataFrame(rows)

def rationale(m):
    if m in SET: return f"<b>Settings:</b> {SET[m]}. <b>Watch out:</b> {WATCH[m]}"
    if m == "Baseline": return f"<b>Reference:</b> mean (continuous) / prevalence (label). {WATCH['Mean only']} {WATCH['Prevalence only']}"
    u, g, w = MLW[m]; return f"<b>Untuned:</b> {u}. <b>Tuned grid (inner 3-fold):</b> {g}. <b>Watch out:</b> {w}"
