"""Run ONE seed of the sensitivity analysis: new 1:3 re-randomised split -> fit every method on train -> score on test -> per-covariate evidence.
usage: python seed_run.py <seed>. Output results/seed_<s>/{perf.csv, evidence.csv, split.csv, balance.csv}. ML models use n_jobs=3 (several seeds run in parallel)."""
import sys, subprocess, warnings; warnings.filterwarnings("ignore")
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1] / "src"))
from joblib import Parallel, delayed
from seed_split import *
from ml_models import variants, predict
from metrics import *
from sklearn.inspection import permutation_importance
seed = int(sys.argv[1]); OUT = HERE.parent / "results" / f"seed_{seed}"; OUT.mkdir(parents=True, exist_ok=True)
split, bal = build_split(seed); split.to_csv(OUT / "split.csv", index=False); bal.to_csv(OUT / "balance.csv", index=False)
PARENT = lambda c: next((p for p in ("phenotype", "smoking_status", "family_history", "sex", "cataracts") if c.startswith(p + "_")), c)
def parent_of(term):
    import re; m = re.search(r"(?:poly|bs)\(([^,)]+)", term); t = m.group(1) if m else re.sub(r"_bin.*$", "", term); t = re.sub(r"#?\d+$", "", t) if (m or "_bin" in term) else t
    return PARENT(t)
def ml_fit(vi, Ztr, y, Zte, yte, task):
    nm, build, tuned, r = variants(task)[vi]; m = build().fit(Ztr, y); p = predict(m, Zte, task)
    imp = None
    if tuned:
        pi = permutation_importance(m, Zte, yte, n_repeats=20, scoring=r["scoring"], random_state=0); imp = pd.DataFrame(dict(term=Zte.columns, mean=pi.importances_mean, se=pi.importances_std / np.sqrt(20)))
    return nm, p, imp
perf, evid = [], []
for arm in ARMS:
    d = get_arm(arm, test=True, split=split); Ztr, Zte = d["Ztr"].reset_index(drop=True), d["Zte"].reset_index(drop=True)
    for tag, Z, y, l in (("train", Ztr, d["ytr"], d["ltr"]), ("test", Zte, d["yte"], d["lte"])):
        D = Z.copy(); D.insert(0, "y", y.values); D.insert(1, "label", l.values); D.to_csv(OUT / f"{tag}_{arm}.csv", index=False)
    for task in ("reg", "bin"):
        r = subprocess.run(["Rscript", str(HERE / "r_seed.R"), arm, task, str(OUT)], capture_output=True, text=True); 
        if r.returncode: print(r.stderr[-400:])
        ytr = (d["ytr"] if task == "reg" else d["ltr"]).values; yte = (d["yte"] if task == "reg" else d["lte"]).values; n = len(yte); preds = {}
        Rp = pd.read_csv(OUT / f"r_{arm}_{task}_preds.csv")
        for nm, g in Rp.groupby("method"): preds[nm] = (g.sort_values("row").pred.values, "Covariate")
        V = variants(task); out = Parallel(n_jobs=3)(delayed(ml_fit)(vi, Ztr, ytr, Zte, yte, task) for vi in range(len(V)))
        for nm, p, imp in out:
            preds[nm] = (p, "ML")
            if imp is not None:
                imp["selected"] = (imp["mean"] - 1.96 * imp["se"] > 0) & (imp["mean"] >= 0.10 * imp["mean"].max()); imp["covariate"] = imp.term.map(PARENT); imp = imp.groupby("covariate", as_index=False).agg(selected=("selected", "max"), imp=("mean", "max"))
                evid.append(imp.assign(seed=seed, arm=arm, task=task, method=nm.replace(" (tuned, GridSearchCV)", " (tuned)"), p=np.nan, coef=np.nan, kind="perm_importance"))
        preds["Mean only" if task == "reg" else "Prevalence only"] = (np.full(n, ytr.mean()), "Baseline")
        for nm, (p, fam) in preds.items():
            if np.isnan(p).any(): continue
            if task == "reg": rec = reg_metrics(yte, p)
            else:
                cut = np.quantile(p, 1 - ytr.mean()) if p.std() > 0 else 1.0; rec = bin_metrics(yte, p, cut)      # prevalence-matched cutoff: label-free rule, no tuning on test
            perf.append(dict(seed=seed, arm=arm, task=task, method=nm, family=fam, **rec))
        Ev = pd.read_csv(OUT / f"r_{arm}_{task}_evidence.csv"); Ev["covariate"] = Ev.term.map(parent_of)
        Ev["selected"] = np.where(Ev.p.notna(), Ev.p < 0.05, True)                              # p-value methods: p<.05; glmnet: non-zero coefficient
        Ev = Ev.groupby(["method", "covariate"], as_index=False).agg(selected=("selected", "max"), p=("p", "min"), coef=("coef", "mean"))
        evid.append(Ev.assign(seed=seed, arm=arm, task=task, kind="p_or_nonzero"))
    print("seed", seed, arm, "done", flush=True)
pd.DataFrame(perf).to_csv(OUT / "perf.csv", index=False); pd.concat(evid).to_csv(OUT / "evidence.csv", index=False)
for f in OUT.glob("train_*.csv"): f.unlink()
for f in OUT.glob("test_*.csv"): f.unlink()
print("seed", seed, "finished")
