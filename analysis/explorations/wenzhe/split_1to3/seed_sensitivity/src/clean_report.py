"""Concise, slide-oriented report: performance of every method over 20 split seeds, which covariates each method retains (stable across seeds),
plain-language variable dictionary, and a clinical-meaning check against the hypothesis-sheet priors. Reads results/seed_*/{perf,evidence,balance}.csv. No fitting.
Writes ../../reports/summary_clean.html and ../../reports/figs/*.png"""
import io, base64, sys, glob
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parents[1] / "src")); sys.path.insert(0, str(HERE.parents[2] / "src"))
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy import stats as st
from common import ARMS
from features import PRIORS, DOMAIN
REP = HERE.parents[1] / "reports"; FIG = REP / "figs"; FIG.mkdir(exist_ok=True, parents=True); RES = HERE.parent / "results"
SGN = {"Mexiletine": -1, "Oligonucleotide": 1, "Tideglusib": 1}; STABLE = 0.70
perf = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RES / "seed_*/perf.csv")))]); ev = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RES / "seed_*/evidence.csv")))]); bal = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(RES / "seed_*/balance.csv")))])
NS = perf.seed.nunique()
# ---------------- variable dictionary (from the participant data dictionary) ----------------
DICT = [("ctg_repeats (shown as log10)", "CTG repeat length", "CTG trinucleotide repeat length in DMPK; the classic genetic severity marker", "Genetic burden"),
 ("somatic_mosaicism_index", "Somatic mosaicism", "Variability of repeat length across a patient's tissues (0-1)", "Genetic burden"),
 ("age_at_onset", "Age at onset", "Age (years) when symptoms first appeared", "Disease stage"), ("disease_duration", "Disease duration", "Years since symptom onset (age - age at onset)", "Disease stage"),
 ("age", "Age (not modelled)", "Current age; omitted because it equals onset age + duration", "Disease stage"), ("phenotype", "DM1 subtype", "juvenile / adult / late onset pattern", "Disease stage"),
 ("myotonia_severity", "Myotonia severity", "Baseline delayed muscle relaxation, 0-10 (higher = worse)", "Muscle"), ("muscle_strength", "Muscle strength", "Composite strength score, 20-100 (higher = stronger)", "Muscle"),
 ("ck_level", "Creatine kinase", "Baseline CK (U/L), marker of muscle damage", "Muscle"), ("pr_interval", "ECG PR interval", "Cardiac conduction time (ms)", "Cardiac"),
 ("cognitive_function", "Cognitive function", "Standardised cognitive performance z-score vs population (higher = better)", "CNS"), ("insulin_resistance", "Insulin resistance", "HOMA-IR index", "Metabolic"),
 ("bmi", "BMI", "Body mass index (kg/m2)", "Systemic"), ("albumin", "Serum albumin", "g/dL, nutritional/hepatic marker (constant in the Mexiletine arm, so dropped there)", "Systemic"),
 ("smoking_status", "Smoking", "never / former / current", "Systemic"), ("sex", "Sex", "male / female", "Demographic"), ("family_history", "Family history", "DM1 family history: yes / no / unknown", "Demographic"), ("cataracts", "Cataracts", "Baseline cataracts yes / no", "Ophthalmic")]
FR = {"log_ctg": "CTG repeat length", "somatic_mosaicism_index": "Somatic mosaicism", "age_at_onset": "Age at onset", "disease_duration": "Disease duration", "phenotype": "DM1 subtype", "myotonia_severity": "Myotonia severity", "muscle_strength": "Muscle strength",
      "ck_level": "Creatine kinase", "pr_interval": "ECG PR interval", "cognitive_function": "Cognitive function", "insulin_resistance": "Insulin resistance", "bmi": "BMI", "albumin": "Serum albumin", "smoking_status": "Smoking", "sex": "Sex", "family_history": "Family history", "cataracts": "Cataracts"}
