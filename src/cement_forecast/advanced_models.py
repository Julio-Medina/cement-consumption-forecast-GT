from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

try:
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import ElasticNet, Ridge
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
except ImportError as exc:  # pragma: no cover - handled at runtime with a clear message
    raise ImportError(
        "Advanced forecasting models require scikit-learn. "
        "Install project dependencies with `pip install -r requirements.txt`."
    ) from exc


DEFAULT_LAGS = (1, 2, 3, 6, 12)
DEFAULT_ROLLING_WINDOWS = (3, 6, 12)


@dataclass(frozen=True)
class SupervisedForecastData:
    """Container for leakage-aware supervised forecasting features."""

    dates: pd.Series
    X: pd.DataFrame
    y: pd.Series


def _as_float_series(values: pd.Series) -> pd.Series:
    return pd.to_numeric(values, errors="coerce").astype("float64")


def forecast_metrics(y_true: Iterable[float], y_pred: Iterable[float]) -> dict[str, float]:
    """Compute standard forecast metrics."""
    actual = pd.Series(y_true, dtype="float64").reset_index(drop=True)
    pred = pd.Series(y_pred, dtype="float64").reset_index(drop=True)

    error = actual - pred
    abs_error = error.abs()

    mae = float(abs_error.mean())
    rmse = float(np.sqrt(np.mean(np.square(error))))

    nonzero_actual = actual.abs() > 1e-12
    mape = (
        float((abs_error[nonzero_actual] / actual[nonzero_actual].abs()).mean() * 100)
        if nonzero_actual.any()
        else float("nan")
    )

    denominator = actual.abs() + pred.abs()
    nonzero_denom = denominator > 1e-12
    smape = (
        float((2 * abs_error[nonzero_denom] / denominator[nonzero_denom]).mean() * 100)
        if nonzero_denom.any()
        else float("nan")
    )

    return {"mae": mae, "rmse": rmse, "mape": mape, "smape": smape}


def create_supervised_forecast_frame(
    df: pd.DataFrame,
    *,
    target: str,
    lags: Iterable[int] = DEFAULT_LAGS,
    rolling_windows: Iterable[int] = DEFAULT_ROLLING_WINDOWS,
    exogenous_columns: Iterable[str] | None = None,
    include_calendar: bool = True,
) -> SupervisedForecastData:
    """Create a leakage-aware supervised ML table from a monthly time series.

    The target lags and rolling statistics are shifted so the model never sees
    the current target value as a feature. Optional exogenous variables are also
    shifted by one month, which keeps the default setup conservative: it only
    uses information that would have been available before the forecast month.
    """
    if "date" not in df.columns:
        raise ValueError("Input dataframe must contain a 'date' column.")
    if target not in df.columns:
        raise ValueError(f"Target column {target!r} was not found.")

    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values("date").reset_index(drop=True)
    data[target] = _as_float_series(data[target])

    features = pd.DataFrame(index=data.index)

    if include_calendar:
        month = data["date"].dt.month.astype(float)
        features["month_sin"] = np.sin(2 * np.pi * month / 12)
        features["month_cos"] = np.cos(2 * np.pi * month / 12)

    for lag in sorted(set(int(lag) for lag in lags)):
        if lag <= 0:
            raise ValueError("All lags must be positive integers.")
        features[f"{target}_lag_{lag}"] = data[target].shift(lag)

    shifted_target = data[target].shift(1)
    for window in sorted(set(int(window) for window in rolling_windows)):
        if window <= 1:
            raise ValueError("Rolling windows must be greater than 1.")
        features[f"{target}_roll_mean_{window}"] = shifted_target.rolling(window).mean()
        features[f"{target}_roll_std_{window}"] = shifted_target.rolling(window).std()

    if exogenous_columns:
        for column in exogenous_columns:
            if column == target or column == "date" or column not in data.columns:
                continue
            values = _as_float_series(data[column])
            features[f"{column}_lag_1"] = values.shift(1)

    supervised = pd.concat(
        [data[["date", target]].rename(columns={target: "__target__"}), features],
        axis=1,
    )
    supervised = supervised.dropna().reset_index(drop=True)

    if supervised.empty:
        raise ValueError(
            "No supervised rows remain after lag/rolling feature generation. "
            "Use a longer series or smaller lag/rolling windows."
        )

    X = supervised.drop(columns=["date", "__target__"])
    y = supervised["__target__"]
    dates = supervised["date"]

    return SupervisedForecastData(dates=dates, X=X, y=y)


def candidate_ml_models(random_state: int = 42) -> dict[str, object]:
    """Return deterministic baseline ML models for tabular forecasting."""
    return {
        "ridge_lagged": Pipeline(
            steps=[
                ("scale", StandardScaler()),
                ("model", Ridge(alpha=1.0)),
            ]
        ),
        "elasticnet_lagged": Pipeline(
            steps=[
                ("scale", StandardScaler()),
                ("model", ElasticNet(alpha=0.02, l1_ratio=0.20, max_iter=20_000, random_state=random_state)),
            ]
        ),
        "random_forest_lagged": RandomForestRegressor(
            n_estimators=250,
            max_depth=6,
            min_samples_leaf=3,
            random_state=random_state,
        ),
        "gradient_boosting_lagged": GradientBoostingRegressor(
            n_estimators=150,
            learning_rate=0.05,
            max_depth=2,
            random_state=random_state,
        ),
    }


def train_holdout_ml_models(
    df: pd.DataFrame,
    *,
    target: str,
    test_size: int = 12,
    lags: Iterable[int] = DEFAULT_LAGS,
    rolling_windows: Iterable[int] = DEFAULT_ROLLING_WINDOWS,
    exogenous_columns: Iterable[str] | None = None,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, SupervisedForecastData]:
    """Train lagged ML forecasters and evaluate on the latest holdout months."""
    supervised = create_supervised_forecast_frame(
        df,
        target=target,
        lags=lags,
        rolling_windows=rolling_windows,
        exogenous_columns=exogenous_columns,
    )

    if len(supervised.y) <= test_size:
        raise ValueError(
            f"Not enough supervised rows ({len(supervised.y)}) for test_size={test_size}."
        )

    split_at = len(supervised.y) - test_size
    X_train = supervised.X.iloc[:split_at]
    y_train = supervised.y.iloc[:split_at]
    X_test = supervised.X.iloc[split_at:]
    y_test = supervised.y.iloc[split_at:]
    test_dates = supervised.dates.iloc[split_at:]

    metric_rows: list[dict[str, float | str]] = []
    prediction_rows: list[pd.DataFrame] = []

    for name, model in candidate_ml_models(random_state=random_state).items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        metrics = forecast_metrics(y_test, pred)
        metric_rows.append({"model": name, **metrics})
        prediction_rows.append(
            pd.DataFrame(
                {
                    "date": test_dates.to_numpy(),
                    "target": target,
                    "model": name,
                    "actual": y_test.to_numpy(),
                    "prediction": pred,
                }
            )
        )

    comparison = pd.DataFrame(metric_rows).sort_values("rmse").reset_index(drop=True)
    predictions = pd.concat(prediction_rows, ignore_index=True)

    return comparison, predictions, supervised
