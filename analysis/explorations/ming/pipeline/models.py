"""The method library: 14 continuous + 14 binary methods, one interface.

Each builder returns a FittedModel with:
  .predict(frame)   -> yhat (continuous) or score in-model-scale (binary)
  .kept_terms       -> list[str] of raw terms the method selected (inference), or
                       None for pure-prediction methods (filled from test-row
                       permutation importance by the runner)
  .coef             -> {term: standardized effect} where defined
  .cutoff           -> Youden cutoff from training OOF (binary only)
Tiers: 'inference' (covariate lists/signs/shapes), 'prediction' (the ceiling).
"""
from __future__ import annotations
import warnings, itertools, sys, os
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.base import clone
from sklearn.linear_model import (LassoCV, ElasticNetCV, RidgeCV,
                                   LogisticRegression, LogisticRegressionCV)
from sklearn.ensemble import (RandomForestRegressor, RandomForestClassifier,
                              HistGradientBoostingRegressor, HistGradientBoostingClassifier)
from sklearn.svm import SVR, SVC
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.model_selection import GridSearchCV, cross_val_predict, RepeatedKFold, RepeatedStratifiedKFold
import statsmodels.api as sm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
from pipeline.data import Transform

warnings.filterwarnings("ignore")


def _y(frame, task):
    return frame["y_cont"].values.astype(float) if task == "continuous" else frame["y_bin"].values.astype(int)


def _cv(task, n_splits=None, repeats=None):
    n_splits = n_splits or C.CV_SPLITS
    repeats = repeats or C.CV_REPEATS
    if task == "continuous":
        return RepeatedKFold(n_splits=n_splits, n_repeats=repeats, random_state=C.SEED)
    return RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=repeats, random_state=C.SEED)


class FittedModel:
    def __init__(self, name, tier, task, predict, kept_terms=None, coef=None, cutoff=None):
        self.name = name; self.tier = tier; self.task = task
        self._predict = predict
        self.kept_terms = kept_terms
        self.coef = coef or {}
        self.cutoff = cutoff

    def predict(self, frame):
        return self._predict(frame)


# ---------------------------------------------------------------------------
# statsmodels inference methods (OLS / Logit): coefficients, p-values, AIC/BIC
# ---------------------------------------------------------------------------
def _sm_fit(design, y, task):
    X = sm.add_constant(design, has_constant="add")
    if task == "continuous":
        return sm.OLS(y, X).fit()
    return sm.Logit(y, X).fit(disp=0, maxiter=200)


def _sm_predict_fn(tf: Transform, terms, params, task):
    cols = []
    for t in terms:
        cols += tf.term_cols_[t]
    cols = sorted(cols)
    beta = params  # includes const first

    def predict(frame):
        D = tf.transform(frame)
        X = D[:, cols] if cols else np.empty((len(frame), 0))
        X = np.hstack([np.ones((len(frame), 1)), X])
        eta = X @ beta
        return expit(eta) if task == "binary" else eta
    return predict


def _coef_by_term(tf: Transform, terms, params):
    """Map design-column coefficients back to raw terms (max |coef| for blocks)."""
    out = {}
    idx = 1  # skip const
    for t in terms:
        k = len(tf.term_cols_[t])
        block = params[idx:idx + k]
        idx += k
        out[t] = float(block[np.argmax(np.abs(block))]) if k else 0.0
    return out


def _fit_sm_subset(train, arm, task, terms):
    tf = Transform(arm, kind="linear").fit(train)
    D = tf.transform(train)
    cols = sorted([c for t in terms for c in tf.term_cols_[t]])
    X = D[:, cols] if cols else np.empty((len(train), 0))
    res = _sm_fit(X, _y(train, task), task)
    params = res.params
    predict = _sm_predict_fn(tf, terms, params, task)
    coef = _coef_by_term(tf, terms, params)
    return tf, res, predict, coef


