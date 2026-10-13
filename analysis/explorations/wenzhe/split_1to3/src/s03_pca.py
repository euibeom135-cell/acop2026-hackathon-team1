"""S03: PCA of the standardised TRAIN covariates per arm (unsupervised: outcome not used). Outputs results/pca_<arm>_{var,loadings}.csv and reports/pca_plots.json (base64 later)."""
from sklearn.decomposition import PCA
from scommon import *
for arm in ARMS:
    Z = get_arm(arm)["Ztr"]; p = PCA().fit(Z); ev = pd.DataFrame({"PC": [f"PC{i+1}" for i in range(len(p.explained_variance_ratio_))], "var_ratio": p.explained_variance_ratio_, "cum": np.cumsum(p.explained_variance_ratio_)})
    L = pd.DataFrame(p.components_[:4].T, index=Z.columns, columns=[f"PC{i+1}" for i in range(4)]); ev.to_csv(ARES / f"pca_{arm}_var.csv", index=False); L.to_csv(ARES / f"pca_{arm}_loadings.csv")
    print(arm, ev.head(5).round(3).to_dict("records")[:3], "k@80%:", int((ev.cum < .8).sum() + 1))
