#!/usr/bin/env python3
"""Build the locked 5-fold partition and the split-sensitivity manifests.

fold 1 = the Oct 11 locked test set (hash recorded for the G3 check).
folds 2-5 = a stratified 4-way split of the Oct 11 training set (seed 2026),
            strata = responder label x within-label median of the continuous
            target, so both the regression and classification views stay
            balanced.
Sensitivity schemes (single80 / single75 / repeat20) resplit ONLY folds 2-5
(the 399 training patients) so the locked 101 are never scored in rehearsal.
"""
from __future__ import annotations
import sys, os, json, hashlib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
from pipeline.data import load_raw, make_arm_frame


def strata(frame: pd.DataFrame) -> np.ndarray:
    """responder label x within-label median split of the continuous target."""
    s = frame["y_bin"].astype(str).copy()
    out = s.values.astype(object)
    for lab in frame["y_bin"].unique():
        m = frame["y_bin"] == lab
        med = frame.loc[m, "y_cont"].median()
        hi = (frame["y_cont"] > med) & m
        out[hi.values] = f"{lab}_hi"
        out[(~hi & m).values] = f"{lab}_lo"
    return out


def main():
    os.makedirs(C.DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(C.OUT, "splits"), exist_ok=True)
    df = load_raw()
    part = pd.read_csv(os.path.join(C.ROOT, "results", "tables", "patient_partitions.csv"))
    locked_test = set(part.loc[part.partition == "Test", "patient_id"])

    rows = []
    summary = {"seed": C.SEED, "arms": {}}
    for arm in C.ARMS:
        g = make_arm_frame(df, arm)
        g_test = g[g.patient_id.isin(locked_test)].copy()
        g_train = g[~g.patient_id.isin(locked_test)].copy().reset_index(drop=True)
        for pid in g_test.patient_id:
            rows.append({"patient_id": pid, "treatment_arm": arm, "fold": 1})
        skf = StratifiedKFold(n_splits=4, shuffle=True, random_state=C.SEED)
        lab = strata(g_train)
        for k, (_, idx) in enumerate(skf.split(g_train, lab), start=2):
            for pid in g_train.iloc[idx].patient_id:
                rows.append({"patient_id": pid, "treatment_arm": arm, "fold": k})
        summary["arms"][arm] = {
            "fold1_test_n": int(len(g_test)),
            "train_n": int(len(g_train)),
        }

    folds = pd.DataFrame(rows).sort_values(["treatment_arm", "fold", "patient_id"])
    folds.to_csv(os.path.join(C.DATA_DIR, "folds_5fold_seed2026.csv"), index=False)
    folds.to_csv(os.path.join(C.OUT, "splits", "fold5_manifest.csv"), index=False)

    # per-fold counts + fold-1 hash for the G3 custodian check
    counts = folds.groupby(["treatment_arm", "fold"]).size().unstack(fill_value=0)
    summary["fold_counts"] = json.loads(counts.to_json())
    fold1_ids = sorted(folds.loc[folds.fold == 1, "patient_id"])
    summary["fold1_sha256"] = hashlib.sha256("\n".join(fold1_ids).encode()).hexdigest()
    summary["fold1_n"] = len(fold1_ids)

    # sensitivity manifests on folds 2-5 only
    train_mask = folds.fold != 1
    train_ids = set(folds.loc[train_mask, "patient_id"])
    def write_single(frac_test, name):
        recs = []
        for arm in C.ARMS:
            g = make_arm_frame(df, arm)
            g = g[g.patient_id.isin(train_ids)].reset_index(drop=True)
            tr, te = train_test_split(g.index, test_size=frac_test, random_state=C.SEED,
                                      stratify=strata(g))
            for i in g.index:
                recs.append({"patient_id": g.loc[i, "patient_id"], "treatment_arm": arm,
                             "partition": "Test" if i in set(te) else "Train"})
        pd.DataFrame(recs).to_csv(os.path.join(C.OUT, "splits", f"{name}.csv"), index=False)
    write_single(0.20, "single80")
    write_single(0.25, "single75")
    seeds = [C.SEED + i for i in range(C.REPEAT_SEEDS)]
    json.dump({"seeds": seeds, "scope": "folds 2-5 (399 training patients)",
               "test_fraction": 0.20},
              open(os.path.join(C.OUT, "splits", "repeat20_seeds.json"), "w"), indent=2)

    json.dump(summary, open(os.path.join(C.OUT, "splits", "summary.json"), "w"), indent=2)
    print(json.dumps(summary, indent=2))
    print("\nfolds written:", os.path.join(C.DATA_DIR, "folds_5fold_seed2026.csv"))


if __name__ == "__main__":
    main()