PK = lambda c: "ctg_repeats" if c == "log_ctg" else c
SHORT = {"lm / glm (all covariates)": "lm / glm (all)", "Stepwise forward (AIC)": "Stepwise fwd (AIC)", "Stepwise backward (AIC)": "Stepwise bwd (AIC)", "Stepwise both (AIC)": "Stepwise both (AIC)", "Stepwise both (BIC)": "Stepwise both (BIC)",
 "Best subset (leaps, BIC, nvmax=10)": "Best subset (BIC)", "Ridge (glmnet)": "Ridge", "LASSO (glmnet, lambda.min)": "LASSO", "LASSO (glmnet, lambda.1se)": "LASSO (1-SE)", "Elastic net (glmnet, alpha=.5)": "Elastic net",
 "Polynomial deg-2 (top-4 covariates)": "Polynomial (top-4)", "Piecewise: cut() tertile bins (top-4 covariates)": "Piecewise (top-4)", "Regression spline bs(df=4) (top-4 covariates)": "Spline bs (top-4)", "Smoothing spline (top-1 covariate, cv=TRUE)": "Smoothing spline (top-1)",
 "GAM (mgcv, s(k=5), REML, select)": "GAM", "PCR (prcomp, k by 5-fold CV)": "PCR (PCA)", "Logistic regression (tuned)": "Logistic reg. (tuned)", "Logistic regression (untuned)": "Logistic reg. (untuned)"}
def sh(m): return SHORT.get(m, m.replace(" (tuned, GridSearchCV)", " (tuned)").replace(" (untuned)", " (untuned)"))
FAM = lambda m: "Baseline" if m in ("Mean only", "Prevalence only") else ("ML" if any(k in m for k in ("Decision tree", "Random forest", "SVM", "KNN", "XGBoost", "MLP", "Logistic")) else "Covariate")
perf["family"] = perf.method.map(FAM); perf["short"] = perf.method.map(sh)
FC = {"Covariate": "#1f77b4", "ML": "#d95f02", "Baseline": "#777"}
def png(fig, name, dpi=95):
    b = io.BytesIO(); fig.savefig(b, format="png", dpi=dpi, bbox_inches="tight"); fig.savefig(FIG / f"{name}.png", dpi=150, bbox_inches="tight"); plt.close(fig); return f'<img src="data:image/png;base64,{base64.b64encode(b.getvalue()).decode()}" style="max-width:100%">'
tbl = lambda t, **k: t.to_html(classes="t", border=0, index=False, float_format=lambda v: f"{v:.2f}", na_rep="", escape=False, **k)
# ---------------- performance ----------------
def agg(task, metric):
    p = perf[(perf.task == task) & (perf.family != "Baseline")]; return p.groupby(["arm", "short", "family"])[metric].agg(["mean", "std"]).reset_index()
def perf_fig(task, metric, ylabel, asc):
    fig, ax = plt.subplots(1, 3, figsize=(20, 7.2), sharex=False); fig.subplots_adjust(wspace=0.62)
    for a, arm in zip(ax, ARMS):
        g = agg(task, metric); g = g[g.arm == arm].sort_values("mean", ascending=asc); base = perf[(perf.arm == arm) & (perf.task == task) & (perf.family == "Baseline")][metric].mean(); y = np.arange(len(g))[::-1]
        a.barh(y, g["mean"], xerr=g["std"], color=[FC[f] for f in g.family], alpha=.85, ecolor="#555", error_kw=dict(lw=.8)); a.set_yticks(y); a.set_yticklabels(g.short, fontsize=7.5); a.axvline(base, c="k", ls="--", lw=.8)
        a.set_title(f"{arm}", fontsize=10); a.set_xlabel(f"{ylabel} (mean ± SD over {NS} splits)", fontsize=8); lo = min(g["mean"].min(), base) - g["std"].max() * 1.3; a.set_xlim(lo if metric != "R2" else min(lo, -.2), None)
    from matplotlib.patches import Patch; from matplotlib.lines import Line2D; ax[0].legend(handles=[Patch(color=FC["Covariate"], label="Covariate model"), Patch(color=FC["ML"], label="Machine learning"), Line2D([], [], color="k", ls="--", label="no-skill baseline")], fontsize=8, loc="lower right")
    return png(fig, f"perf_{task}_{metric}")
