import pandas as pd

from cement_forecast.features import add_calendar_features, add_lag_features, make_supervised_monthly_dataset


def test_add_calendar_features_monthly():
    df = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-02-01"])})
    out = add_calendar_features(df)
    assert list(out["month"]) == [1, 2]
    assert list(out["quarter"]) == [1, 1]
    assert "month_sin" in out.columns
    assert "month_cos" in out.columns


def test_add_lag_features():
    df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=4, freq="MS"), "y": [1, 2, 3, 4]})
    out = add_lag_features(df, columns=["y"], lags=[1, 2])
    assert pd.isna(out.loc[0, "y_lag_1"])
    assert out.loc[2, "y_lag_1"] == 2
    assert out.loc[2, "y_lag_2"] == 1


def test_make_supervised_monthly_dataset_drops_initial_missing_lags():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=24, freq="MS"),
            "target": range(24),
            "x": range(100, 124),
        }
    )
    out = make_supervised_monthly_dataset(
        df,
        target_col="target",
        predictor_cols=["x"],
        lags=[1, 12],
        rolling_windows=[3],
    )
    assert not out.isna().any().any()
    assert "target_lag_12" in out.columns
    assert "x_lag_12" in out.columns
    assert "target_roll_mean_3" in out.columns
