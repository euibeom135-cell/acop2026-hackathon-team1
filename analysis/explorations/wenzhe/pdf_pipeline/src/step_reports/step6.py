"""Step 6 page: Evaluate. The locked test scores (results/test_scoreboard.csv) are rendered; nothing is re-scored. Selection of primary models is by TRAIN CV only."""
from data import *
from step5 import MLW
import json, signal_view as sv

REF = ["lm / glm (all covariates)", "Stepwise both (BIC)", "LASSO (glmnet, lambda.min)", "Elastic net (glmnet, alpha=.5)", "Random forest (untuned)", "Random forest (tuned, GridSearchCV)", "XGBoost (untuned)", "XGBoost (tuned, GridSearchCV)"]

def compact(arm, task):
    t = tsb(); t = t[(t.arm == arm) & (t.task == task)]; base = "Mean only" if task == "reg" else "Prevalence only"
    keep = [base] + REF + list(t[t.is_primary].method); sel = t[t.method.isin(keep)].copy()
    sel["o"] = sel.method.map(lambda m: 0 if m == base else (1 if m in REF[:4] else 2)); sel = sel.sort_values(["o", "family"], kind="stable")
    sel["Method"] = [short(m) + (" &#9733;" if p else "") for m, p in zip(sel.method, sel.is_primary)]; sel["Type"] = sel.family
    return sel

def fmt_reg(sel):
    return pd.DataFrame({"Method": sel.Method, "Type": sel.Type, "RMSE [95% CI]": [f"{x.RMSE:.3f} [{x.RMSE_lo:.2f}, {x.RMSE_hi:.2f}]" for x in sel.itertuples()], "MAE": sel.MAE, "R2 (vs test mean)": sel.R2,
                         "RMSE gain over mean-only [95% CI]": ["0 (reference)" if x.family == "Baseline" else f"{x.dRMSE_vs_mean:+.2f} [{x.dRMSE_lo:+.2f}, {x.dRMSE_hi:+.2f}]" for x in sel.itertuples()]})

def fmt_bin(sel):
    return pd.DataFrame({"Method": sel.Method, "Type": sel.Type, "ROC-AUC [95% CI]": [f"{x.AUC:.3f} [{x.AUC_lo:.2f}, {x.AUC_hi:.2f}]" for x in sel.itertuples()], "Recall": sel.recall, "Precision": sel.precision,
                         "Accuracy": sel.accuracy, "TP / FP / FN / TN": [f"{int(x.TP)} / {int(x.FP)} / {int(x.FN)} / {int(x.TN)}" for x in sel.itertuples()], "Cutoff": sel.cutoff})

def full_table(arm, task):
    t = tsb(); t = t[(t.arm == arm) & (t.task == task)]
    return fmt_reg(t.assign(Method=t.method.map(short), Type=t.family)) if task == "reg" else fmt_bin(t.assign(Method=t.method.map(short), Type=t.family))

def class_mix():
    t = tsb(); rows = []
    for a in ARMS:
        b = t[(t.arm == a) & (t.task == "bin") & (t.method == "Prevalence only")].iloc[0]; n = int(b.n_test); nr = int(b.n_resp); p = prim(); pc = p[(p.arm == a) & (p.task == "bin")]
        cuts = []
        for tr in ["Covariate", "ML"]:
            m = pc[pc.track == tr].iloc[0].primary_method; c = t[(t.arm == a) & (t.task == "bin") & (t.method == m)].iloc[0].cutoff; cuts.append(f"{short(m)}: {c:.3f}")
        rows.append({"Arm": a, "Test n": n, "Responders": nr, "Non-responders": n - nr, "Responder share": f"{nr / n:.0%}", "Everyone-non-responder accuracy": f"{(n - nr) / n:.1%}", "Recall of that baseline": "0%", "Cutoffs of the two CV-picked models": " | ".join(cuts)})
    return pd.DataFrame(rows)

