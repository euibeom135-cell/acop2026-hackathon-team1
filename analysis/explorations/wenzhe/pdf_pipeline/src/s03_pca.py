"""S03: PCA of the TRAIN covariates per arm (unsupervised: outcome not used; numeric columns z-scored, dummies left 0/1). Outputs results/pca_<arm>_{var,loadings}.csv."""
from sklearn.decomposition import PCA
from pcommon import *
from ml_models import make_pre
for arm in ARMS:
    d = get_arm(arm); Z = make_pre(d["num"], list(d["Xtr"].columns)).fit_transform(d["Xtr"]); p = PCA().fit(Z)
    ev = pd.DataFrame({"PC": [f"PC{i+1}" for i in range(len(p.explained_variance_ratio_))], "var_ratio": p.explained_variance_ratio_, "cum": np.cumsum(p.explained_variance_ratio_)})
    L = pd.DataFrame(p.components_[:4].T, index=Z.columns, columns=[f"PC{i+1}" for i in range(4)]); ev.to_csv(ARES / f"pca_{arm}_var.csv", index=False); L.to_csv(ARES / f"pca_{arm}_loadings.csv")
    print(arm, "k@80%:", int((ev.cum < .8).sum() + 1), "PC1-3 var:", ev.var_ratio.head(3).round(3).tolist())
