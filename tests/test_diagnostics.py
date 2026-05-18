from __future__ import annotations

from pathlib import Path
import importlib.util

import pandas as pd

from cement_forecast.diagnostics import (
    best_model_row,
    compute_lag_correlations,
    filter_predictions_for_model,
    percentage_improvement,
)


def test_percentage_improvement_for_lower_is_better_metric():
    assert round(percentage_improvement(10.0, 7.5), 2) == 25.0


def test_best_model_row_uses_lowest_rmse():
    comparison = pd.DataFrame(
        {
            "model": ["a", "b", "c"],
            "rmse": [4.0, 2.0, 3.0],
            "mae": [3.0, 1.5, 2.5],
            "status": ["trained", "trained", "skipped"],
        }
    )

    best = best_model_row(comparison)

    assert best["model"] == "b"


def test_filter_predictions_for_model_sorts_dates():
    predictions = pd.DataFrame(
        {
            "date": ["2024-02-01", "2024-01-01", "2024-01-01"],
            "model": ["ridge", "ridge", "elasticnet"],
            "actual": [2.0, 1.0, 1.0],
            "prediction": [2.1, 1.1, 0.9],
        }
    )

    filtered = filter_predictions_for_model(predictions, "ridge")

    assert list(filtered["date"].dt.strftime("%Y-%m-%d")) == [
        "2024-01-01",
        "2024-02-01",
    ]


def test_compute_lag_correlations_returns_leakage_safe_lags():
    dates = pd.date_range("2020-01-01", periods=40, freq="MS")
    x = pd.Series(range(40), dtype="float64")
    df = pd.DataFrame(
        {
            "date": dates,
            "target": x.shift(1).fillna(0),
            "feature": x,
        }
    )

    correlations = compute_lag_correlations(
        df,
        target="target",
        max_lag=3,
        min_observations=10,
    )

    assert not correlations.empty
    assert set(correlations["lag"]).issubset({1, 2, 3})
    assert "feature" in set(correlations["feature"])


def test_build_report_contains_key_sections(tmp_path: Path):
    script_path = Path("scripts/make_forecast_diagnostics.py")
    spec = importlib.util.spec_from_file_location(
        "make_forecast_diagnostics",
        script_path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    comparison = pd.DataFrame(
        {
            "model": ["elasticnet_lagged"],
            "mae": [5.0],
            "rmse": [7.0],
            "mape": [3.0],
            "smape": [3.2],
        }
    )

    correlations = pd.DataFrame(
        columns=[
            "feature",
            "lag",
            "correlation",
            "abs_correlation",
            "observations",
        ]
    )

    report = module.build_report(
        data_path=Path("data/processed/monthly_panel_2019_2026.csv"),
        target="imae_construction_index",
        comparison=comparison,
        correlations=correlations,
        best_model="elasticnet_lagged",
        baseline_rmse=11.0,
        baseline_mae=10.0,
        figure_paths={},
    )

    assert "# Forecast Diagnostics and Model Interpretation" in report
    assert "elasticnet_lagged" in report
    assert "RMSE improvement" in report
