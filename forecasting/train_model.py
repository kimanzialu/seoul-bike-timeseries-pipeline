"""
Rebuild the Task 1 model bundle (models/seoul_bike_rf_one_hour.joblib).

This is a script version of Task 1 section C: the same features, the same
chronological 85/15 split, the same three Random Forest experiments scored by
3-fold TimeSeriesSplit, and selection by mean CV MAE. Use it when the joblib
file from the notebook isn't on your machine, since trained models are not
committed to git.

    python -m forecasting.train_model
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

from forecasting.preprocessing import (FEATURE_COLUMNS, TARGET, load_raw_csv,
                                       make_forecasting_features)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "data" / "SeoulBikeData.csv"
DEFAULT_MODEL = ROOT / "models" / "seoul_bike_rf_one_hour.joblib"

EXPERIMENTS = [
    {"experiment": "RF_1", "n_estimators": 80, "max_depth": 10, "min_samples_leaf": 4},
    {"experiment": "RF_2", "n_estimators": 140, "max_depth": 14, "min_samples_leaf": 2},
    {"experiment": "RF_3", "n_estimators": 180, "max_depth": None, "min_samples_leaf": 2},
]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--out", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()

    df = load_raw_csv(args.csv)
    features = make_forecasting_features(df)
    model_data = features.dropna(subset=FEATURE_COLUMNS + [TARGET])
    X, y = model_data[FEATURE_COLUMNS], model_data[TARGET]
    split_idx = int(len(X) * 0.85)
    X_dev, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_dev, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    print(f"Dev {X_dev.index.min()} -> {X_dev.index.max()} ({len(X_dev)} rows)")
    print(f"Test {X_test.index.min()} -> {X_test.index.max()} ({len(X_test)} rows)")

    rows = []
    for params in EXPERIMENTS:
        started, maes = time.perf_counter(), []
        for train_idx, valid_idx in TimeSeriesSplit(n_splits=3).split(X_dev):
            rf = RandomForestRegressor(n_estimators=params["n_estimators"],
                                       max_depth=params["max_depth"],
                                       min_samples_leaf=params["min_samples_leaf"],
                                       random_state=42, n_jobs=-1)
            rf.fit(X_dev.iloc[train_idx], y_dev.iloc[train_idx])
            pred = np.clip(rf.predict(X_dev.iloc[valid_idx]), 0, None)
            maes.append(mean_absolute_error(y_dev.iloc[valid_idx], pred))
        rows.append({**params, "cv_mae_mean": float(np.mean(maes)),
                     "runtime_s": round(time.perf_counter() - started, 1)})
        print(f"  {params['experiment']}: CV MAE {np.mean(maes):.2f}")

    best = min(rows, key=lambda r: r["cv_mae_mean"])
    selected = {"n_estimators": best["n_estimators"], "max_depth": best["max_depth"],
                "min_samples_leaf": best["min_samples_leaf"],
                "random_state": 42, "n_jobs": -1}
    model = RandomForestRegressor(**selected).fit(X_dev, y_dev)
    test_pred = np.clip(model.predict(X_test), 0, None)
    metrics = {
        "selected_experiment": best["experiment"],
        "cv_mae_mean": best["cv_mae_mean"],
        "test_mae": float(mean_absolute_error(y_test, test_pred)),
        "test_rmse": float(np.sqrt(mean_squared_error(y_test, test_pred))),
        "test_r2": float(r2_score(y_test, test_pred)),
    }
    print("Selected", best["experiment"], json.dumps(metrics, indent=2))

    # Same keys as the notebook's bundle, plus metrics so the predict script can report them.
    bundle = {
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
        "forecast_horizon_hours": 1,
        "hyperparameters": selected,
        "training_target": TARGET,
        "last_training_timestamp": str(X_dev.index.max()),
        "metrics": metrics,
        "experiments": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    dump(bundle, args.out, compress=3)
    print(f"Saved {args.out} ({args.out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
