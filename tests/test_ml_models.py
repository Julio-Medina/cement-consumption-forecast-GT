from __future__ import annotations

import numpy as np
import pandas as pd

from cement_forecast.ml_models import (
    candidate_predictor_columns,
    evaluate_holdout_models,
    prepare_supervised_features,
)


def make_monthly_frame(n: int = 48) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=n, freq="MS")
    trend = np.linspace(0, 1, n)
    return pd.DataFrame(
        {
            "date": dates,
            "cement_demand_proxy": trend + np.sin(np.arange(n) / 3),
            "cement_demand_proxy_source_count": 3,
            "indicator_a": trend * 2,
            "indicator_b": np.cos(np.arange(n) / 4),
        }
    )


def test_candidate_predictor_columns_excludes_target_and_source_count():
    df = make_monthly_frame()
    cols = candidate_predictor_columns(df, target_col="cement_demand_proxy")
    assert "indicator_a" in cols
    assert "cement_demand_proxy" not in cols
    assert "cement_demand_proxy_source_count" not in cols


def test_prepare_supervised_features_uses_lagged_features_not_raw_predictors():
    df = make_monthly_frame()
    supervised, feature_cols = prepare_supervised_features(
        df,
        target_col="cement_demand_proxy",
        lags=[1, 2],
        rolling_windows=[3],
    )
    assert len(supervised) > 0
    assert "indicator_a" not in feature_cols
    assert "indicator_a_lag_1" in feature_cols
    assert "cement_demand_proxy_lag_1" in feature_cols
    assert "cement_demand_proxy_roll_mean_3" in feature_cols


def test_evaluate_holdout_models_returns_metrics_and_predictions():
    df = make_monthly_frame(n=60)
    supervised, feature_cols = prepare_supervised_features(df, target_col="cement_demand_proxy")
    results, predictions = evaluate_holdout_models(
        supervised,
        feature_cols=feature_cols,
        target_col="cement_demand_proxy",
        test_size=6,
    )
    assert set(results["model"]) == {"ridge", "random_forest", "gradient_boosting"}
    assert {"mae", "rmse", "mape", "smape"}.issubset(results.columns)
    assert len(predictions) == 6
    assert "pred_ridge" in predictions.columns
