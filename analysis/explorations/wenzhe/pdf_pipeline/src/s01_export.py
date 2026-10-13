"""S01: export per-arm TRAIN feature matrices (UNSCALED; scaling is done inside each fit) + shared CV folds for the R side. The TEST feature matrix is exported only by s07 (the single scoring pass)."""
from pcommon import *
sp = split_table(); print(sp.groupby(["arm", "set"]).size().unstack().to_string())
for arm in ARMS:
    d = get_arm(arm); D = d["Xtr"].copy(); D.insert(0, "y", d["ytr"].values); D.insert(1, "label", d["ltr"].values); D.to_csv(ARES / f"features_train_{arm}.csv", index=False)
    folds(arm, d["ltr"]).to_csv(ARES / f"folds_{arm}.csv", index=False)
    pd.DataFrame(dict(feature=d["Xtr"].columns, parent=[d["parent"][c] for c in d["Xtr"].columns], domain=[DOMAIN[d["parent"][c]] for c in d["Xtr"].columns], numeric=[c in d["num"] for c in d["Xtr"].columns])).to_csv(ARES / f"feature_map_{arm}.csv", index=False)
    print(arm, D.shape, "numeric z-scored:", len(d["num"]), "dummies left raw:", D.shape[1] - 2 - len(d["num"]))