def build_ols_all(train, arm, task):
    terms = Transform(arm).raw_terms
    tf, res, predict, coef = _fit_sm_subset(train, arm, task, terms)
    # kept = terms with any dummy p<0.05
    kept, idx, pv = [], 1, res.pvalues
    for t in terms:
        k = len(tf.term_cols_[t])
        if np.nanmin(pv[idx:idx + k]) < 0.05:
            kept.append(t)
        idx += k
    name = "OLS all" if task == "continuous" else "Logistic all"
    return FittedModel(name, "inference", task, predict, kept_terms=kept, coef=coef)


def _stepwise(train, arm, task, crit):
    all_terms = Transform(arm).raw_terms
    selected, remaining = [], list(all_terms)
    def score(terms):
        _, res, _, _ = _fit_sm_subset(train, arm, task, terms)
        return res.aic if crit == "aic" else res.bic
    best = score([])
    improved = True
    while improved:
        improved = False
        # forward
        cand = [(score(selected + [t]), t) for t in remaining]
        if cand:
            s, t = min(cand)
            if s < best - 1e-6:
                best = s; selected.append(t); remaining.remove(t); improved = True
        # backward
        if len(selected) > 1:
            cand = [(score([x for x in selected if x != t]), t) for t in selected]
            s, t = min(cand)
            if s < best - 1e-6:
                best = s; selected.remove(t); remaining.append(t); improved = True
    tf, res, predict, coef = _fit_sm_subset(train, arm, task, selected)
    tag = crit.upper()
    base = "Stepwise" if task == "continuous" else "Logistic stepwise"
    return FittedModel(f"{base} {tag}", "inference", task, predict,
                       kept_terms=selected, coef=coef)


def build_stepwise_aic(train, arm, task): return _stepwise(train, arm, task, "aic")
def build_stepwise_bic(train, arm, task): return _stepwise(train, arm, task, "bic")


def build_best_subset(train, arm, task, max_terms=5, pool=10):
    all_terms = Transform(arm).raw_terms
    # pre-screen to the strongest marginal terms to keep it exhaustive-but-cheap
    y = _y(train, task)
    strength = {}
    for t in all_terms:
        _, res, _, _ = _fit_sm_subset(train, arm, task, [t])
        strength[t] = res.bic
    pool_terms = sorted(all_terms, key=lambda t: strength[t])[:pool]
    best_bic, best_terms = np.inf, []
    for r in range(1, max_terms + 1):
        for combo in itertools.combinations(pool_terms, r):
            _, res, _, _ = _fit_sm_subset(train, arm, task, list(combo))
            if res.bic < best_bic:
                best_bic, best_terms = res.bic, list(combo)
    tf, res, predict, coef = _fit_sm_subset(train, arm, task, best_terms)
    base = "Best subset" if task == "continuous" else "Logistic best subset"
    return FittedModel(base, "inference", task, predict, kept_terms=best_terms, coef=coef)


# ---------------------------------------------------------------------------
# penalized linear / logistic
# ---------------------------------------------------------------------------
def _penalized_predict(tf, est, task):
    def predict(frame):
        D = tf.transform(frame)
        if task == "continuous":
            return est.predict(D)
        return est.predict_proba(D)[:, 1]
    return predict


def _coef_terms_from_vector(tf, coef_vec):
    out = {}
    for t, cols in tf.term_cols_.items():
        block = coef_vec[cols]
        out[t] = float(block[np.argmax(np.abs(block))]) if len(block) else 0.0
    kept = [t for t, v in out.items() if abs(v) > 1e-8]
    return out, kept


