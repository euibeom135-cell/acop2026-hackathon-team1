"""Machine-learning methods from the kickoff PDF (scikit-learn / xgboost), each as an UNTUNED (PDF snippet settings) and TUNED (small GridSearchCV) row.
Every estimator is a Pipeline(pre -> est) where `pre` z-scores ONLY the numeric covariates (0/1 dummies pass through unscaled). Because the scaler lives inside the pipeline it is re-fitted on the
training rows of every CV fold (and of every inner GridSearchCV fold). Trees / forests / XGBoost are invariant to monotone per-column rescaling, so they receive the same pipeline output; this is stated, not tuned."""
import numpy as np
from sklearn.base import clone
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.svm import SVR, SVC
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, KFold, StratifiedKFold
from xgboost import XGBRegressor, XGBClassifier

S = 42
TREE_GRID = {"max_depth": [2, 3, 5, None], "min_samples_leaf": [1, 5, 10]}
def _ttr(m): return TransformedTargetRegressor(regressor=m, transformer=StandardScaler())     # SVR/MLP need a scaled target
def _p(prefix, g): return {f"{prefix}__{k}": v for k, v in g.items()}

def make_pre(num_cols, all_cols):
    """Scale numeric columns only; dummies are passed through unchanged. Output keeps pandas column names."""
    keep = [c for c in all_cols if c not in num_cols]
    return ColumnTransformer([("num", StandardScaler(), list(num_cols)), ("dum", "passthrough", keep)], verbose_feature_names_out=False).set_output(transform="pandas")

def registry(task):
    """-> list of dict(name, est, grid, scoring). Grid keys are relative to the bare estimator and get the 'est__' pipeline prefix in variants()."""
    reg = task == "reg"; sc = "neg_root_mean_squared_error" if reg else "roc_auc"; R = []
    def add(name, est, grid): R.append(dict(name=name, est=est, grid=grid, scoring=sc))
    if not reg: add("Logistic regression", LogisticRegression(max_iter=2000), {"C": [0.01, 0.1, 1, 10, 100]})
    add("Decision tree", (DecisionTreeRegressor(max_depth=3, random_state=S) if reg else DecisionTreeClassifier(max_depth=3, random_state=S)), TREE_GRID)
    add("Random forest", (RandomForestRegressor(300, random_state=S, n_jobs=1) if reg else RandomForestClassifier(300, random_state=S, n_jobs=1)), TREE_GRID)
    if reg:
        add("SVM (RBF)", _ttr(SVR(kernel="rbf")), _p("regressor", {"C": [0.1, 1, 10], "gamma": ["scale", 0.01, 0.1]}))
        add("KNN", KNeighborsRegressor(7), {"n_neighbors": [3, 5, 7, 11, 15, 21], "weights": ["uniform", "distance"]})
        add("XGBoost", XGBRegressor(n_estimators=200, max_depth=3, random_state=S, n_jobs=1), {"max_depth": [2, 3, 4], "n_estimators": [100, 300], "learning_rate": [.03, .1], "subsample": [.8]})
        add("MLP (16,)", _ttr(MLPRegressor(hidden_layer_sizes=(16,), max_iter=3000, random_state=S)), _p("regressor", {"hidden_layer_sizes": [(8,), (16,), (32,)], "alpha": [1e-4, 1e-2, 1.0]}))
    else:
        add("SVM (RBF)", SVC(kernel="rbf", probability=True, random_state=S), {"C": [0.1, 1, 10], "gamma": ["scale", 0.01, 0.1]})
        add("KNN", KNeighborsClassifier(7), {"n_neighbors": [3, 5, 7, 11, 15, 21], "weights": ["uniform", "distance"]})
        add("XGBoost", XGBClassifier(n_estimators=200, max_depth=3, random_state=S, n_jobs=1), {"max_depth": [2, 3, 4], "n_estimators": [100, 300], "learning_rate": [.03, .1], "subsample": [.8]})
        add("MLP (16,)", MLPClassifier(hidden_layer_sizes=(16,), max_iter=3000, random_state=S), {"hidden_layer_sizes": [(8,), (16,), (32,)], "alpha": [1e-4, 1e-2, 1.0]})
    return R

def variants(task, num_cols, all_cols):
    """Rows: (label, builder(), tuned flag, registry entry). builder() returns a fresh Pipeline (untuned) or GridSearchCV over the pipeline (inner 3-fold on whatever data it is fitted on)."""
    out = []; mk = lambda r: Pipeline([("pre", make_pre(num_cols, all_cols)), ("est", clone(r["est"]))])
    for r in registry(task):
        out.append((f"{r['name']} (untuned)", (lambda r=r: mk(r)), False, r))
        cv = KFold(3, shuffle=True, random_state=0) if task == "reg" else StratifiedKFold(3, shuffle=True, random_state=0)
        out.append((f"{r['name']} (tuned, GridSearchCV)", (lambda r=r, cv=cv: GridSearchCV(mk(r), {f"est__{k}": v for k, v in r["grid"].items()}, scoring=r["scoring"], cv=cv, n_jobs=1)), True, r))
    return out

def predict(model, X, task):
    return model.predict(X) if task == "reg" else model.predict_proba(X)[:, 1]
