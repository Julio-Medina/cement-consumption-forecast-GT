import numpy as np
import pytest

from cement_forecast.models import MovingAverageForecaster, NaiveForecaster, SeasonalNaiveForecaster


def test_naive_forecaster_repeats_last_value():
    model = NaiveForecaster().fit([1, 2, 5])
    assert np.array_equal(model.predict(3), np.array([5, 5, 5]))


def test_seasonal_naive_repeats_last_season():
    model = SeasonalNaiveForecaster(season_length=3).fit([1, 2, 3, 4, 5, 6])
    assert np.array_equal(model.predict(5), np.array([4, 5, 6, 4, 5]))


def test_moving_average_forecaster_uses_trailing_window():
    model = MovingAverageForecaster(window=3).fit([1, 2, 7, 10])
    assert np.array_equal(model.predict(2), np.array([pytest.approx((2 + 7 + 10) / 3)] * 2))


def test_forecasters_reject_invalid_horizon():
    model = NaiveForecaster().fit([1])
    with pytest.raises(ValueError):
        model.predict(0)