def _build_penalized(train, arm, task, which):
    tf = Transform(arm, kind="linear").fit(train)
    D = tf.transform(train); y = _y(train, task)
    cv = _cv(task)
    if task == "continuous":
        if which == "lasso":
            est = LassoCV(cv=cv, random_state=C.SEED, max_iter=50000, n_jobs=C.N_JOBS)
        elif which == "enet":
            est = ElasticNetCV(l1_ratio=[.2, .5, .8, .95], cv=cv, random_state=C.SEED,
                               max_iter=50000, n_jobs=C.N_JOBS)
        else:  # ridge
            est = RidgeCV(alphas=np.logspace(-3, 3, 25))
        est.fit(D, y); coef_vec = est.coef_
    else:
        Cs = np.logspace(-3, 3, 15)
        if which == "lasso":
            est = LogisticRegressionCV(Cs=Cs, cv=cv, penalty="l1", solver="liblinear",
                                       scoring="roc_auc", max_iter=5000)
        elif which == "enet":
            est = LogisticRegressionCV(Cs=Cs, cv=cv, penalty="elasticnet", solver="saga",
                                       l1_ratios=[.5], scoring="roc_auc", max_iter=10000, n_jobs=C.N_JOBS)
        else:
            est = LogisticRegressionCV(Cs=Cs, cv=cv, penalty="l2", solver="lbfgs",
                                       scoring="roc_auc", max_iter=5000)
        est.fit(D, y); coef_vec = est.coef_.ravel()
    coef, kept = _coef_terms_from_vector(tf, coef_vec)
    if which == "ridge":  # ridge keeps all; report top by |coef|
        kept = sorted(coef, key=lambda t: -abs(coef[t]))[:C.TOP_K_IMPORTANCE]
    predict = _penalized_predict(tf, est, task)
    cutoff = _oof_cutoff(clone(est), D, y, task)
    names = {"lasso": "LASSO", "enet": "Elastic net", "ridge": "Ridge"}
    nm = names[which] + ("" if task == "continuous" else " logistic")
    return FittedModel(nm, "inference", task, predict, kept_terms=kept, coef=coef, cutoff=cutoff)


def build_lasso(train, arm, task): return _build_penalized(train, arm, task, "lasso")
def build_enet(train, arm, task): return _build_penalized(train, arm, task, "enet")
def build_ridge(train, arm, task): return _build_penalized(train, arm, task, "ridge")


# ---------------------------------------------------------------------------
# GAM via cubic B-splines + ridge / logistic (shapes come from PD plots later)
# ---------------------------------------------------------------------------
def build_gam(train, arm, task):
    tf = Transform(arm, kind="spline").fit(train)
    D = tf.transform(train); y = _y(train, task)
    if task == "continuous":
        est = RidgeCV(alphas=np.logspace(-3, 3, 25)); est.fit(D, y); coef_vec = est.coef_
    else:
        est = LogisticRegression(penalty="l2", C=1.0, max_iter=5000); est.fit(D, y)
        coef_vec = est.coef_.ravel()
    # per-term effect = L2 norm of its spline block
    coef = {t: float(np.linalg.norm(coef_vec[cols])) for t, cols in tf.term_cols_.items()}
    kept = sorted(coef, key=lambda t: -coef[t])[:C.TOP_K_IMPORTANCE]
    predict = _penalized_predict(tf, est, task)
    cutoff = _oof_cutoff(clone(est), D, y, task)
    nm = "GAM" if task == "continuous" else "GAM logistic"
    return FittedModel(nm, "inference", task, predict, kept_terms=kept, coef=coef, cutoff=cutoff)


# ---------------------------------------------------------------------------
# prediction tier (trees / SVM / kNN / MLP)
# ---------------------------------------------------------------------------
def _oof_cutoff(est, D, y, task):
    if task != "binary":
        return None
    from pipeline.metrics import youden_cutoff
    try:
        oof = cross_val_predict(est, D, y, cv=_cv(task, repeats=1),
                                method="predict_proba", n_jobs=C.N_JOBS)[:, 1]
    except Exception:
        oof = cross_val_predict(est, D, y, cv=_cv(task, repeats=1),
                                method="decision_function", n_jobs=C.N_JOBS)
    return youden_cutoff(y, oof)


def _ml_predict(tf, est, task):
    def predict(frame):
        D = tf.transform(frame)
        if task == "continuous":
            return est.predict(D)
        if hasattr(est, "predict_proba"):
            return est.predict_proba(D)[:, 1]
        return est.decision_function(D)
    return predict


