"""Seed-sensitivity split generator: the SAME 1:3 outcome-quartile-stratified, covariate-re-randomised design as n00_split.py, with a different master seed.
Candidate j of master seed s uses random_state = s*100000 + j; K candidates; accept the best 2% by Mahalanobis distance; use the first accepted candidate."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "src"))
from scommon import *
from sklearn.model_selection import train_test_split
K, ACCEPT_Q = 1000, 0.02
def build_split(master, K=K):
    df, X = features_all(); rows, diag = [], []
    for arm in ARMS:
        a = df[df.treatment_arm == arm]; y = ARMS[arm]["y"]; Xa = X.loc[a.index]; Xa = Xa.loc[:, Xa.std() > 0]; Zs = (Xa - Xa.mean()) / Xa.std(ddof=0); N = len(a)
        bins = pd.qcut(a[y], N_BINS, labels=False, duplicates="drop"); Sinv = np.linalg.pinv(np.cov(Zs.values.T)); sdv = Zs.values.std(0)
        def score(m):
            d = Zs.values[m].mean(0) - Zs.values[~m].mean(0); return (m.sum() * (~m).sum() / N) * d @ Sinv @ d, np.abs(d / sdv).max()
        C = []
        for j in range(K):
            _, te = train_test_split(np.arange(N), test_size=TEST_FRAC, random_state=master * 100000 + j, stratify=bins); m = np.zeros(N, bool); m[te] = True; C.append((j, *score(m)))
        C = pd.DataFrame(C, columns=["j", "M", "max_smd"]); j = int(C[C.M <= C.M.quantile(ACCEPT_Q)].j.iloc[0])
        _, te = train_test_split(np.arange(N), test_size=TEST_FRAC, random_state=master * 100000 + j, stratify=bins); m = np.zeros(N, bool); m[te] = True
        rows += [(pid, arm, "test" if t else "train") for pid, t in zip(a.patient_id, m)]; diag.append(dict(seed=master, arm=arm, n_train=int((~m).sum()), n_test=int(m.sum()), M=score(m)[0], max_abs_smd=score(m)[1], random_median_max_smd=C.max_smd.median()))
    return pd.DataFrame(rows, columns=["patient_id", "arm", "set"]), pd.DataFrame(diag)