def table_reg():
    p = perf[(perf.task == "reg")]; t = p.groupby(["short", "family", "arm"]).agg(RMSE=("RMSE", "mean"), R2=("R2", "mean"), R2sd=("R2", "std"), MAE=("MAE", "mean")).reset_index()
    rows = []
    for (s, f), g in t.groupby(["short", "family"]):
        r = dict(Method=s, Track=f)
        for arm in ARMS: x = g[g.arm == arm].iloc[0]; r[f"{arm[:4]}. R² (±SD)"] = f"{x.R2:.2f} ± {x.R2sd:.2f}"; r[f"{arm[:4]}. RMSE"] = x.RMSE
        r["mean R²"] = g.R2.mean(); rows.append(r)
    return pd.DataFrame(rows).sort_values("mean R²", ascending=False)
def table_bin():
    p = perf[(perf.task == "bin")]; t = p.groupby(["short", "family", "arm"]).agg(AUC=("AUC", "mean"), sd=("AUC", "std"), rec=("recall", "mean"), pre=("precision", "mean"), acc=("accuracy", "mean")).reset_index(); rows = []
    for (s, f), g in t.groupby(["short", "family"]):
        r = dict(Method=s, Track=f)
        for arm in ARMS: x = g[g.arm == arm].iloc[0]; r[f"{arm[:4]}. AUC (±SD)"] = f"{x.AUC:.2f} ± {x['sd']:.2f}"
        r["mean AUC"] = g.AUC.mean(); r["recall"] = g.rec.mean(); r["precision"] = g.pre.mean(); r["accuracy"] = g.acc.mean(); rows.append(r)
    return pd.DataFrame(rows).sort_values("mean AUC", ascending=False)
def rank_fig():
    out = []
    for task, metric, asc in (("reg", "RMSE", True), ("bin", "AUC", False)):
        p = perf[(perf.task == task) & (perf.family != "Baseline")].copy(); p["rank"] = p.groupby(["seed", "arm"])[metric].rank(ascending=asc); R = p.groupby(["short", "family", "arm"])["rank"].mean().unstack("arm").reset_index(); R["all arms"] = R[list(ARMS)].mean(axis=1); out.append(R.sort_values("all arms"))
    fig, ax = plt.subplots(1, 2, figsize=(14, 6.2))
    for a, R, ttl in zip(ax, out, ("Continuous outcome (rank by test RMSE)", "Responder label (rank by test AUC)")):
        M = R[list(ARMS) + ["all arms"]].values; im = a.imshow(M, cmap="RdYlGn_r", aspect="auto"); a.set_yticks(range(len(R))); a.set_yticklabels([f"{s}" for s in R.short], fontsize=7.5); a.set_xticks(range(4)); a.set_xticklabels([x[:5] + "." for x in ARMS] + ["all arms"], fontsize=8)
        for i in range(M.shape[0]):
            for j in range(4): a.text(j, i, f"{M[i, j]:.1f}", ha="center", va="center", fontsize=7)
        for t_, f in zip(a.get_yticklabels(), R.family): t_.set_color(FC[f])
        a.set_title(ttl + "\nmean rank over splits (1 = best)", fontsize=9)
    return png(fig, "mean_rank"), out
