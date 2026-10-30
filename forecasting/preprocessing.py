"""
Preprocessing and feature engineering shared by training and prediction.

These functions copy the Task 1 notebook (section C, ``make_forecasting_features``)
exactly. Training and prediction both call ``make_forecasting_features``, so the
lag, rolling-window and calendar features are built by the same code at both
stages. That keeps the model from receiving features in a different format at
prediction time than it saw during training.

Forecast definition (from Task 1): predict ``rented_bike_count`` at hour t using
only information known at hour t-1. That means calendar features for hour t,
past demand (lags and rolling statistics), and the previous hour's weather.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TARGET = "rented_bike_count"

# Same order as Task 1. The model expects its columns in exactly this order.
FEATURE_COLUMNS = [
    "hour", "day_of_week", "month", "is_weekend", "hour_sin", "hour_cos",
    "lag_1h", "lag_24h", "lag_168h",
    "rolling_mean_24h", "rolling_mean_168h", "rolling_std_24h",
    "temperature_lag_1h", "humidity_lag_1h", "rainfall_lag_1h",
]

# The longest lag (one week) decides how much history a forecast needs.
REQUIRED_HISTORY_HOURS = 168

# Fields the feature formulas read. The API returns more, which is fine.
REQUIRED_FIELDS = [
    "timestamp", TARGET, "temperature_c", "humidity_pct", "rainfall_mm",
]
NUMERIC_FIELDS = [
    TARGET, "temperature_c", "humidity_pct", "wind_speed_ms", "visibility_10m",
    "dew_point_c", "solar_radiation", "rainfall_mm", "snowfall_cm",
]

# Column names in the raw Kaggle CSV, mapped to the names used by the API and
# databases (Task 2/3). The notebook calls solar radiation
# "solar_radiation_mj_m2"; it is not a model feature, so the mismatch does not
# matter here.
CSV_COLUMN_MAP = {
    "Date": "date", "Rented Bike Count": TARGET, "Hour": "hour",
    "Temperature(°C)": "temperature_c", "Humidity(%)": "humidity_pct",
    "Wind speed (m/s)": "wind_speed_ms", "Visibility (10m)": "visibility_10m",
    "Dew point temperature(°C)": "dew_point_c",
    "Solar Radiation (MJ/m2)": "solar_radiation",
    "Rainfall(mm)": "rainfall_mm", "Snowfall (cm)": "snowfall_cm",
    "Seasons": "season", "Holiday": "holiday", "Functioning Day": "functioning_day",
}


class PreprocessingError(ValueError):
    """Raised when the fetched data cannot be turned into a valid model input."""


def load_raw_csv(path) -> pd.DataFrame:
    """Read the Kaggle CSV the same way as Task 1 (encoding fallback, rename, timestamp)."""
    raw = None
    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        try:
            raw = pd.read_csv(path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    if raw is None:
        raise PreprocessingError(f"Could not decode {path}")

    missing = sorted(set(CSV_COLUMN_MAP) - set(raw.columns))
    if missing:
        raise PreprocessingError(f"CSV is missing required columns: {missing}")

    df = raw.rename(columns=CSV_COLUMN_MAP)
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
    df["hour"] = pd.to_numeric(df["hour"]).astype(int)
    df["timestamp"] = df["date"] + pd.to_timedelta(df["hour"], unit="h")
    return df.drop(columns=["date", "hour"]).sort_values("timestamp").reset_index(drop=True)


def clean_records(records, max_gap_fill: int = 3, start=None, end=None) -> tuple[pd.DataFrame, dict]:
    """
    Turn raw API records (a list of dicts or a DataFrame) into a clean hourly series.

    Steps, following the Task 1 data-quality checks:
      1. Check that the required fields are present.
      2. Parse timestamps (dropping any timezone) and coerce numeric fields.
      3. Reject negative or missing target values.
      4. Remove duplicate timestamps, keeping the most recent write.
      5. Sort the rows and put them on a regular hourly grid.
      6. Fill missing hours. The original dataset had none, so Task 1 did no
         imputation. Through the API, CRUD deletes can leave gaps. Up to
         ``max_gap_fill`` missing hours are filled by time interpolation
         (numeric columns) and forward fill (categorical columns). More gaps
         than that raise an error instead of letting the model see invented
         history.

    ``start``/``end`` (optional) give the window that was requested. With them,
    hours missing at the very start or end of the window are caught too, not
    only gaps between records.

    Returns the cleaned frame and a report dict describing what was changed.
    """
    df = pd.DataFrame(records).copy()
    if df.empty:
        raise PreprocessingError("No records were returned by the API.")

    missing = [c for c in REQUIRED_FIELDS if c not in df.columns]
    if missing:
        raise PreprocessingError(f"Records are missing required fields: {missing}")

    report = {"records_received": int(len(df))}

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if getattr(df["timestamp"].dt, "tz", None) is not None:
        df["timestamp"] = df["timestamp"].dt.tz_localize(None)
    bad_ts = int(df["timestamp"].isna().sum())
    if bad_ts:
        raise PreprocessingError(f"{bad_ts} record(s) have an unparseable timestamp.")

    for col in NUMERIC_FIELDS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if df[TARGET].isna().any() or (df[TARGET] < 0).any():
        raise PreprocessingError("Target values must be present and non-negative.")

    before = len(df)
    df = df.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    report["duplicates_removed"] = int(before - len(df))

    df = df.set_index("timestamp")
    grid_start = pd.Timestamp(start) if start is not None else df.index.min()
    grid_end = pd.Timestamp(end) if end is not None else df.index.max()
    df = df.reindex(pd.date_range(grid_start, grid_end, freq="h", name="timestamp"))
    missing_hours = df.index[df[TARGET].isna()]
    report["missing_hours"] = [str(t) for t in missing_hours]
    if len(missing_hours) > max_gap_fill:
        raise PreprocessingError(
            f"{len(missing_hours)} hourly records are missing from the history "
            f"(limit {max_gap_fill}). Lag features would be unreliable."
        )
    if len(missing_hours):
        numeric = [c for c in NUMERIC_FIELDS if c in df.columns]
        df[numeric] = df[numeric].interpolate(method="time", limit_direction="both")
        df = df.ffill().bfill()

    # Weather gaps inside an existing record (the columns are nullable in the DB).
    weather_nulls = int(df[["temperature_c", "humidity_pct", "rainfall_mm"]].isna().sum().sum())
    if weather_nulls:
        cols = ["temperature_c", "humidity_pct", "rainfall_mm"]
        df[cols] = df[cols].interpolate(method="time", limit_direction="both")
    report["weather_values_filled"] = weather_nulls

    df = df.reset_index()
    report["clean_rows"] = int(len(df))
    report["history_start"] = str(df["timestamp"].iloc[0])
    report["history_end"] = str(df["timestamp"].iloc[-1])
    return df, report


def make_forecasting_features(data: pd.DataFrame) -> pd.DataFrame:
    """Build one-hour-ahead features with no current-target or future-weather leakage.

    Copied unchanged from Task 1, section C.
    """
    indexed = data.set_index("timestamp").sort_index().asfreq("h").copy()
    indexed["hour"] = indexed.index.hour
    indexed["day_of_week"] = indexed.index.dayofweek
    indexed["month"] = indexed.index.month
    indexed["is_weekend"] = (indexed.index.dayofweek >= 5).astype(int)
    indexed["hour_sin"] = np.sin(2 * np.pi * indexed["hour"] / 24)
    indexed["hour_cos"] = np.cos(2 * np.pi * indexed["hour"] / 24)
    counts = indexed[TARGET]
    indexed["lag_1h"] = counts.shift(1)
    indexed["lag_24h"] = counts.shift(24)
    indexed["lag_168h"] = counts.shift(168)
    indexed["rolling_mean_24h"] = counts.shift(1).rolling(24, min_periods=24).mean()
    indexed["rolling_mean_168h"] = counts.shift(1).rolling(168, min_periods=168).mean()
    indexed["rolling_std_24h"] = counts.shift(1).rolling(24, min_periods=24).std()
    indexed["temperature_lag_1h"] = indexed["temperature_c"].shift(1)
    indexed["humidity_lag_1h"] = indexed["humidity_pct"].shift(1)
    indexed["rainfall_lag_1h"] = indexed["rainfall_mm"].shift(1)
    return indexed


def build_next_hour_features(history: pd.DataFrame) -> tuple[pd.Timestamp, pd.DataFrame]:
    """
    Make the single feature row for the hour after the last record in ``history``.

    An empty placeholder row is added for the target hour and the result is
    passed through ``make_forecasting_features``, the same function used in
    training. The placeholder's own target and weather values stay NaN, and
    every feature reads only shifted (past) values, so nothing from the
    target hour leaks into the input.
    """
    if len(history) < REQUIRED_HISTORY_HOURS:
        raise PreprocessingError(
            f"Need at least {REQUIRED_HISTORY_HOURS} hourly records, got {len(history)}."
        )
    next_time = history["timestamp"].iloc[-1] + pd.Timedelta(hours=1)
    placeholder = pd.DataFrame({"timestamp": [next_time]})
    extended = pd.concat([history, placeholder], ignore_index=True)

    features = make_forecasting_features(extended)
    row = features.loc[[next_time], FEATURE_COLUMNS]
    if row.isna().any(axis=None):
        bad = row.columns[row.isna().iloc[0]].tolist()
        raise PreprocessingError(f"Could not compute features: {bad}")
    return next_time, row.reset_index(drop=True)