def fig_forest():
    t = tsb(); fig, ax = plt.subplots(2, 3, figsize=(15, 8))
    for i, task in enumerate(["reg", "bin"]):
        for j, a in enumerate(ARMS):
            s = compact(a, task).iloc[::-1]; y = np.arange(len(s)); met, lo, hi = ("RMSE", "RMSE_lo", "RMSE_hi") if task == "reg" else ("AUC", "AUC_lo", "AUC_hi")
            ax[i, j].errorbar(s[met], y, xerr=[s[met] - s[lo], s[hi] - s[met]], fmt="none", ecolor="#aaa", lw=1)
            ax[i, j].scatter(s[met], y, c=[FC[f] for f in s.family], s=[70 if p else 22 for p in s.is_primary], zorder=3, edgecolor=["k" if p else "none" for p in s.is_primary])
            ax[i, j].set_yticks(y); ax[i, j].set_yticklabels([short(m) for m in s.method], fontsize=7); ax[i, j].set_title(f"{a}: test {met} [95% CI] ({'lower' if task == 'reg' else 'higher'} better)", fontsize=9)
            if task == "bin": ax[i, j].axvline(.5, color="#777", ls="--", lw=.8)
            ax[i, j].tick_params(axis="x", labelsize=7)
    h = [plt.Line2D([], [], marker="o", ls="", color=v, label=k) for k, v in FC.items()] + [plt.Line2D([], [], marker="o", ls="", color="w", markeredgecolor="k", markersize=9, label="CV-picked primary")]
    fig.legend(handles=h, loc="lower center", ncol=4, fontsize=8); fig.tight_layout(rect=[0, .03, 1, 1]); return fig_html(fig, "s6_test_forest")

def answer_table():
    h = head(); p = prim(); rows = []
    for x in h.itertuples():
        task = x.task; sm = 1 if task == "reg" else -1; met = x.metric
        cv_c = p[(p.arm == x.arm) & (p.task == task) & (p.track == "Covariate")].iloc[0]; cv_m = p[(p.arm == x.arm) & (p.task == task) & (p.track == "ML")].iloc[0]
        c, m = x.primary_Covariate_value, x.primary_ML_value; better = (m < c) if task == "reg" else (m > c); tie = abs(m - c) < 1e-9
        rel = "tie" if tie else ("ML ahead" if better else "covariate ahead")
        rows.append({"Arm": x.arm, "Outcome": TASKN[task], "Baseline": f"{x.baseline_value:.3f}", "CV-picked covariate": f"{short(x.primary_Covariate)} ({c:.3f}) [{x.primary_Covariate_CI}]", "CV-picked ML": f"{short(x.primary_ML)} ({m:.3f}) [{x.primary_ML_CI}]",
                     f"{met} metric": met, "Test comparison": rel, "Train CV (cov vs ML)": f"{cv_c.cv_value:.3f} vs {cv_m.cv_value:.3f}"})
    return pd.DataFrame(rows)

def importance_table():
    i = r("test_importance.csv"); p = prim(); s = sig(); rows = []
    for (a, t), g in p.groupby(["arm", "task"], sort=False):
        m = g[g.track == "ML"].iloc[0].primary_method; x = i[(i.arm == a) & (i.task == t) & (i.method == m)].sort_values("perm_mean", ascending=False).head(3)
        parts = []
        for q in x.itertuples():
            v = s[(s.arm == a) & (s.task == t) & (s.covariate == q.term)].verdict; parts.append(f"{nice(q.term)} ({q.perm_mean:.3f}; train verdict {v.iloc[0] if len(v) else 'n/a'})")
        rows.append({"Arm": a, "Outcome": TASKN[t], "CV-picked ML model": short(m), "Top 3 test permutation importance (mean drop)": "; ".join(parts)})
    return pd.DataFrame(rows)

