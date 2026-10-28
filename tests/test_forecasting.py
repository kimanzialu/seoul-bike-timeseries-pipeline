"""Tests for the Task 4 prediction pipeline."""
from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from joblib import load

from forecasting.api_client import BikeApiClient
from forecasting.predict import run_forecast
from forecasting.preprocessing import (FEATURE_COLUMNS, PreprocessingError,
                                       build_next_hour_features, clean_records,
                                       make_forecasting_features)


def test_inference_features_match_training_features(dataset):
    """A feature row built at prediction time must equal the row used in training."""
    training = make_forecasting_features(dataset)
    for target in ["2018-06-15 08:00", "2018-11-30 23:00", "2018-02-03 17:00"]:
        t = pd.Timestamp(target)
        history = dataset[dataset["timestamp"] < t].tail(168).reset_index(drop=True)
        when, row = build_next_hour_features(history)
        assert when == t
        expected = training.loc[[t], FEATURE_COLUMNS].reset_index(drop=True)
        pd.testing.assert_frame_equal(row, expected, check_dtype=False)


@pytest.mark.parametrize("source", ["sql", "mongo"])
def test_end_to_end_next_hour(api, dataset, model_path, source):
    client = BikeApiClient(source=source, client=api)
    result = run_forecast(client, model_path, verbose=False)

    assert result["forecast_timestamp"] == "2018-12-01 00:00:00"
    assert result["preprocessing_report"]["clean_rows"] == 168
    assert result["predicted_rented_bike_count"] >= 0

    # The same prediction the model gives on the notebook's own feature row.
    bundle = load(model_path)
    extended = pd.concat([dataset, pd.DataFrame({"timestamp": [pd.Timestamp("2018-12-01")]})])
    expected_row = make_forecasting_features(extended).loc[["2018-12-01"], FEATURE_COLUMNS]
    expected = float(np.clip(bundle["model"].predict(expected_row)[0], 0, None))
    assert result["predicted_rented_bike_count"] == pytest.approx(expected, abs=0.01)


def test_sql_and_mongo_agree(api, model_path):
    at = datetime(2018, 11, 28, 18)
    sql = run_forecast(BikeApiClient(source="sql", client=api), model_path, at=at, verbose=False)
    mongo = run_forecast(BikeApiClient(source="mongo", client=api), model_path, at=at, verbose=False)
    assert sql["predicted_rented_bike_count"] == mongo["predicted_rented_bike_count"]
    assert sql["actual_rented_bike_count"] == mongo["actual_rented_bike_count"]


def _delete_hours(api, source, hours):
    client = BikeApiClient(source=source, client=api)
    prefix = client.prefix
    for h in hours:
        rec = client.get_range(h, h)[0]
        assert api.delete(f"{prefix}/{rec['id']}").status_code == 204


@pytest.mark.parametrize("source", ["sql", "mongo"])
def test_small_gaps_are_interpolated(api, model_path, source):
    """Records deleted through the CRUD API leave gaps that preprocessing must handle."""
    _delete_hours(api, source, [datetime(2018, 11, 30, 10), datetime(2018, 11, 29, 3)])
    result = run_forecast(BikeApiClient(source=source, client=api), model_path, verbose=False)
    assert len(result["preprocessing_report"]["missing_hours"]) == 2
    assert result["preprocessing_report"]["clean_rows"] == 168


def test_gap_at_window_start_is_detected(api, model_path):
    """A missing first hour must be noticed, not silently shorten the history."""
    _delete_hours(api, "sql", [datetime(2018, 11, 24, 0)])  # first hour of the 168h window
    result = run_forecast(BikeApiClient(source="sql", client=api), model_path, verbose=False)
    assert result["preprocessing_report"]["missing_hours"] == ["2018-11-24 00:00:00"]


def test_too_many_gaps_rejected(api, model_path):
    _delete_hours(api, "sql", [datetime(2018, 11, 30, h) for h in range(5)])
    with pytest.raises(PreprocessingError, match="missing"):
        run_forecast(BikeApiClient(source="sql", client=api), model_path, verbose=False)


def test_duplicates_and_bad_input():
    base = {"temperature_c": 1.0, "humidity_pct": 50, "rainfall_mm": 0.0}
    recs = [{"timestamp": "2018-01-01T00:00:00", "rented_bike_count": 5, **base},
            {"timestamp": "2018-01-01T00:00:00", "rented_bike_count": 7, **base},
            {"timestamp": "2018-01-01T01:00:00", "rented_bike_count": 9, **base}]
    df, report = clean_records(recs)
    assert report["duplicates_removed"] == 1 and df["rented_bike_count"].tolist() == [7, 9]

    with pytest.raises(PreprocessingError):
        clean_records([{"timestamp": "2018-01-01", "rented_bike_count": -1, **base}])
    with pytest.raises(PreprocessingError):
        clean_records([])
    with pytest.raises(PreprocessingError, match="168"):
        build_next_hour_features(df)
