"""Single renderer for the signal-vs-noise verdict (ONE rule). Used by Step 6.5 and by summary.html so the two cannot disagree. Source: results/signal_noise_summary.csv (TRAIN evidence only)."""
from data import *

RULE = pd.DataFrame([("a", "Selection frequency", "pooled selection frequency >= 0.6 over three selectors (LASSO lambda.min, elastic net, stepwise-BIC) in 200 bootstrap resamples"),
    ("b", "Sign stability", "sign of the lm/glm coefficient equals the full-train sign in >= 4 of 5 train subsamples (80% each)"),
    ("c", "Multi-family use", "used by >= 2 of 3 families on full train: penalised (LASSO or EN non-zero); stepwise-BIC retained; nonlinear/ML (GAM term p < 0.05, or RF held-out permutation importance > 0 in >= 4/5 folds)"),
    ("d", "Beats shuffled-outcome null", "lm/glm |t| above the 95th percentile of its own null (500 outcome permutations), or RF held-out permutation importance above the 95th percentile of the RF null (100 permutations)")],
    columns=["", "Criterion", "Definition (train rows only)"])
VERDICT_RULE = "SIGNAL = all 4 criteria; BORDERLINE = 2 or 3; NOISE = 0 or 1. Applied unchanged to every arm and both outcomes."
ck = lambda b: "&#10003;" if b else "&#10007;"

def S(): return sig()

def _row(x):
    cls = {"SIGNAL": "sig", "BORDERLINE": "bor"}.get(x.verdict, "noi")
    prior = f"{x.prior_strength}, {x.prior_sign_on_benefit}" if x.prior_strength != "expected_noise" else "expected noise"
    flag = " (plausible noise)" if x.plausible_but_noise else ""
    return (f"<tr class={cls}><td>{x['rank']}</td><td><b>{nice(x.covariate)}</b>{flag}</td><td><b>{x.verdict}</b> ({x.n_criteria}/4)</td><td>{ck(x.crit_a)} {x.selfreq_pooled:.2f}</td><td>{ck(x.crit_b)} {x.sign_same_k_of_5}/5</td>"
            f"<td>{ck(x.crit_c)} {x.n_families}/3</td><td>{ck(x.crit_d)}</td><td>{x.effect_on_benefit.replace('higher/present = ', 'higher: ')}</td><td>{esc(prior)}</td><td>{x.sign_agrees_with_prior}</td></tr>")
HDR = ("<tr><th>#</th><th>Covariate</th><th>Verdict</th><th>(a) sel. freq</th><th>(b) sign</th><th>(c) families</th><th>(d) &gt; null</th><th>Effect on benefit</th><th>Prior (strength, sign on benefit)</th><th>Agrees with prior</th></tr>")

def ranked_table(arm, task):
    d = S(); d = d[(d.arm == arm) & (d.task == task)].sort_values("rank")
    vis = d[(d.verdict != "NOISE") | d.plausible_but_noise]; rest = d[(d.verdict == "NOISE") & ~d.plausible_but_noise]
    t = f"<table class=t>{HDR}{''.join(_row(x) for _, x in vis.iterrows())}</table>"
    if len(rest): t += f"<details><summary>{len(rest)} further NOISE covariates</summary><table class=t>{HDR}{''.join(_row(x) for _, x in rest.iterrows())}</table></details>"
    return t

def signal_sets():
    """arm -> task -> dict(signal=[...], borderline=[...]) (feature level)."""
    d = S(); out = {}
    for (a, t), g in d.groupby(["arm", "task"]):
        out.setdefault(a, {})[t] = dict(signal=list(g[g.verdict == "SIGNAL"].covariate), borderline=list(g[g.verdict == "BORDERLINE"].covariate))
    return out

def signal_summary_table():
    s = signal_sets(); rows = []
    for a in ARMS:
        f = lambda t, k: "; ".join(nice(c) for c in s[a][t][k]) or "none"
        rows.append({"Arm": a, "SIGNAL, continuous outcome": f("reg", "signal"), "SIGNAL, responder label": f("bin", "signal"),
                     "BORDERLINE, continuous": f("reg", "borderline"), "BORDERLINE, label": f("bin", "borderline")})
    return pd.DataFrame(rows)

def matrix():
    d = S(); cols = [(a, t) for a in ARMS for t in ["reg", "bin"]]; piv = {}
    for a, t in cols:
        g = d[(d.arm == a) & (d.task == t)].set_index("covariate"); piv[(a, t)] = g.verdict
    M = pd.DataFrame(piv); M = M[M.apply(lambda r: (r != "NOISE").any() and r.notna().any(), axis=1)]
    order = {"SIGNAL": 2, "BORDERLINE": 1, "NOISE": 0}; M = M.loc[M.apply(lambda r: -sum(order.get(v, 0) for v in r), axis=1).sort_values(kind="stable").index]
    head = "<tr><th rowspan=2>Covariate</th>" + "".join(f"<th colspan=2>{a}</th>" for a in ARMS) + "</tr><tr>" + "".join("<th>cont.</th><th>label</th>" for _ in ARMS) + "</tr>"
    body = ""
    for cov, r_ in M.iterrows():
        body += f"<tr><td>{nice(cov)}</td>" + "".join(f"<td style='background:{VCOL.get(r_[c], '#fff')};text-align:center'>{ {'SIGNAL': 'SIGNAL', 'BORDERLINE': 'border.', 'NOISE': 'noise'}.get(r_[c], 'n/a (constant)') }</td>" for c in cols) + "</tr>"
    return f"<table class=t>{head}{body}</table>"

def noise_table():
    d = S(); d = d[d.plausible_but_noise].sort_values(["arm", "task", "rank"]); rows = []
    for _, x in d.iterrows(): rows.append({"Arm": x.arm, "Outcome": TASKN[x.task], "Covariate": nice(x.covariate), "Why it looked plausible, and why it is noise": esc(x.plausible_noise_reason)})
    return pd.DataFrame(rows)

def disagree_table():
    d = S(); d = d[(d.sign_agrees_with_prior == "DISAGREE") & (d.verdict != "NOISE")]; rows = []
    for _, x in d.iterrows():
        rows.append({"Arm": x.arm, "Outcome": TASKN[x.task], "Covariate": nice(x.covariate), "Verdict": x.verdict, "Train effect": x.effect_on_benefit.replace("higher/present = ", "higher: "),
                     "Sheet expected (sign on benefit)": x.prior_sign_on_benefit, "Prior strength": x.prior_strength, "lm/glm p": f"{x.p_value:.3f}"})
    return pd.DataFrame(rows)
