"""reports/summary.html: one-page executive summary; single source of truth for the signal verdict (rendered by the same signal_view module as Step 6.5)."""
from data import *
import signal_view as sv, step6

def build():
    AN = step6.answer_table(); AN = AN.drop(columns=[c for c in AN.columns if c.endswith("metric")]); cont = sv.matrix()
    flow = "".join(f'<li><a href="steps/{f}"><b>Step {n}: {t}</b></a> &ndash; {d}</li>' for n, t, f, d in STEPS)
    body = f"""<h1 style='color:{PUR}'>DM1 six-step analysis: executive summary</h1>{strip(-1, 'steps/')}
{box("Per-arm analysis of the simulated DM1 trial following the kickoff six-step workflow. Genuine 80/20 stratified split (seed 42) per arm, test set scored once. Two questions: which covariates carry signal, and does ML improve on covariate modelling.")}
<h2>The six-step flow</h2><ol>{flow}</ol><p><a href="steps/index.html">All step pages</a></p>
<h2>Covariate identification: signal vs noise (one rule)</h2>
<p>{sv.VERDICT_RULE} Criteria: (a) selection frequency &gt;= 0.6 over LASSO / elastic net / stepwise-BIC bootstraps; (b) sign stable in &gt;= 4/5 subsamples; (c) used by &gt;= 2 of 3 method families; (d) beats a shuffled-outcome null. Train-only evidence; details and ranked tables in <a href="steps/step6_evaluate.html#65">Step 6.5</a>.</p>
{tbl(sv.signal_summary_table())}{cont}
<ul><li>Plausible-looking but noise in every arm: PR interval, cataracts and insulin resistance (Mexiletine, Oligonucleotide); PR interval, creatine kinase and current smoking (Tideglusib).</li>
<li>Sign disagreements with the hypothesis sheet (only BORDERLINE): Mexiletine cognitive function; Oligonucleotide disease duration.</li>
<li>Surprise: disease duration is SIGNAL for Mexiletine and Tideglusib (continuous) with no sheet direction; Mexiletine myotonia severity on the label misses SIGNAL only on criterion (a), at 0.597 versus 0.6.</li></ul>
<h2>Can ML improve beyond covariate modelling?</h2>
<p>Models are picked by train CV only, then compared once on the locked test set (test n = 33-34 per arm; 95% bootstrap CIs in brackets).</p>{tbl(AN)}
<div class=box><b>No consistent advantage for ML.</b> It is ahead in 2 of 6 test comparisons: Tideglusib continuous (RMSE 2.35 vs 2.83, the clearest, supported by CV) and Oligonucleotide label (AUC 0.800 vs 0.771, within noise). It ties or trails in the other four, and all interval pairs overlap.</div>
<h2>Top caveats</h2><ul><li>Test sets are 33-34 patients (10-16 responders): wide CIs, one patient moves a score.</li><li>Data are simulated; nothing here describes real patients or therapies.</li>
<li>The responder label gives little signal (1.9-3.2 responders per model column).</li><li>Permutation importance at small n is noisy and shares credit among correlated covariates; SIGNAL calls are candidates for confirmation, not proof.</li>
<li>The main project had scored this split once before with different frozen specifications; that file was not used here. Selection in this pipeline was CV-only.</li></ul>
<p class=foot>{FOOTER}</p>"""
    h = f"<!doctype html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>DM1 executive summary</title>{CSS}</head><body style='--c:{PUR}'>{body}</body></html>"
    (REP / "summary.html").write_text(h); return "summary.html"
