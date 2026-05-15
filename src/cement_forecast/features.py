from __future__ import annotations

import numpy as np
import pandas as pd


def add_calendar_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Add deterministic calendar features for monthly forecasting."""
    out = df.copy()
    dates = pd.to_datetime(out[date_col])
    calendar = pd.DataFrame(
        {
            "year": dates.dt.year,
            "month": dates.dt.month,
            "quarter": dates.dt.quarter,
            "month_sin": np.sin(2 * np.pi * dates.dt.month / 12),
            "month_cos": np.cos(2 * np.pi * dates.dt.month / 12),
        },
        index=out.index,
    )
    return pd.concat([out, calendar], axis=1)


def add_lag_features(
    df: pd.DataFrame,
    columns: list[str],
    lags: list[int],
    sort_col: str = "date",
) -> pd.DataFrame:
    """Add lagged versions of selected columns."""
    out = df.sort_values(sort_col).copy()
    lagged = {
        f"{column}_lag_{lag}": out[column].shift(lag)
        for column in columns
        for lag in lags
    }
    if not lagged:
        return out
    return pd.concat([out, pd.DataFrame(lagged, index=out.index)], axis=1)


def add_rolling_features(
    df: pd.DataFrame,
    columns: list[str],
    windows: list[int],
    sort_col: str = "date",
) -> pd.DataFrame:
    """Add rolling mean and standard-deviation features using only past observations."""
    out = df.sort_values(sort_col).copy()
    rolling = {}
    for column in columns:
        shifted = out[column].shift(1)
        for window in windows:
            rolling[f"{column}_roll_mean_{window}"] = shifted.rolling(window=window).mean()
            rolling[f"{column}_roll_std_{window}"] = shifted.rolling(window=window).std()
    if not rolling:
        return out
    return pd.concat([out, pd.DataFrame(rolling, index=out.index)], axis=1)


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