def _build_ml(train, arm, task, est, name, grid=None):
    tf = Transform(arm, kind="tree").fit(train)
    D = tf.transform(train); y = _y(train, task)
    if grid:
        scoring = "r2" if task == "continuous" else "roc_auc"
        gs = GridSearchCV(est, grid, cv=_cv(task, repeats=1), scoring=scoring, n_jobs=C.N_JOBS)
        gs.fit(D, y); est = gs.best_estimator_
    else:
        est.fit(D, y)
    predict = _ml_predict(tf, est, task)
    cutoff = _oof_cutoff(clone(est), D, y, task)
    return FittedModel(name, "prediction", task, predict, kept_terms=None, cutoff=cutoff)


def build_rf(train, arm, task):
    est = (RandomForestRegressor if task == "continuous" else RandomForestClassifier)(
        n_estimators=500, random_state=C.SEED, n_jobs=C.N_JOBS)
    return _build_ml(train, arm, task, est, "Random forest")


def build_gbm_untuned(train, arm, task):
    est = (HistGradientBoostingRegressor if task == "continuous" else HistGradientBoostingClassifier)(
        random_state=C.SEED)
    return _build_ml(train, arm, task, est, "Gradient boosting (untuned)")


def build_gbm_tuned(train, arm, task):
    est = (HistGradientBoostingRegressor if task == "continuous" else HistGradientBoostingClassifier)(
        random_state=C.SEED)
    grid = {"max_depth": [2, 3, None], "learning_rate": [0.03, 0.1], "max_iter": [200, 400]}
    return _build_ml(train, arm, task, est, "Gradient boosting (tuned)", grid)


def build_svm(train, arm, task):
    if task == "continuous":
        est = SVR(); grid = {"C": [0.3, 1, 3, 10], "gamma": ["scale", 0.05, 0.1]}
    else:
        est = SVC(probability=True, random_state=C.SEED)
        grid = {"C": [0.3, 1, 3, 10], "gamma": ["scale", 0.05, 0.1]}
    return _build_ml(train, arm, task, est, "SVM (tuned)", grid)


def build_knn(train, arm, task):
    est = (KNeighborsRegressor if task == "continuous" else KNeighborsClassifier)()
    grid = {"n_neighbors": [5, 10, 15, 20, 30], "weights": ["uniform", "distance"]}
    return _build_ml(train, arm, task, est, "kNN (tuned)", grid)


def build_mlp(train, arm, task):
    if task == "continuous":
        est = MLPRegressor(max_iter=2000, random_state=C.SEED, early_stopping=True)
    else:
        est = MLPClassifier(max_iter=2000, random_state=C.SEED, early_stopping=True)
    grid = {"hidden_layer_sizes": [(16,), (32,), (16, 8)], "alpha": [1e-4, 1e-2, 1e-1]}
    return _build_ml(train, arm, task, est, "MLP (tuned)", grid)


# ---------------------------------------------------------------------------
# registry (ordered; tier annotated by builder)
# ---------------------------------------------------------------------------
BUILDERS = {
    "ols_all": build_ols_all,
    "stepwise_aic": build_stepwise_aic,
    "stepwise_bic": build_stepwise_bic,
    "best_subset": build_best_subset,
    "lasso": build_lasso,
    "enet": build_enet,
    "ridge": build_ridge,
    "gam": build_gam,
    "random_forest": build_rf,
    "gbm_untuned": build_gbm_untuned,
    "gbm_tuned": build_gbm_tuned,
    "svm": build_svm,
    "knn": build_knn,
    "mlp": build_mlp,
}
INFERENCE = ["ols_all", "stepwise_aic", "stepwise_bic", "best_subset",
             "lasso", "enet", "ridge", "gam"]
PREDICTION = ["random_forest", "gbm_untuned", "gbm_tuned", "svm", "knn", "mlp"]
CHEAP = ["ols_all", "lasso", "ridge", "random_forest", "gbm_untuned"]  # for repeat20