def sec63b():
    import method_figs as mf
    def blk(m):
        s = mf.slug(m); nm = "Baselines" if m == "Baseline" else m
        return f"<details><summary><b>{esc(nm)}</b></summary>{mf.pred_grid(mf.test_get, m, f's6_{s}_pred')}</details>"
    tp = mf._tp(); tabs = ""
    for a in ARMS:
        for t in ["reg", "bin"]:
            d = tp[(tp.arm == a) & (tp.task == t)]; o = d.groupby("row").obs.first()
            pv = d.pivot(index="row", columns="method", values="pred").reindex(columns=[m for m in d.method.unique()])
            pv.columns = [short(m) for m in pv.columns]; pv = pv.map(lambda v: "-" if pd.isna(v) else f"{v:.2f}")
            pv.insert(0, "Observed", [f"{v:g}" for v in o.loc[pv.index]]); pv.index = [f"test row {i}" for i in pv.index]
            tabs += f"<details><summary>{a} - {TASKN[t]}: per-patient test predictions ({len(pv)} patients x {pv.shape[1] - 1} methods)</summary><div style='overflow-x:auto'>{tbl(pv, index=True)}</div></details>"
    return f"""<h3 id="63b">6.3b Per-method held-out test predictions</h3>
<p>Every panel below is drawn from <code>results/test_predictions.csv</code>, the output of the single locked test scoring; nothing was refitted or re-scored for these figures. Rows: continuous outcome observed vs predicted (top) and responder-label ROC (bottom); columns: arms. ML panels overlay the untuned and tuned variants. Test patients carry no identifier in the results, so they are labelled by test row index. With 33-34 patients the scatter is noisy; read the panels as illustration, not ranking.</p>
<h4>Covariate track</h4>{''.join(blk(m) for m in mf.COV + ['Baseline'])}<h4>ML track</h4>{''.join(blk(m) for m in MLW)}
<h4>Per-patient test predictions</h4><p class=note>Label predictions are probabilities of Responder (the Youden cutoff of 6.2 turns them into classes). Observed = continuous outcome or 0/1 label.</p>{tabs}"""

