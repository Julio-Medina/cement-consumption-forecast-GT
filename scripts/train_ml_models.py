from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import argparse

import pandas as pd

from cement_forecast.config import TARGET_COLUMN
from cement_forecast.ml_models import evaluate_holdout_models, prepare_supervised_features


def main() -> None:
    parser = argparse.ArgumentParser(description="Train leakage-aware ML forecasting models.")
    parser.add_argument("--data", required=True, help="Path to modeling_dataset.csv")
    parser.add_argument("--target", default=TARGET_COLUMN, help="Target column")
    parser.add_argument("--test-size", type=int, default=12, help="Number of last observations for testing")
    parser.add_argument("--output-dir", default="reports", help="Directory for CSV outputs")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.data, parse_dates=["date"])
    supervised, feature_cols = prepare_supervised_features(df, target_col=args.target)
    results, predictions = evaluate_holdout_models(
        supervised,
        feature_cols=feature_cols,
        target_col=args.target,
        test_size=args.test_size,
    )

    results_path = output_dir / "ml_model_comparison.csv"
    predictions_path = output_dir / "ml_holdout_predictions.csv"
    results.to_csv(results_path, index=False)
    predictions.to_csv(predictions_path, index=False)

    print(f"Supervised observations: {len(supervised)}")
    print(f"Feature count: {len(feature_cols)}")
    print(results.to_string(index=False))
    print(f"\nSaved model comparison to {results_path}")
    print(f"Saved holdout predictions to {predictions_path}")


if __name__ == "__main__":
    main()
