import pandas as pd
import pytest

from cement_forecast.targets import available_targets, default_target, target_label, validate_target_column


def test_available_targets_prefers_business_targets_over_proxy():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=3, freq="MS"),
            "cement_demand_proxy": [0.1, 0.2, 0.3],
            "construction_area_m2": [100.0, 200.0, 300.0],
        }
    )
    targets = available_targets(df)
    assert [target.column for target in targets][:2] == ["construction_area_m2", "cement_demand_proxy"]
    assert default_target(df) == "construction_area_m2"


def test_target_label_uses_catalog_then_fallback():
    assert target_label("construction_area_m2") == "Construction area"
    assert target_label("custom_metric") == "Custom Metric"


def test_validate_target_column_rejects_missing_or_sparse_target():
    df = pd.DataFrame({"date": ["2024-01-01", "2024-02-01"], "x": [1.0, None]})
    with pytest.raises(ValueError, match="missing"):
        validate_target_column(df, "y")
    with pytest.raises(ValueError, match="only 1"):
        validate_target_column(df, "x", min_observations=2)
