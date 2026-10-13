"""N00: 1:3 (25% test) split per arm with outcome-quantile stratification + covariate-based RE-RANDOMISATION (Morgan & Rubin 2012 style).
Procedure (fixed in advance, outcome-free apart from the strata): draw K stratified candidate splits (seeds 0..K-1); score each by the Mahalanobis distance M of the train-test difference in
covariate means (all baseline features, standardised); ACCEPT candidates with M <= the ACCEPT_Q quantile of the K draws; use the FIRST accepted candidate in seed order (random among acceptable).
Outputs results/split_1to3.csv, split_balance.csv, split_candidates.csv. The old split (main project) is compared on the same diagnostics."""
import numpy as np, pandas as pd
from scipy import stats
from sklearn.model_selection import train_test_split
from scommon import *
K, ACCEPT_Q = 5000, 0.02
df, X = features_all(); old = pd.read_csv(MAIN / "results" / "split_seed42.csv").set_index("patient_id").set_index("arm", append=True)
rows, bal, cand_all = [], [], []
for arm in ARMS:
    a = df[df.treatment_arm == arm]; y = ARMS[arm]["y"]; Xa = X.loc[a.index]; Xa = Xa.loc[:, Xa.std() > 0]; Zs = (Xa - Xa.mean()) / Xa.std(ddof=0); N = len(a)
    bins = pd.qcut(a[y], N_BINS, labels=False, duplicates="drop"); Sinv = np.linalg.pinv(np.cov(Zs.values.T)); nte = int(round(TEST_FRAC * N))
    def score(te_mask):
        d = Zs.values[te_mask].mean(0) - Zs.values[~te_mask].mean(0); M = (te_mask.sum() * (~te_mask).sum() / N) * d @ Sinv @ d; return M, np.abs(d / Zs.values.std(0)).max()
    cands = []
    for s in range(K):
        _, te = train_test_split(np.arange(N), test_size=TEST_FRAC, random_state=s, stratify=bins); m = np.zeros(N, bool); m[te] = True; M, mx = score(m); cands.append((s, M, mx))
    C = pd.DataFrame(cands, columns=["seed", "M", "max_abs_smd"]); thr = C.M.quantile(ACCEPT_Q); acc = C[C.M <= thr]; chosen = int(acc.seed.iloc[0])
    _, te = train_test_split(np.arange(N), test_size=TEST_FRAC, random_state=chosen, stratify=bins); m = np.zeros(N, bool); m[te] = True
    Mc, mxc = score(m); rows += [(pid, arm, "test" if t else "train") for pid, t in zip(a.patient_id, m)]
    mo = np.array([old.loc[(p, arm), "set"] == "test" for p in a.patient_id]); Mo, mxo = score(mo)
    C["arm"] = arm; C["accepted"] = C.M <= thr; cand_all.append(C)
    # balance table (new vs old split): SMD for numeric/dummy features, KS for outcome, label proportion
    for nm, mk in (("new 1:3 re-randomised", m), ("old 80/20 (main project)", mo)):
        for c in Zs.columns: bal.append(dict(arm=arm, split=nm, var=c, smd=(Zs[c].values[mk].mean() - Zs[c].values[~mk].mean()) / Zs[c].std(ddof=0), p=stats.ttest_ind(Zs[c].values[mk], Zs[c].values[~mk]).pvalue))
        bal.append(dict(arm=arm, split=nm, var="OUTCOME " + y, smd=(a[y].values[mk].mean() - a[y].values[~mk].mean()) / a[y].std(), p=stats.ks_2samp(a[y].values[mk], a[y].values[~mk]).pvalue))
        lab = (a[ARMS[arm]["label"]] == "Responder").values; bal.append(dict(arm=arm, split=nm, var="LABEL responder share", smd=lab[mk].mean() - lab[~mk].mean(), p=stats.fisher_exact(pd.crosstab(mk, lab))[1]))
    print(f"{arm}: N={N}, test={m.sum()}, chosen seed={chosen}; M new={Mc:.1f} (pctile among {K} random draws: {100*(C.M<=Mc).mean():.1f}%), old split M={Mo:.1f} (pctile {100*(C.M<=Mo).mean():.1f}%); max|SMD| new={mxc:.3f} old={mxo:.3f}; random-draw median max|SMD|={C.max_abs_smd.median():.3f}")
pd.DataFrame(rows, columns=["patient_id", "arm", "set"]).to_csv(ARES / "split_1to3.csv", index=False); pd.DataFrame(bal).to_csv(ARES / "split_balance.csv", index=False); pd.concat(cand_all).to_csv(ARES / "split_candidates.csv", index=False)
