from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


def load_script_module():
    path = Path("scripts/make_baseline_report.py")
    spec = importlib.util.spec_from_file_location("make_baseline_report", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_monthly_data(periods: int = 36) -> pd.DataFrame:
    dates = pd.date_range("2021-01-01", periods=periods, freq="MS")
    trend = np.linspace(100, 150, periods)
    season = 5 * np.sin(np.arange(periods) * 2 * np.pi / 12)
    return pd.DataFrame(
        {
            "date": dates,
            "imae_construction_index": trend + season,
            "ipmc_cement_related_index": np.linspace(90, 120, periods),
        }
    )


def test_train_baselines_returns_sorted_comparison_and_predictions():
    module = load_script_module()
    df = make_monthly_data()

    train, test, comparison, predictions = module.train_baselines(
        df,
        target="imae_construction_index",
        test_size=6,
    )

    assert len(train) == 30
    assert len(test) == 6
    assert not comparison.empty
    assert comparison.iloc[0]["status"] == "trained"
    assert {"model", "mae", "rmse", "mape", "smape", "status"}.issubset(comparison.columns)
    assert {"date", "target", "model", "actual", "prediction"}.issubset(predictions.columns)
    assert predictions["target"].eq("imae_construction_index").all()


def test_make_markdown_report_contains_key_sections():
    module = load_script_module()
    df = make_monthly_data()
    train, test, comparison, _ = module.train_baselines(
        df,
        target="imae_construction_index",
        test_size=6,
    )

    report = module.make_markdown_report(
        data_path=Path("data/processed/monthly_panel_2019_2026.csv"),
        target="imae_construction_index",
        train=train,
        test=test,
        comparison=comparison,
    )

    assert "# IMAE Construction Baseline Forecasting Results" in report
    assert "## Model comparison" in report
    assert "imae_construction_index" in report
    assert "Best baseline" in report


def test_train_baselines_rejects_too_short_series():
    module = load_script_module()
    df = make_monthly_data(periods=5)

