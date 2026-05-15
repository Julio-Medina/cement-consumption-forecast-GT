from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


import argparse

import pandas as pd

from cement_forecast.config import TARGET_COLUMN
from cement_forecast.evaluation import regression_report, temporal_train_test_split
from cement_forecast.models import MovingAverageForecaster, NaiveForecaster, SeasonalNaiveForecaster


def main() -> None:
    parser = argparse.ArgumentParser(description="Train baseline forecasting models.")
    parser.add_argument("--data", required=True, help="Path to a monthly modeling CSV")
    parser.add_argument("--target", default=TARGET_COLUMN, help="Target column")
    parser.add_argument("--test-size", type=int, default=12, help="Number of last months for testing")
    args = parser.parse_args()

    df = pd.read_csv(args.data, parse_dates=["date"])
    before = len(df)
    df = df.dropna(subset=[args.target]).reset_index(drop=True)
    dropped = before - len(df)
    if dropped:
        print(f"Dropped {dropped} rows with missing target values before training.")
    if len(df) <= args.test_size:
        raise SystemExit(
            f"Not enough target observations ({len(df)}) for test_size={args.test_size}. "
            "Reduce --test-size or add more target data."
        )
    train, test = temporal_train_test_split(df, test_size=args.test_size)

    y_train = train[args.target]
    y_test = test[args.target]

    models = {
        "naive": NaiveForecaster(),
        "seasonal_naive_12": SeasonalNaiveForecaster(season_length=12),
        "moving_average_3": MovingAverageForecaster(window=3),
        "moving_average_6": MovingAverageForecaster(window=6),
    }

    rows = []
    for name, model in models.items():
        model.fit(y_train)
        preds = model.predict(len(test))
        metrics = regression_report(y_test, preds)
        rows.append({"model": name, **metrics})

    results = pd.DataFrame(rows).sort_values("rmse")
    print(results.to_string(index=False))


if __name__ == "__main__":
    main()
