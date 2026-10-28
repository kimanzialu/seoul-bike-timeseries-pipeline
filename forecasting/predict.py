"""
Task 4: end-to-end one-hour-ahead forecast.

    1. Fetch      the last 168 hourly records from the Task 3 API (SQL or MongoDB)
    2. Preprocess with the Task 1 cleaning steps and feature formulas
    3. Load       the trained Random Forest bundle (joblib)
    4. Predict    rented_bike_count for the next hour

Usage (start the API first: uvicorn app.main:app --reload):

    python -m forecasting.predict                      # next hour after the latest record, via MySQL
    python -m forecasting.predict --source mongo       # same, via MongoDB
    python -m forecasting.predict --at "2018-11-30 18:00"   # backtest a known hour and compare with the actual value
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from joblib import load

from forecasting.api_client import SOURCES, ApiError, BikeApiClient
from forecasting.preprocessing import (FEATURE_COLUMNS, REQUIRED_HISTORY_HOURS,
                                       PreprocessingError, build_next_hour_features,
                                       clean_records)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "models" / "seoul_bike_rf_one_hour.joblib"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "predictions"


def load_bundle(path: Path) -> dict:
    """Load the model bundle and check it matches the features this code builds."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Model not found at {path}. Copy the joblib saved by the Task 1 notebook "
            "there, or rebuild it with: python -m forecasting.train_model"
        )
    bundle = load(path)
    if list(bundle["feature_columns"]) != FEATURE_COLUMNS:
        raise ValueError("Model was trained on different features than this pipeline builds.")
    return bundle


def run_forecast(client: BikeApiClient, model_path: Path = DEFAULT_MODEL,
                 at: datetime | None = None, max_gap_fill: int = 3,
                 verbose: bool = True) -> dict:
    """Run the full pipeline and return the result as a dict."""
    log = print if verbose else (lambda *a, **k: None)

    # 1. Fetch
    if at is None:
        end = datetime.fromisoformat(client.get_latest()["timestamp"])
    else:
        end = at - timedelta(hours=1)
    start = end - timedelta(hours=REQUIRED_HISTORY_HOURS - 1)
    log(f"[1/4] Fetching history from the {client.source.upper()} API: {start} -> {end}")
    records = client.get_range(start, end)
    log(f"      received {len(records)} records")

    # 2. Preprocess
    log("[2/4] Preprocessing (Task 1 cleaning + lag / rolling-mean features)")
    history, report = clean_records(records, max_gap_fill=max_gap_fill, start=start, end=end)
    if report["duplicates_removed"] or report["missing_hours"] or report["weather_values_filled"]:
        log(f"      cleaned: {report['duplicates_removed']} duplicates removed, "
            f"{len(report['missing_hours'])} missing hours interpolated, "
            f"{report['weather_values_filled']} weather values filled")
    target_time, features = build_next_hour_features(history)

    # 3. Load model
    log(f"[3/4] Loading model: {model_path.name}")
    bundle = load_bundle(model_path)

    # 4. Predict (clipped at 0 like Task 1, since rentals can't be negative)
    prediction = float(np.clip(bundle["model"].predict(features)[0], 0, None))
    log(f"[4/4] Forecast for {target_time:%Y-%m-%d %H:%M}: "
        f"{prediction:.0f} bikes rented")

    result = {
        "source": client.source,
        "forecast_timestamp": str(target_time),
        "predicted_rented_bike_count": round(prediction, 2),
        "history_window": {"start": report["history_start"], "end": report["history_end"]},
        "preprocessing_report": report,
        "features": {k: round(float(v), 4) for k, v in features.iloc[0].items()},
        "model": {
            "file": model_path.name,
            "hyperparameters": bundle.get("hyperparameters"),
            "test_mae": (bundle.get("metrics") or {}).get("test_mae"),
        },
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    # In backtest mode, look up the real value so the forecast can be checked.
    if at is not None:
        actual = client.get_range(at, at)
        if actual:
            value = actual[0]["rented_bike_count"]
            result["actual_rented_bike_count"] = value
            result["absolute_error"] = round(abs(prediction - value), 2)
            log(f"      actual: {value}  |  absolute error: {result['absolute_error']:.0f}")
    return result


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", choices=list(SOURCES), default="sql",
                        help="which database API to read from (default: sql)")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--at", type=datetime.fromisoformat,
                        help="hour to forecast, e.g. '2018-11-30 18:00' (default: hour after latest record)")
    parser.add_argument("--max-gap-fill", type=int, default=3,
                        help="max missing hours to interpolate before refusing (default: 3)")
    parser.add_argument("--output", type=Path,
                        help="where to save the JSON result (default: outputs/predictions/)")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    client = BikeApiClient(base_url=args.base_url, source=args.source)
    try:
        result = run_forecast(client, args.model, at=args.at, max_gap_fill=args.max_gap_fill)
    except (ApiError, PreprocessingError, FileNotFoundError, ValueError) as exc:
        print(f"\nForecast failed: {exc}", file=sys.stderr)
        return 1
    finally:
        client.close()

    out = args.output or DEFAULT_OUTPUT_DIR / (
        f"forecast_{args.source}_{result['forecast_timestamp'].replace(':', '').replace(' ', '_')}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nSaved result to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
