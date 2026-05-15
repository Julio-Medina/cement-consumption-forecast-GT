from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from cement_forecast.evaluation import regression_report, temporal_train_test_split
from cement_forecast.features import add_calendar_features, add_lag_features, add_rolling_features


DEFAULT_LAGS = [1, 2, 3, 6, 12]
DEFAULT_ROLLING_WINDOWS = [3, 6, 12]


def candidate_predictor_columns(
    df: pd.DataFrame,
    target_col: str,
    date_col: str = "date",
    min_non_missing_ratio: float = 0.5,
) -> list[str]:
    """Return numeric predictor columns that are safe to lag for forecasting.

    Very sparse columns are excluded by default because they add little information
    and can make the first ML iteration harder to interpret.
    """
    blocked = {date_col, target_col, f"{target_col}_source_count"}
    numeric_cols = df.select_dtypes(include=["number"]).columns
    cols: list[str] = []
    for col in numeric_cols:
        if col in blocked:
            continue
        if df[col].notna().mean() >= min_non_missing_ratio:
            cols.append(col)
    return cols


def prepare_supervised_features(
    df: pd.DataFrame,
    target_col: str,
    predictor_cols: list[str] | None = None,
    lags: list[int] | None = None,
    rolling_windows: list[int] | None = None,
    date_col: str = "date",
) -> tuple[pd.DataFrame, list[str]]:
    """Create lagged, leakage-aware features for one-step-ahead monthly forecasting.

    The returned feature list excludes contemporaneous raw indicators. It keeps
    deterministic calendar features and lagged/rolling features, so the model does
    not learn from same-month values that would not be available at forecast time.
    Sparse exogenous lag features may contain missing values; model pipelines impute
    them during training.
    """
    if predictor_cols is None:
        predictor_cols = candidate_predictor_columns(df, target_col=target_col, date_col=date_col)
    if lags is None:
        lags = DEFAULT_LAGS
    if rolling_windows is None:
        rolling_windows = DEFAULT_ROLLING_WINDOWS

    clean = df.copy()
    clean[date_col] = pd.to_datetime(clean[date_col])
    clean = clean.sort_values(date_col).dropna(subset=[target_col]).reset_index(drop=True)

    supervised = add_calendar_features(clean, date_col=date_col)
    supervised = add_lag_features(supervised, [target_col, *predictor_cols], lags=lags, sort_col=date_col)
    supervised = add_rolling_features(supervised, [target_col], windows=rolling_windows, sort_col=date_col)

    calendar_cols = ["year", "month", "quarter", "month_sin", "month_cos"]
    target_feature_cols = [
        col
        for col in supervised.columns
        if col.startswith(f"{target_col}_lag_") or col.startswith(f"{target_col}_roll_")
    ]
    predictor_lag_cols = [
        col
        for col in supervised.columns
        if any(col.startswith(f"{predictor}_lag_") for predictor in predictor_cols)
    ]
    feature_cols = calendar_cols + target_feature_cols + predictor_lag_cols

    # Require enough target history for autoregressive features. Exogenous lag
    # features are allowed to be missing and are imputed inside the model pipelines.
    required_cols = [target_col, *target_feature_cols]
    supervised = supervised.dropna(subset=required_cols).reset_index(drop=True)
    return supervised, feature_cols


def _imputed_tree_pipeline(model: object) -> Pipeline:
    return Pipeline(steps=[("imputer", SimpleImputer(strategy="median")), ("model", model)])


def build_regressors(random_state: int = 42) -> dict[str, object]:
    """Return a small portfolio of robust tabular forecasting models."""
    return {
        "ridge": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", RidgeCV(alphas=np.logspace(-3, 3, 13))),
            ]
        ),
        "random_forest": _imputed_tree_pipeline(
            RandomForestRegressor(
                n_estimators=80,
                min_samples_leaf=3,
                random_state=random_state,
                n_jobs=1,
            )
        ),
        "gradient_boosting": _imputed_tree_pipeline(
            GradientBoostingRegressor(
                n_estimators=120,
                learning_rate=0.04,
                max_depth=2,
                random_state=random_state,
            )
        ),
    }


def evaluate_holdout_models(
    supervised: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    test_size: int = 12,
    date_col: str = "date",
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Train ML regressors on a temporal split and return metrics and predictions."""
    if len(supervised) <= test_size:
        raise ValueError(
            f"Not enough supervised observations ({len(supervised)}) for test_size={test_size}."
        )
    if not feature_cols:
        raise ValueError("feature_cols cannot be empty")

    train, test = temporal_train_test_split(supervised, test_size=test_size, date_col=date_col)
    x_train = train[feature_cols]
    y_train = train[target_col]
    x_test = test[feature_cols]
    y_test = test[target_col]

    metrics_rows: list[dict[str, float | str]] = []
    pred_frame = test[[date_col, target_col]].copy()

    for name, model in build_regressors(random_state=random_state).items():
        model.fit(x_train, y_train)
        preds = model.predict(x_test)
        pred_frame[f"pred_{name}"] = preds
        metrics_rows.append({"model": name, **regression_report(y_test, preds)})

    results = pd.DataFrame(metrics_rows).sort_values("rmse").reset_index(drop=True)
    return results, pred_frame
