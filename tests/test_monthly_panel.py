from __future__ import annotations

import pandas as pd
import pytest

from cement_forecast.monthly_panel import (
    build_strict_monthly_panel,
    monthly_index,
    validate_complete_monthly_panel,
)


def test_monthly_index_is_inclusive():
    idx = monthly_index("2019-01-01", "2019-03-01")
    assert [d.strftime("%Y-%m-%d") for d in idx] == [
        "2019-01-01",
        "2019-02-01",
        "2019-03-01",
    ]


def test_build_strict_panel_drops_incomplete_non_required_columns():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2019-01-01", periods=4, freq="MS"),
            "complete_indicator": [1.0, 2.0, 3.0, 4.0],
            "sparse_indicator": [10.0, None, 30.0, 40.0],
        }
    )
    panel, report = build_strict_monthly_panel(df, start="2019-01-01", end="2019-04-01")
    assert panel.columns.tolist() == ["date", "complete_indicator"]
    assert "sparse_indicator" in report.dropped_columns
    assert report.is_complete


def test_build_strict_panel_fails_when_required_column_is_incomplete():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2019-01-01", periods=4, freq="MS"),
            "target": [1.0, 2.0, None, 4.0],
        }
    )
    with pytest.raises(ValueError, match="Required columns are not complete"):
        build_strict_monthly_panel(
            df,
            start="2019-01-01",
            end="2019-04-01",
            required_columns=["target"],
        )


def test_validate_complete_monthly_panel_rejects_missing_month():
    df = pd.DataFrame(
        {
            "date": ["2019-01-01", "2019-03-01"],
            "x": [1, 3],
        }
    )
    with pytest.raises(ValueError, match="expected"):
        validate_complete_monthly_panel(df, start="2019-01-01", end="2019-03-01")