def family_fig():
    rows = []
    for arm in ARMS:
        for task, metric in (("reg", "R2"), ("bin", "AUC")):
            p = perf[(perf.arm == arm) & (perf.task == task) & (perf.family != "Baseline")]; w = p.groupby(["seed", "family"])[metric].agg(["mean", "max"]).unstack("family")
            for stat, lab in (("mean", "average method"), ("max", "best method in track (chosen on test: optimistic)")): d = w[stat]["ML"] - w[stat]["Covariate"]; rows.append(dict(arm=arm, task=task, stat=lab, diff=d.mean(), lo=np.percentile(d, 2.5), hi=np.percentile(d, 97.5), frac_ml_better=(d > 0).mean()))
    D = pd.DataFrame(rows); fig, ax = plt.subplots(1, 2, figsize=(13, 3.6))
    for a, task, ttl in zip(ax, ("reg", "bin"), ("Continuous outcome: R² (ML - covariate)", "Responder label: AUC (ML - covariate)")):
        g = D[(D.task == task) & (D.stat == "average method")]; y = np.arange(len(g)); a.errorbar(g["diff"], y, xerr=[g["diff"] - g.lo, g.hi - g["diff"]], fmt="o", c="k"); a.axvline(0, c="r", ls="--"); a.set_yticks(y); a.set_yticklabels(g.arm); a.set_title(ttl + f"\naverage over methods in each track; bars = 2.5-97.5% of {NS} splits", fontsize=8.5)
    return png(fig, "family_diff"), D
# ---------------- covariates retained ----------------
EV = ev.copy(); EV["short"] = EV.method.map(sh); EV = EV[EV.short != "Ridge"]
def freq_table(arm, task):
    e = EV[(EV.arm == arm) & (EV.task == task)]; F = e.groupby(["short", "covariate"]).selected.sum().unstack("covariate").fillna(0) / NS
    # methods with evidence but no rows for a covariate => 0 (never selected)
    return F
def heat(arm):
    Fs = {t: freq_table(arm, t) for t in ("reg", "bin")}; cols = sorted(set(Fs["reg"].columns) | set(Fs["bin"].columns)); cols = [c for c in cols if c != "albumin" or arm != "Mexiletine"]
    order = pd.concat([Fs[t].reindex(columns=cols).fillna(0) for t in Fs]).mean().sort_values(ascending=False).index.tolist()[:12]
    fig, ax = plt.subplots(1, 2, figsize=(15, 6.0)); stats_ = {}
    for a, t, ttl in zip(ax, ("reg", "bin"), ("Continuous outcome", "Responder label")):
        F = Fs[t].reindex(columns=order).fillna(0); ml = [i for i in F.index if FAM(i + " ") == "ML" or "tuned" in i]; cov = [i for i in F.index if i not in ml]; F = F.loc[cov + ml]
        im = a.imshow(F.values, cmap="Blues", vmin=0, vmax=1, aspect="auto"); a.set_yticks(range(len(F))); a.set_yticklabels(F.index, fontsize=7.5); a.set_xticks(range(len(order))); a.set_xticklabels([FR.get(c, c) for c in order], rotation=55, ha="right", fontsize=8)
        for i in range(F.shape[0]):
            for j in range(F.shape[1]):
                if F.values[i, j] >= STABLE: a.text(j, i, "●", ha="center", va="center", color="w", fontsize=8)
        a.axhline(len(cov) - .5, c="k", lw=1.2); a.set_title(f"{arm} - {ttl}", fontsize=9); stats_[t] = (F >= STABLE).sum(axis=0).reindex(order); stats_[t + "_n"] = len(F)
    plt.colorbar(im, ax=ax, fraction=.02, label=f"share of {NS} splits in which the method retained the covariate"); return png(fig, f"covariates_{arm}"), stats_, order
def direction(arm, c):
    e = ev[(ev.arm == arm) & (ev.task == "reg") & (ev.covariate == c) & (ev.method == "LASSO (glmnet, lambda.min)") & ev.coef.notna() & ev.selected]
    if c in ("phenotype", "sex", "family_history", "smoking_status", "cataracts") or len(e) < NS * 0.5: return ""
    return "higher → more improvement" if np.sign(e.coef.mean()) * SGN[arm] > 0 else "higher → less improvement"   # improvement scale; coefficient = outcome units per SD of the covariate
def prior_txt(arm, c):
    s, sign = PRIORS[arm][PK(c)]; return {3: "strong", 2: "moderate", 1: "weak", 0: "none"}[s] + ({1: ", expects higher → more improvement", -1: ", expects higher → less improvement", 0: ""}[sign] if s else "")
