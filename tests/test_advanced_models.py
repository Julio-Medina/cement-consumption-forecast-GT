from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cement_forecast.advanced_models import (
    create_supervised_forecast_frame,
    forecast_metrics,
    train_holdout_ml_models,
)


def make_monthly_data(periods: int = 72) -> pd.DataFrame:
    dates = pd.date_range("2018-01-01", periods=periods, freq="MS")
    t = np.arange(periods, dtype=float)
    seasonal = 10 * np.sin(2 * np.pi * t / 12)
    return pd.DataFrame(
        {
            "date": dates,
            "imae_construction_index": 100 + 0.8 * t + seasonal,
            "ipmc_cement_related_index": 95 + 0.4 * t,
        }
    )


def test_create_supervised_forecast_frame_uses_shifted_features():
    df = make_monthly_data()
    supervised = create_supervised_forecast_frame(
        df,
        target="imae_construction_index",
        lags=(1, 12),
        rolling_windows=(3,),
    )

    assert "imae_construction_index_lag_1" in supervised.X.columns
    assert "imae_construction_index_lag_12" in supervised.X.columns
    assert "imae_construction_index_roll_mean_3" in supervised.X.columns
    assert len(supervised.X) < len(df)
    assert supervised.X.isna().sum().sum() == 0


def test_forecast_metrics_returns_expected_keys():
    metrics = forecast_metrics([100, 110, 120], [101, 108, 119])
    assert set(metrics) == {"mae", "rmse", "mape", "smape"}
    assert metrics["mae"] > 0
    assert metrics["rmse"] > 0


def test_train_holdout_ml_models_returns_sorted_comparison_and_predictions():
    df = make_monthly_data()
    comparison, predictions, supervised = train_holdout_ml_models(
        df,
        target="imae_construction_index",
        test_size=12,
        lags=(1, 2, 3, 6, 12),
        rolling_windows=(3, 6),
    )

    assert not comparison.empty
    assert comparison["rmse"].is_monotonic_increasing
    assert {"model", "mae", "rmse", "mape", "smape"}.issubset(comparison.columns)
    assert not predictions.empty
    assert predictions["model"].nunique() == len(comparison)
    assert len(supervised.y) > 12


def test_train_holdout_ml_models_rejects_too_short_series():
    df = make_monthly_data(periods=16)
    with pytest.raises(ValueError):
        train_holdout_ml_models(
            df,
            target="imae_construction_index",
            test_size=12,
            lags=(1, 2, 3, 6, 12),
            rolling_windows=(3,),
        )
