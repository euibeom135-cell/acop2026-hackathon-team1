"""Step 2 page: Split once per arm (genuine 80/20, stratified, seed 42, locked) and the repeated CV used inside TRAIN."""
from data import *
import json

def balance():
    sp = split(); ts = tsb(); tp = r("test_predictions.csv"); rows = []
    for a in ARMS:
        d = train(a); n_te = int((sp[(sp.arm == a)].set == "test").sum()); nr = ts[(ts.arm == a) & (ts.task == "bin") & (ts.method == "Prevalence only")].iloc[0]
        yte = tp[(tp.arm == a) & (tp.task == "reg")].drop_duplicates("row").obs      # observed test outcomes as stored in the locked scoring output
        rows.append({"Arm": a, "Train n": len(d), "Test n": n_te, "Train / total": f"{len(d) / (len(d) + n_te):.0%}", "Responders train": f"{int(d.label.sum())} ({d.label.mean():.1%})",
                     "Responders test": f"{int(nr.n_resp)} ({nr.n_resp / n_te:.1%})", "Outcome mean (SD) train": f"{d.y.mean():.2f} ({d.y.std():.2f})", "Outcome mean (SD) test": f"{yte.mean():.2f} ({yte.std():.2f})"})
    return pd.DataFrame(rows)

def fig_balance():
    tp = r("test_predictions.csv"); fig, ax = plt.subplots(1, 3, figsize=(11, 2.8))
    for a_, a in zip(ax, ARMS):
        d = train(a); yte = tp[(tp.arm == a) & (tp.task == "reg")].drop_duplicates("row").obs; bins = np.histogram_bin_edges(np.r_[d.y, yte], 14)
        a_.hist(d.y, bins=bins, density=True, alpha=.6, color=ARMC[a], label=f"train n={len(d)}"); a_.hist(yte, bins=bins, density=True, alpha=.5, color="#444", label=f"test n={len(yte)}")
        a_.set_title(f"{a}: {OUTCOME[a][0]}", fontsize=8); a_.legend(fontsize=7); a_.tick_params(labelsize=7)
    fig.tight_layout(); return fig_html(fig, "s2_balance")

def cv_table():
    rows = []
    for a in ARMS:
        f = folds = r(f"folds_{a}.csv"); d = train(a); f = f.assign(lab=d.label.values[f.row.values]); g = f.groupby(["rep", "fold"]).agg(n=("row", "size"), resp=("lab", "mean"))
        rows.append({"Arm": a, "Repeats x folds": f"{f.rep.nunique()} x {f.fold.nunique()} = {len(g)} fits per method", "Validation fold size": f"{g.n.min()}-{g.n.max()}", "Fit size (train rows per fit)": f"{len(d) - g.n.max()}-{len(d) - g.n.min()}",
                     "Responder share per validation fold": f"{g.resp.min():.0%}-{g.resp.max():.0%} (train {d.label.mean():.0%})"})
    return pd.DataFrame(rows)

def build():
    B = balance(); C = cv_table(); lock = json.loads((RES / "TEST_SCORED.lock").read_text())
    R = req([("Split each arm separately", "Three independent 80/20 splits, one per arm", "2.1"),
             ("Stratify by outcome (responder label directly; continuous outcome binned first)", "Stratified on the responder label; train vs test label share and continuous-outcome mean/SD shown", "2.1, 2.2"),
             ("Fix the random seed", "Seed 42; the split file results/split_seed42.csv is read as given, nothing re-randomised", "2.1"),
             ("Lock the test set; use it only for the final evaluation", "Test rows are first opened in Step 6; a lock file blocks re-scoring", "2.3"),
             ("(Step 5 / checklist) tuning on training data only", "Repeated stratified 5-fold x3 CV inside TRAIN for every comparison; inner 3-fold grid search for tuned ML", "2.4")])
    body = f"""{R}<h2>2.1 The split</h2>
<p>One split per arm, 80% train / 20% test, stratified on the responder label, random seed 42. The split is the project's single locked split file (<code>results/split_seed42.csv</code>, read-only); no new split was drawn and no alternative split was compared.</p>
{tbl(B, cap="Set sizes and balance (outcome summaries of the test set are read from the locked scoring output, for balance only)")}
<h2>2.2 Balance check</h2>{fig_balance()}
{note("Stratification keeps the responder share of train and test within about one patient of each other (table). The continuous outcome was not used for stratification; its train and test distributions overlap as shown, but with 33-34 test patients small differences in mean and SD are expected.")}
<h2>2.3 Test set is locked</h2>
<p>The test rows are not used for exploration (Step 1), preprocessing (Step 3), selection (Step 4) or tuning (Step 5). They are opened once, in Step 6, in a single scoring pass. The guard file <code>results/TEST_SCORED.lock</code> records that pass (started {esc(lock['started'])}, finished {esc(lock['finished'])}) and blocks a second scoring unless explicitly forced.</p>
<h2>2.4 Cross-validation inside train</h2>
<p>All model comparison and tuning uses <b>repeated stratified 5-fold CV, 3 repeats, seed 42</b>, on the training rows only, stratified on the responder label. The same folds are used for every method and for both outcome types, so methods are compared on the same patients. Tuned ML models additionally run an inner 3-fold grid search on each outer fold's training rows (nested), so a tuned model is never tuned on the fold that scores it. Every preprocessing step is re-fitted on each fold's training part (Step 3).</p>
{tbl(C)}"""
    return page(1, "Split once per arm, then cross-validate inside train", "A genuine, seeded, stratified 80/20 split per arm; the test set is locked until Step 6. Model comparison uses repeated 5-fold CV on train.", body)