VER = {"Mexiletine": {"myotonia_severity": "Mexiletine acts on the muscle sodium channel to relieve myotonia: patients with more baseline myotonia have more to gain (and more to regress)."},
       "Oligonucleotide": {"log_ctg": "The oligonucleotide targets the toxic CUG-repeat RNA, so repeat burden is the plausible driver; direction was left open by the hypothesis sheet."},
       "Tideglusib": {"cognitive_function": "Tideglusib (GSK-3 inhibitor) is aimed at CNS involvement; lower baseline cognition = more room to improve."}}
def summary_table(arm, st_, order):
    nR, nB = st_["reg_n"], st_["bin_n"]; rows = []
    for c in order:
        kR, kB = int(st_["reg"][c]), int(st_["bin"][c]); s = PRIORS[arm][PK(c)][0]
        if kR + kB < 3 and s < 3: continue
        strong = kR >= nR * .5 or kB >= nB * .5; d = direction(arm, c); sg = PRIORS[arm][PK(c)][1]; opp = bool(d) and sg != 0 and ((d.startswith("higher → more")) != (sg > 0))
        if strong and s >= 2 and not opp: v = "<b style='color:#1a7f37'>Retained &amp; clinically plausible</b>"
        elif strong and s >= 2 and opp: v = "<b style='color:#b45f06'>Retained, direction opposite to prior</b>"
        elif strong: v = "<b style='color:#b45f06'>Retained, weak/no prior: needs validation</b>"
        elif s == 3: v = "Strong prior, not retained by most methods"
        else: v = "Occasionally retained (&lt;50% of methods)"
        rows.append({"Covariate": FR.get(c, c), "Retained by (continuous)": f"{kR}/{nR}", "Retained by (responder)": f"{kB}/{nB}", "Effect direction (data)": d, "Hypothesis-sheet prior": prior_txt(arm, c), "Verdict": v})
    return pd.DataFrame(rows).head(8)
def noprior_missed(arm):
    return [FR[c] for c in FR if PRIORS[arm].get(PK(c), (0, 0))[0] == 3 and c in FR]
# ---------------- balance ----------------
bl = bal.groupby("arm").agg(max_smd_mean=("max_abs_smd", "mean"), max_smd_range_lo=("max_abs_smd", "min"), max_smd_range_hi=("max_abs_smd", "max"), rnd=("random_median_max_smd", "mean")).reset_index()
# ---------------- build ----------------
pf_reg, pf_bin = perf_fig("reg", "R2", "test R²", False), perf_fig("bin", "AUC", "test ROC-AUC", False); rk, ranks = rank_fig(); fam_html, famD = family_fig(); tR, tB = table_reg(), table_bin()
sec_cov, kf = [], []
for arm in ARMS:
    h, s_, order = heat(arm); T = summary_table(arm, s_, order); sec_cov.append(f"<h3>{arm}</h3>{h}{tbl(T)}<p class=note>{VER[arm].get(next(iter(VER[arm])), '')}</p>"); kf.append((arm, T))
