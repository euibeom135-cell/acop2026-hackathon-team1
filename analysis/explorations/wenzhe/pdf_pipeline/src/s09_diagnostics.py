"""S09: TRAIN-ONLY decision-tree diagram per arm x task for the report. Scaling mirrors ml_models.make_pre (z-score numeric columns per feature_map, dummies untouched); tree params = most frequent tuned
(max_depth, min_samples_leaf) in ml_<arm>_<task>_cv_params.csv (fallback depth 3 / leaf 1). usage: python s09_diagnostics.py [arm task]. Output results/diag_figs/tree_<arm>_<task>.png. No held-out data is read."""
import sys, ast, collections
from pathlib import Path
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier, plot_tree
RES = Path(__file__).resolve().parent.parent / "results"; OUT = RES / "diag_figs"; OUT.mkdir(exist_ok=True)
ARMS = ["Mexiletine", "Oligonucleotide", "Tideglusib"]; LAB = {"reg": "reg continuous outcome", "bin": "responder label"}

def load_scaled(arm, task):
    """-> X (numeric z-scored on train, dummies raw), target."""
    D = pd.read_csv(RES / f"features_train_{arm}.csv"); fmap = pd.read_csv(RES / f"feature_map_{arm}.csv")
    cols = [c for c in D.columns if c not in ("y", "label")]; num = [c for c in fmap.feature[fmap.numeric.astype(bool)] if c in cols]; X = D[cols].copy().astype(float)
    for c in num: sd = X[c].std(ddof=0); X[c] = (X[c] - X[c].mean()) / (sd if sd > 0 else 1.0)    # StandardScaler (ddof=0)
    return X, D["y" if task == "reg" else "label"].values

def tuned_params(arm, task):
    """Most frequent (max_depth, min_samples_leaf) among tuned Decision tree CV fits; fallback (3, 1)."""
    try:
        P = pd.read_csv(RES / f"ml_{arm}_{task}_cv_params.csv"); P = P[P.method.str.contains("Decision tree (tuned", regex=False)]
        c = collections.Counter((ast.literal_eval(s).get("est__max_depth"), ast.literal_eval(s).get("est__min_samples_leaf", 1)) for s in P.params)
        if c: (md, ml), _ = c.most_common(1)[0]; return md, ml
    except Exception: pass
    return 3, 1

def tree_fig(arm, task):
    X, y = load_scaled(arm, task); md, ml = tuned_params(arm, task)
    est = (DecisionTreeRegressor if task == "reg" else DecisionTreeClassifier)(max_depth=md, min_samples_leaf=ml, random_state=0).fit(X, y)
    sh = min(3, md if md is not None else 3); w = max(14, 5 * 2 ** max(sh - 1, 0)); fig, ax = plt.subplots(figsize=(w, 3 + 2.2 * sh))
    plot_tree(est, feature_names=list(X.columns), filled=True, rounded=True, fontsize=9, max_depth=3, impurity=False, proportion=True, ax=ax,
              class_names=None if task == "reg" else ["non-responder", "responder"])
    ax.set_title(f"{arm} - {LAB[task]}: decision tree (depth<=3 shown; tuned params max_depth={md}, min_samples_leaf={ml})", fontsize=13)
    fig.savefig(OUT / f"tree_{arm}_{task}.png", dpi=130, bbox_inches="tight"); plt.close(fig)

if __name__ == "__main__":
    combos = [(sys.argv[1], sys.argv[2])] if len(sys.argv) >= 3 else [(a, t) for a in ARMS for t in ("reg", "bin")]
    for arm, task in combos:
        try: tree_fig(arm, task); print("s09 OK", arm, task, flush=True)
        except Exception as e: (OUT / f"_FAILED_tree_{arm}_{task}.txt").write_text(repr(e)); print("s09 FAILED", arm, task, e, flush=True)