def build():
    lock = json.loads((RES / "TEST_SCORED.lock").read_text()); CM = class_mix(); AN = answer_table(); tt = tsb()
    R = req([("Score once on the held-out test set", "One scoring pass; guard file results/TEST_SCORED.lock; nothing refitted or re-scored afterwards", "6.1"),
             ("Check the class mix; accuracy alone can mislead; pair accuracy with recall and precision; state the cutoff", "Class mix, 'everyone non-responder' baseline, Youden cutoff fixed from TRAIN out-of-fold scores", "6.2"),
             ("One scoreboard per arm; covariate and ML rows together on the same test patients; untuned and tuned side by side", "Table 6.3 per arm (stepwise, LASSO / elastic net, RF and XGBoost untuned and tuned, plus the CV-picked primaries); bootstrap intervals", "6.3"),
             ("Match metrics to the outcome: RMSE, MAE, R2 (vs test mean, original units, direction per arm) / ROC-AUC, recall, precision, accuracy, TP/FP/FN/TN", "Columns of the tables in 6.3; direction of benefit stated per arm", "6.3"),
             ("Do not over-read small gaps on a few dozen test patients", "95% bootstrap CIs; verdicts avoid ranking on small gaps", "6.3, 6.4, 6.6"),
             ("Compare the covariates, not only the scores (what each method kept; importance)", "Signal-vs-noise table over several selectors, resampling and a null; test permutation importance of the ML picks", "6.5"),
             ("Key covariates are separated from noise", "ONE pre-stated rule; ranked tables per arm and outcome; plausible-but-noise named", "6.5")])
    arms_txt = "".join(f"<li><b>{a}</b>: {OUTCOME[a][0]}, {OUTCOME[a][1]}</li>" for a in ARMS)
    sc = ""
    for a in ARMS:
        sc += f"<h3>{a}</h3>" + tbl(fmt_reg(compact(a, "reg")), dec=3, cap=f"Continuous outcome ({OUTCOME[a][0]}; {OUTCOME[a][1]}); RMSE and MAE in original units") + tbl(fmt_bin(compact(a, "bin")), dec=3, cap="Responder label at the stated train-OOF Youden cutoff (positive class = responder)")
    full = "".join(f"<h4>{a} - {TASKN[t]}</h4>" + tbl(full_table(a, t), dec=3) for a in ARMS for t in ["reg", "bin"])
    sset = sv.signal_sets()
    body = f"""{R}
<h2>6.1 The test set was scored once</h2>
<p>The 33 / 34 / 34 test patients were scored in a single pass (script s07; guard <code>results/TEST_SCORED.lock</code>, started {esc(lock['started'])}, finished {esc(lock['finished'])}, {lock['rows']} scoreboard rows). The primary models were fixed beforehand by TRAIN cross-validation only (Step 5.5); selection used no test information. Detail: <a href="../../notes/compute_notes.html">compute notes</a>.</p>
{warn("Disclosure: the main DM1 project had already scored this same 80/20 test split once, with different, frozen model specifications. That earlier file was neither read nor used here. This pass is the canonical, single scoring of the full method set; all test numbers below are reported whatever they are, and nothing was tuned, removed or re-run after seeing them.")}
<ul>{arms_txt}</ul>
<h2>6.2 Class mix, cutoff and the 'everyone non-responder' baseline</h2>{tbl(CM)}
<p>Responders are the minority in every arm, so a model that calls everybody a non-responder is already 'accurate' for 53-70% of patients (last accuracy column) while finding no responder at all (recall 0, no precision). Accuracy is therefore read together with recall, precision and ROC-AUC (which ignores the class mix; 0.5 = no skill). Predicted labels use each method's Youden-J cutoff computed from its TRAIN out-of-fold scores (averaged over CV repeats) and fixed before any test row was read.</p>
<h2>6.3 Scoreboard per arm (same test patients)</h2>
<p>Star = the model picked by TRAIN CV in its track. R2 is relative to the mean of the test outcomes (it can be negative). 'RMSE gain' is mean-only RMSE minus model RMSE (positive = better than predicting the mean), with a 95% bootstrap CI (2000 resamples). With 33-34 test patients one patient moves a score noticeably; gaps of a few hundredths are not interpretable.</p>
{fig_forest()}{sc}
<details><summary>Full test scoreboard (all methods, all arms, both outcomes; {len(tt)} rows)</summary>{full}</details>
{sec63b()}
<h2>6.4 Can ML improve beyond covariate modelling?</h2>
<p>Each track is represented by the model <b>picked by TRAIN CV</b> (not by test score), compared on the same test patients:</p>{tbl(AN.drop(columns=[c for c in AN.columns if c.endswith('metric')]))}
<div class=box><b>Answer.</b> No consistent advantage for ML. On the test set the CV-picked ML model is ahead in only 2 of 6 comparisons: <b>Tideglusib continuous</b> (RMSE 2.35 vs 2.83, about 17% lower; it also led in train CV, 2.16 vs 2.42) and <b>Oligonucleotide label</b> (AUC 0.800 vs 0.771, a gap of a few patients with heavily overlapping intervals and a tiny CV gap). It is behind or tied in the other four (Mexiletine both outcomes, Oligonucleotide continuous, Tideglusib label). The intervals overlap in every pair, so even the Tideglusib continuous advantage is suggestive rather than proven. In 4 of 6 comparisons the simpler covariate model matches or beats the ML pick, and it also names the covariates (6.5).</div>
<h2 id="65">6.5 Covariate identification: signal versus noise</h2>
<p>This is the deliverable on which the kickoff checklist asks ('key covariates are separated from noise'). It uses <b>one</b> rule, fixed in advance and applied unchanged to every arm and outcome; all evidence is from TRAIN rows only (selection frequency over bootstrap resamples, sign stability over subsamples, multi-family use, and a shuffled-outcome null). The test set plays no part in any verdict.</p>
{tbl(sv.RULE, cap="The four criteria (one point each)")}<p><b>{sv.VERDICT_RULE}</b> Direction is the sign of the full-train standardised lm/glm coefficient translated to benefit (Mexiletine continuous: more negative = better; label: Responder = better). Prior signs were transcribed from the hypothesis sheet before results were read; 'open' means the sheet gives no direction. Verdicts are per feature (dummy levels are separate rows).</p>
<h3>Signal covariates per arm</h3>{tbl(sv.signal_summary_table())}
<h3>Cross-arm side by side (only covariates that are not NOISE somewhere)</h3>{sv.matrix()}
<p>Why arms differ: each arm is a different drug acting through a different pathway, and the pre-data hypothesis sheet already expected different drivers per arm (Mexiletine: myotonia severity; Tideglusib: cognitive function and muscle strength; Oligonucleotide: CTG-repeat related covariates). The signal sets follow that pattern: myotonia severity for the sodium-channel arm, cognitive function for Tideglusib, log10 CTG for Oligonucleotide. Disease duration is SIGNAL in two arms (continuous outcome) and BORDERLINE, with the opposite sign to the sheet, in Oligonucleotide. Sample sizes of 128-136 and a continuous outcome that carries more information than the label also explain why the label yields almost no SIGNAL.</p>
<h3>Ranked verdict tables</h3>
{''.join(f"<h4>{a} - {TASKN[t]}</h4>" + sv.ranked_table(a, t) for a in ARMS for t in ['reg', 'bin'])}
<h3>Plausible-looking covariates that are noise</h3>{tbl(sv.noise_table())}
<h3>Sign disagreements with the hypothesis sheet (SIGNAL / BORDERLINE only)</h3>{tbl(sv.disagree_table())}
{note("Mexiletine cognitive function (weak prior, expected helpful) and Oligonucleotide disease duration (moderate prior, expected harmful) point the opposite way in the training data. Both are only BORDERLINE with lm/glm p-values of 0.08-0.19, so these are flags for follow-up, not findings.")}
<h3>Surprises</h3>
<ul><li><b>Disease duration is SIGNAL for Mexiletine and Tideglusib (continuous)</b>, although the sheet gave no direction (Mexiletine: listed as expected noise). In Mexiletine the call rests on selection frequency 0.75, sign stability and the random-forest null; the lm/glm p-value is only 0.088, so it is the weakest of the SIGNAL calls. Disease duration also correlates with muscle strength (r = -0.76 to -0.79), so credit between the two is shared (a kickoff watch-out for correlated covariates).</li>
<li><b>Mexiletine myotonia severity on the label is BORDERLINE, not SIGNAL</b>: it passes criteria (b), (c) and (d) and misses only (a), with pooled selection frequency 0.597 against the 0.6 threshold. It is the same covariate that is the strongest SIGNAL on the continuous outcome. The rule was not relaxed.</li>
<li><b>Strong priors not supported</b>: for Oligonucleotide the sheet rated somatic mosaicism and muscle strength as strong, but both are NOISE on both outcomes (1 criterion or fewer).</li></ul>
<h3>Importance in the ML picks (explanatory only)</h3>
<p>Permutation importance on the test set for the CV-picked ML model, shown next to the train verdict. It feeds no selection and no verdict.</p>{tbl(importance_table(), dec=3)}
<h2>6.6 Conclusions and caveats</h2>
<ul>
<li><b>Signal covariates</b> are few: Mexiletine myotonia severity and disease duration (continuous); Oligonucleotide log10 CTG (continuous); Tideglusib cognitive function (both outcomes) and disease duration (continuous). The responder label gives SIGNAL only for Tideglusib cognitive function; elsewhere label evidence is BORDERLINE at best.</li>
<li><b>Prediction</b>: every CV-picked model beat its baseline in train CV; on test the covariate and ML tracks are largely indistinguishable, with ML clearly ahead only for Tideglusib continuous.</li>
<li><b>Small test sets</b> (33-34 patients, 10-16 responders): intervals are wide, one patient moves a classification score, and gaps of a few hundredths should not be ranked.</li>
<li><b>Simulated data</b>: results describe a synthetic dataset, not real patients or approved therapies.</li>
<li><b>Label outcomes yield little signal</b>: the dichotomised label has fewer effective observations per covariate (1.9-3.2 responders per column), so selection frequencies are lower and many covariates are BORDERLINE.</li>
<li><b>Permutation importance at small n</b> is noisy and splits credit between correlated covariates (Tideglusib disease duration is SIGNAL on train but absent from the top 3 test importances of the XGBoost pick, where cognitive function dominates), so importance rankings are supporting, not decisive.</li>
<li><b>Verdicts are train-only evidence</b>; a covariate marked SIGNAL here is a candidate for confirmation in independent data.</li></ul>"""
    return page(5, "Evaluate on the held-out test set", "One scoring pass on the locked test set; covariate and ML tracks compared on the same patients; the covariate-identification deliverable.", body)