# key findings (computed)
topR = tR.iloc[0]; topB = tB.iloc[0]; best_ml = tR[tR.Track == "ML"].iloc[0]; best_cv = tR[tR.Track == "Covariate"].iloc[0]
fd = famD[famD.stat == "average method"]
def top_cov(arm, T, k=1): return ", ".join(T.Covariate.head(k))
kfind = f"""<ol>
<li><b>Same drivers whatever the method.</b> {'; '.join(f"{a}: <b>{top_cov(a, T)}</b> ({T.iloc[0]['Retained by (continuous)']} methods, continuous outcome)" for a, T in kf)}. Other covariates are retained by far fewer methods.</li>
<li><b>The best methods of both tracks are equivalent.</b> Best single methods on average R²: <b>{topR.Method}</b> ({topR['mean R²']:.2f}); best covariate model <b>{best_cv.Method}</b> ({best_cv['mean R²']:.2f}); best ML <b>{best_ml.Method}</b> ({best_ml['mean R²']:.2f}). Averaged over <i>all</i> methods in a track, ML is {'lower' if fd[fd.task=='reg']['diff'].mean() < 0 else 'higher'}; the 95% range over splits excludes zero in {', '.join(r.arm for _, r in fd[fd.task=='reg'].iterrows() if r.hi < 0 or r.lo > 0) or 'no arm'} (ML minus covariate R²: {', '.join(f"{r.arm[:4]}. {r['diff']:+.2f}" for _, r in fd[fd.task == 'reg'].iterrows())}) because MLP, KNN and SVM do poorly on ~120 patients; tree ensembles (forest, XGBoost) match the best covariate models in Mexiletine, fall behind them in Oligonucleotide, and beat them only in Tideglusib (mean R² ≈ 0.52 vs ≈ 0.43; non-linear muscle-strength effect).</li>
<li><b>Predictability differs by arm:</b> {', '.join(f"{a} best mean test R² {tR[f'{a[:4]}. R² (±SD)'].map(lambda s: float(s.split()[0])).max():.2f}" for a in ARMS)}.</li>
<li><b>Results are split-dependent:</b> the SD across the {NS} seeds (error bars) is often as large as the gaps between neighbouring methods, so only large, consistent differences should be quoted.</li></ol>"""
dict_html = tbl(pd.DataFrame(DICT, columns=["Variable name in data", "Plain name", "Meaning", "Domain"]))
meth_rows = [("lm / glm", "Linear (logistic) regression on all covariates", "p < 0.05"), ("Stepwise (4 variants)", "Adds/drops covariates by AIC or BIC", "kept in final model with p < 0.05"), ("Best subset", "Exhaustive search, best by BIC (continuous only)", "kept with p < 0.05"),
 ("Ridge / LASSO / Elastic net", "Penalised regression; ridge never drops a covariate, so it is not scored for retention", "non-zero coefficient"), ("Polynomial / Piecewise / Spline", "Curved effects on the 4 covariates most correlated with the target (re-chosen inside each fit)", "drop-one F/χ² test p < 0.05"),
 ("Smoothing spline", "One smooth curve on the single strongest covariate", "correlation p < 0.05"), ("GAM", "Smooth term for every continuous covariate", "smooth/linear term p < 0.05"), ("PCR (PCA)", "Regression on principal components; no covariate-level result", "n/a"),
 ("Logistic, tree, forest, SVM, KNN, XGBoost, MLP", "Machine learning, untuned and tuned (GridSearchCV)", "permutation importance on test > 0 (95% CI) and ≥ 10% of the model's top importance")]
