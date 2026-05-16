from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cement_forecast.evaluation import temporal_train_test_split
from cement_forecast.models import (
    MovingAverageForecaster,
    NaiveForecaster,
    SeasonalNaiveForecaster,
)
from cement_forecast.targets import default_target, validate_target_column


def evaluate_forecast(y_true, y_pred) -> dict[str, float]:
    """Compute standard forecast metrics.

    This local function avoids depending on a specific evaluation.py API.
    """
    y_true = pd.Series(y_true, dtype="float64").reset_index(drop=True)
    y_pred = pd.Series(y_pred, dtype="float64").reset_index(drop=True)

    error = y_true - y_pred
    abs_error = error.abs()

    mae = float(abs_error.mean())
    rmse = float((error.pow(2).mean()) ** 0.5)

    nonzero_true = y_true.abs() > 1e-12
    if nonzero_true.any():
        mape = float((abs_error[nonzero_true] / y_true[nonzero_true].abs()).mean() * 100)
    else:
        mape = float("nan")

    denominator = y_true.abs() + y_pred.abs()
    nonzero_denom = denominator > 1e-12
    if nonzero_denom.any():
        smape = float((2 * abs_error[nonzero_denom] / denominator[nonzero_denom]).mean() * 100)
    else:
        smape = float("nan")

    return {
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "smape": smape,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train baseline forecasters and write a Markdown report."
    )
    parser.add_argument(
        "--data",
        default="data/processed/monthly_panel_2019_2026.csv",
        help="Path to a strict monthly panel CSV.",
    )
    parser.add_argument(
        "--target",
        default=None,
        help="Target column to forecast. If omitted, a default target is selected.",
    )
    parser.add_argument(
        "--test-size",
        type=int,
        default=12,
        help="Number of latest monthly observations used as holdout test set.",
    )
    parser.add_argument(
        "--output-md",
        default="reports/imae_baseline_results.md",
        help="Path to write the Markdown report.",
    )
    parser.add_argument(
        "--output-csv",
        default="reports/imae_baseline_comparison.csv",
        help="Path to write model-comparison metrics.",
    )
    parser.add_argument(
        "--output-predictions",
        default="reports/imae_baseline_predictions.csv",
        help="Path to write holdout predictions.",
    )
    return parser.parse_args()


def baseline_models() -> list[tuple[str, object]]:
    return [
        ("naive", NaiveForecaster()),
        ("moving_average_3", MovingAverageForecaster(window=3)),
        ("moving_average_6", MovingAverageForecaster(window=6)),
        ("seasonal_naive_12", SeasonalNaiveForecaster(season_length=12)),
    ]


def train_baselines(
    df: pd.DataFrame,
    *,
    target: str,
    test_size: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = df.sort_values("date").copy()
    df = df.dropna(subset=[target]).copy()

    if len(df) <= test_size:
        raise ValueError(
            f"Not enough observations for target {target!r}: "
            f"{len(df)} rows with test_size={test_size}."
        )

    train, test = temporal_train_test_split(df, test_size=test_size)
    y_train = train[target]
    y_test = test[target]

    metric_rows: list[dict[str, float | str]] = []
    prediction_frames: list[pd.DataFrame] = []

    for name, model in baseline_models():
        try:
            model.fit(y_train)
            pred = model.predict(len(y_test))
            metrics = evaluate_forecast(y_test, pred)
        except ValueError as exc:
            metric_rows.append(
                {
                    "model": name,
                    "mae": float("nan"),
                    "rmse": float("nan"),
                    "mape": float("nan"),
                    "smape": float("nan"),
                    "status": f"skipped: {exc}",
                }
            )
            continue

        metric_rows.append({"model": name, **metrics, "status": "trained"})

        prediction_frames.append(
            pd.DataFrame(
                {
                    "date": test["date"].to_numpy(),
                    "target": target,
                    "model": name,
                    "actual": y_test.to_numpy(),
                    "prediction": pred,
                }
            )
        )

    comparison = pd.DataFrame(metric_rows)
    trained = comparison[comparison["status"].eq("trained")].copy()
    skipped = comparison[~comparison["status"].eq("trained")].copy()

    if trained.empty:
        raise ValueError(f"No baseline model could be trained for target {target!r}.")

    trained = trained.sort_values("rmse").reset_index(drop=True)
    comparison = pd.concat([trained, skipped], ignore_index=True)

    predictions = (
        pd.concat(prediction_frames, ignore_index=True)
        if prediction_frames
        else pd.DataFrame(columns=["date", "target", "model", "actual", "prediction"])
    )

    return train, test, comparison, predictions


def make_markdown_report(
    *,
    data_path: Path,
    target: str,
    train: pd.DataFrame,
    test: pd.DataFrame,
    comparison: pd.DataFrame,
) -> str:
    trained = comparison[comparison["status"].eq("trained")].copy()
    best = trained.iloc[0]

    lines = [
        "# IMAE Construction Baseline Forecasting Results",
        "",
        "## Modeling setup",
        "",
        f"- Dataset: `{data_path}`",
        f"- Target: `{target}`",
        f"- Training window: {train['date'].min().date()} to {train['date'].max().date()}",
        f"- Holdout window: {test['date'].min().date()} to {test['date'].max().date()}",
        f"- Training observations: {len(train)}",
        f"- Holdout observations: {len(test)}",
        "",
        "## Model comparison",
        "",
        comparison.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Best baseline",
        "",
        f"The best baseline by RMSE is `{best['model']}`.",
        "",
        "This baseline becomes the benchmark that advanced forecasting models must beat. "
        "If a more complex model does not improve on this result, the simpler baseline is preferred.",
        "",
        "## Portfolio interpretation",
        "",
        "The target is a real public monthly construction-activity indicator from Banguat IMAE. "
        "This is more defensible than the earlier exploratory cement-demand proxy because it is "
        "directly observed, monthly, and complete over the selected recent modeling window.",
        "",
    ]

    return "\n".join(lines)


def main() -> None:
    args = parse_args()

    data_path = Path(args.data)
    df = pd.read_csv(data_path, parse_dates=["date"])

    target = args.target or default_target(df)
    validate_target_column(df, target, min_observations=args.test_size + 1)

    train, test, comparison, predictions = train_baselines(
        df,
        target=target,
        test_size=args.test_size,
    )

    output_md = Path(args.output_md)
    output_csv = Path(args.output_csv)
    output_predictions = Path(args.output_predictions)

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_predictions.parent.mkdir(parents=True, exist_ok=True)

    comparison.to_csv(output_csv, index=False)
    predictions.to_csv(output_predictions, index=False)

    report = make_markdown_report(
        data_path=data_path,
        target=target,
        train=train,
        test=test,
        comparison=comparison,
    )

    output_md.write_text(report, encoding="utf-8")

    print("Baseline model comparison")
    print(comparison.to_string(index=False))
    print(f"\nWrote report: {output_md}")
    print(f"Wrote metrics: {output_csv}")
    print(f"Wrote predictions: {output_predictions}")


if __name__ == "__main__":
    main()
