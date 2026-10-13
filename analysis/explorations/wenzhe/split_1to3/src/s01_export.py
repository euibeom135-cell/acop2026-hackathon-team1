"""S01: export per-arm TRAIN (and, only for the final scoring, TEST) matrices + shared CV folds for the R side. Test is exported separately by s06."""
from scommon import *
for arm in ARMS:
    d = get_arm(arm); D = d["Ztr"].copy(); D.insert(0, "y", d["ytr"].values); D.insert(1, "label", d["ltr"].values); D.to_csv(ARES / f"train_{arm}.csv", index=False)
    folds(arm, d["ltr"]).to_csv(ARES / f"folds_{arm}.csv", index=False)
    print(arm, D.shape)