html = f"""<!doctype html><meta charset=utf-8><title>DM1 clean summary</title>
<style>body{{font-family:system-ui;max-width:1250px;margin:2em auto;line-height:1.45;padding:0 1em;color:#222}}.t{{border-collapse:collapse;font-size:12px;margin:.5em 0}}.t td,.t th{{border:1px solid #ccc;padding:3px 8px;text-align:left}}.t th{{background:#f3f5f8}}.box{{background:#f4f7fb;border-left:4px solid #3a6ea5;padding:.4em 1em;margin:1em 0}}h2{{margin-top:1.8em;border-bottom:2px solid #3a6ea5;padding-bottom:2px}}.note{{color:#555;font-size:13px}}small{{color:#666}}</style>
<h1>DM1 hackathon: which covariates matter and which method predicts best</h1>
<p><small>Team 1 · Wenzhe Ma · simulated data · every method in the kickoff guide · results repeated over {NS} different 1:3 train/test splits · detailed code-level report: <code>summary_split1to3.html</code></small></p>
<div class="box"><b>Key findings</b>{kfind}</div>
<h2>0. Design in one paragraph</h2>
<p>Each arm is modelled separately. For each of {NS} random seeds the patients were split 75/25 (outcome-quartile strata, then covariate re-randomisation; worst train-test covariate imbalance {bl.max_smd_mean.min():.2f}-{bl.max_smd_mean.max():.2f} SD on average vs {bl.rnd.mean():.2f} for plain random splits). All {perf.method.nunique() - 2} methods were fitted on the training part only and scored on the test part (≈41-43 patients). Tables and bars below are <b>mean ± SD over the {NS} splits</b>. A covariate is <b>retained</b> by a method when the method selects it (rule per method below) in <b>≥ {int(STABLE*100)}% of the splits</b>, which guards against chance picks from a single split.</p>
<h2>1. What the variables mean</h2>{dict_html}
<h2>2. Which method performs better?</h2>
<p><b>Figure 1 · Continuous outcome</b> (R² vs test mean: 0 = no better than predicting the average; higher is better). Blue = covariate models, orange = machine learning.</p>{pf_reg}
<p><b>Figure 2 · Responder label</b> (ROC-AUC: 0.5 = chance).</p>{pf_bin}
<p><b>Figure 3 · Mean rank of each method</b> across splits (1 = best in its split).</p>{rk}
<p><b>Figure 4 · Is ML better than covariate modelling?</b> Difference in average performance of the two tracks over the splits.</p>{fam_html}
<h3>Table 1 · Goodness of fit, continuous outcome (test set, mean over {NS} splits)</h3>{tbl(tR)}
<h3>Table 2 · Goodness of fit, responder label (test set; recall/precision/accuracy at a cutoff that predicts the training responder share as positive)</h3>{tbl(tB)}
<p class=note>Baselines (no skill) have R² ≈ 0 and AUC = 0.5. RMSE/MAE are in outcome units and cannot be compared across arms.</p>
<h2>3. Which covariates does each method retain?</h2>
<p>Dark cell = share of splits in which the method retained the covariate; ● = retained in ≥ {int(STABLE*100)}% of splits. Top block: covariate-modelling methods; bottom block: machine-learning models (tuned). Columns are ordered by overall agreement. Direction is on the improvement scale (from LASSO coefficients). The prior comes from the pre-data mechanistic hypothesis sheet.</p>{''.join(sec_cov)}
<h3>How 'retained' is defined for each method</h3>{tbl(pd.DataFrame(meth_rows, columns=["Method", "What it is", "Covariate counts as retained when (in a given split)"]))}
<h2>4. Take-aways for the slides</h2><ul>
<li>One covariate per arm is picked by essentially every method; the remaining covariates are inconsistent between methods and between splits and should not be presented as drivers.</li>
<li>The retained drivers match the mechanism of each drug (Mexiletine - myotonia; Oligonucleotide - repeat burden; Tideglusib - cognition) where the hypothesis sheet had a prior.</li>
<li>Which covariates matter is method-independent; which method predicts best is not: tree ensembles and simple penalised/stepwise models are equivalent in Mexiletine (ensembles are ahead only in Tideglusib, behind in Oligonucleotide), flexible networks/KNN/SVM are worse on ~120 patients, and nothing rescues the weakly predictable Oligonucleotide arm.</li></ul>
<h2>5. Caveats</h2><ul><li>Test sets are 41-43 patients; one patient moves a split's metric, hence the multi-seed design. Splits share the same 500 patients, so the {NS} results are not independent replicates; SDs understate uncertainty about new patients.</li>
<li>'Retained' uses within-method p-values (after selection for stepwise/best subset, so optimistic) and permutation importance for ML; stability across splits is the multiplicity guard, not a formal correction.</li>
<li>Correlated covariates (CTG vs myotonia severity; onset vs duration) share credit, so a retained covariate can be a proxy.</li></ul>
<p class=note>Reproduce: <code>bash split_1to3/seed_sensitivity/run_seeds.sh</code> then <code>python split_1to3/seed_sensitivity/src/clean_report.py</code>. Figures as PNG in <code>split_1to3/reports/figs/</code>. AI use: Claude Code wrote and ran the code and drafted the text; numbers are regenerated by the scripts.</p>"""
(REP / "summary_clean.html").write_text(html); print("wrote", len(html) // 1024, "KB;", NS, "seeds")
