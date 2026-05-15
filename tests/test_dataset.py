import pandas as pd
import pytest

from cement_forecast.dataset import build_proxy_target, merge_monthly_frames


def test_merge_monthly_frames_outer_join():
    left = pd.DataFrame({"date": ["2024-01-01", "2024-02-01"], "a": [1, 2]})
    right = pd.DataFrame({"date": ["2024-02-01", "2024-03-01"], "b": [10, 20]})

    result = merge_monthly_frames([left, right])

    assert list(result["date"].dt.strftime("%Y-%m-%d")) == [
        "2024-01-01",
        "2024-02-01",
        "2024-03-01",
    ]
    assert result.shape == (3, 3)


def test_build_proxy_target_creates_target_from_candidate_columns():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=4, freq="MS"),
            "ipmc_cement_index": [100, 110, 120, 130],
            "construction_area_m2": [1000, 1050, 1100, 1150],
        }
    )

    result = build_proxy_target(df)

    assert "cement_demand_proxy" in result.columns
    assert result["cement_demand_proxy"].notna().all()


def test_build_proxy_target_raises_without_candidates():
    df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=2, freq="MS"), "x": [1, 2]})
    with pytest.raises(ValueError):
        build_proxy_target(df)
