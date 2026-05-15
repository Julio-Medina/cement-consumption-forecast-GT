from __future__ import annotations

import pandas as pd


def add_calendar_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Add deterministic calendar features for monthly forecasting."""
    out = df.copy()
    dates = pd.to_datetime(out[date_col])
    out["year"] = dates.dt.year
    out["month"] = dates.dt.month
    out["quarter"] = dates.dt.quarter
    out["month_sin"] = __import__("numpy").sin(2 * __import__("numpy").pi * out["month"] / 12)
    out["month_cos"] = __import__("numpy").cos(2 * __import__("numpy").pi * out["month"] / 12)
    return out


def add_lag_features(
    df: pd.DataFrame,
    columns: list[str],
    lags: list[int],
    sort_col: str = "date",
) -> pd.DataFrame:
    """Add lagged versions of selected columns."""
    out = df.sort_values(sort_col).copy()
    for column in columns:
        for lag in lags:
            out[f"{column}_lag_{lag}"] = out[column].shift(lag)
    return out


def add_rolling_features(
    df: pd.DataFrame,
    columns: list[str],
    windows: list[int],
    sort_col: str = "date",
) -> pd.DataFrame:
    """Add rolling mean features using only past observations."""
    out = df.sort_values(sort_col).copy()
    for column in columns:
        shifted = out[column].shift(1)
        for window in windows:
            out[f"{column}_roll_mean_{window}"] = shifted.rolling(window=window).mean()
            out[f"{column}_roll_std_{window}"] = shifted.rolling(window=window).std()
    return out


def make_supervised_monthly_dataset(
    df: pd.DataFrame,
    target_col: str,
    predictor_cols: list[str] | None = None,
    lags: list[int] | None = None,
    rolling_windows: list[int] | None = None,
) -> pd.DataFrame:
    """Create a simple supervised-learning table for monthly time-series forecasting."""
    if lags is None:
        lags = [1, 2, 3, 6, 12]
    if rolling_windows is None:
        rolling_windows = [3, 6, 12]
    if predictor_cols is None:
        predictor_cols = []

    out = add_calendar_features(df)
    feature_base_cols = [target_col, *predictor_cols]
    out = add_lag_features(out, feature_base_cols, lags=lags)
    out = add_rolling_features(out, [target_col], windows=rolling_windows)
    return out.dropna().reset_index(drop=True)
