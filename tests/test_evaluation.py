import math

import pandas as pd
import pytest

from cement_forecast.evaluation import mae, mape, regression_report, rmse, smape, temporal_train_test_split


def test_regression_metrics_basic():
    y_true = [100, 200, 300]
    y_pred = [110, 190, 330]
    assert mae(y_true, y_pred) == pytest.approx(16.6666667)
    assert rmse(y_true, y_pred) == pytest.approx(math.sqrt((100 + 100 + 900) / 3))
    assert mape(y_true, y_pred) == pytest.approx(((0.1 + 0.05 + 0.1) / 3) * 100)
    assert smape(y_true, y_pred) > 0


def test_regression_report_has_expected_keys():
    report = regression_report([1, 2, 3], [1, 2, 4])
    assert set(report) == {"mae", "rmse", "mape", "smape"}


def test_temporal_train_test_split_uses_last_rows_as_test():
    df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=6, freq="MS"), "y": range(6)})
    train, test = temporal_train_test_split(df, test_size=2)
    assert len(train) == 4
    assert len(test) == 2
    assert list(test["y"]) == [4, 5]


def test_temporal_train_test_split_rejects_bad_size():
    df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=3, freq="MS"), "y": range(3)})
    with pytest.raises(ValueError):
        temporal_train_test_split(df, test_size=3)
