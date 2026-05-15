from __future__ import annotations

import numpy as np
import pandas as pd


class NaiveForecaster:
    """Forecast every future point as the last observed value."""

    def fit(self, y: pd.Series | np.ndarray) -> "NaiveForecaster":
        values = np.asarray(y, dtype=float)
        if len(values) == 0:
            raise ValueError("Cannot fit NaiveForecaster on an empty series")
        self.last_value_ = float(values[-1])
        return self

    def predict(self, horizon: int) -> np.ndarray:
        if horizon <= 0:
            raise ValueError("horizon must be positive")
        return np.repeat(self.last_value_, horizon)


class SeasonalNaiveForecaster:
    """Forecast using the value from the same season in the last observed cycle."""

    def __init__(self, season_length: int = 12):
        if season_length <= 0:
            raise ValueError("season_length must be positive")
        self.season_length = season_length

    def fit(self, y: pd.Series | np.ndarray) -> "SeasonalNaiveForecaster":
        values = np.asarray(y, dtype=float)
        if len(values) < self.season_length:
            raise ValueError("Series length must be at least the season length")
        self.last_season_ = values[-self.season_length :]
        return self

    def predict(self, horizon: int) -> np.ndarray:
        if horizon <= 0:
            raise ValueError("horizon must be positive")
        repeats = int(np.ceil(horizon / self.season_length))
        return np.tile(self.last_season_, repeats)[:horizon]


class MovingAverageForecaster:
    """Forecast every future point as the trailing average."""

    def __init__(self, window: int = 3):
        if window <= 0:
            raise ValueError("window must be positive")
        self.window = window

    def fit(self, y: pd.Series | np.ndarray) -> "MovingAverageForecaster":
        values = np.asarray(y, dtype=float)
        if len(values) < self.window:
            raise ValueError("Series length must be at least the moving-average window")
        self.mean_ = float(np.mean(values[-self.window :]))
        return self

    def predict(self, horizon: int) -> np.ndarray:
        if horizon <= 0:
            raise ValueError("horizon must be positive")
        return np.repeat(self.mean_, horizon)
