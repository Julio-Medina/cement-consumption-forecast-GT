from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cement_forecast.advanced_models import train_holdout_ml_models
from cement_forecast.targets import default_target, validate_target_column


def parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train lagged ML forecasting models on the strict monthly panel."
    )
    parser.add_argument(
        "--data",
        default="data/processed/monthly_panel_2019_2026.csv",
        help="Path to strict monthly panel CSV.",
    )
    parser.add_argument(
        "--target",
        default=None,
        help="Target column. Defaults to the preferred target available in the dataset.",
    )
    parser.add_argument("--test-size", type=int, default=12)
    parser.add_argument("--lags", default="1,2,3,6,12")
    parser.add_argument("--rolling-windows", default="3,6,12")
    parser.add_argument(
        "--include-exogenous",
        action="store_true",
        help="Use one-month-lagged numeric non-target columns as additional predictors.",
    )
    parser.add_argument("--baseline-rmse", type=float, default=None)
    parser.add_argument("--baseline-mae", type=float, default=None)
    parser.add_argument(
        "--output-md",
        default="reports/advanced_model_results.md",
    )
    parser.add_argument(
        "--output-csv",
        default="reports/advanced_model_comparison.csv",
    )
    parser.add_argument(
        "--output-predictions",
        default="reports/advanced_model_predictions.csv",
    )
    return parser.parse_args()


def infer_exogenous_columns(df: pd.DataFrame, target: str) -> list[str]:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    return [col for col in numeric_cols if col != target]


def make_markdown_report(
    *,
    data_path: Path,
    target: str,
    comparison: pd.DataFrame,
    supervised_rows: int,
    feature_count: int,
    baseline_rmse: float | None,
    baseline_mae: float | None,
    include_exogenous: bool,
) -> str:
    best = comparison.iloc[0]

    lines = [
        "# Advanced Forecasting Model Results",
        "",
        "## Modeling setup",
        "",
        f"- Dataset: `{data_path}`",
        f"- Target: `{target}`",
        f"- Supervised rows after lag generation: {supervised_rows}",
        f"- Feature count: {feature_count}",
        f"- Exogenous predictors included: {include_exogenous}",
        "",
        "## Model comparison",
        "",
        comparison.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Best advanced model",
        "",
        f"The best advanced model by RMSE is `{best['model']}`.",
        "",
    ]

    if baseline_rmse is not None:
        rmse_delta = float(best["rmse"] - baseline_rmse)
        lines.extend(
            [
                "## Comparison against baseline benchmark",
                "",
                f"- Baseline RMSE: {baseline_rmse:.6f}",
                f"- Best advanced RMSE: {float(best['rmse']):.6f}",
                f"- RMSE delta: {rmse_delta:.6f}",
            ]
        )
        if baseline_mae is not None:
            mae_delta = float(best["mae"] - baseline_mae)
            lines.extend(
                [
                    f"- Baseline MAE: {baseline_mae:.6f}",
                    f"- Best advanced MAE: {float(best['mae']):.6f}",
                    f"- MAE delta: {mae_delta:.6f}",
                ]
            )
        lines.append("")
        if rmse_delta < 0:
            lines.append("The best advanced model beats the baseline benchmark by RMSE.")
        else:
            lines.append(
                "The advanced models do not yet beat the simple baseline by RMSE. "
                "This is a valid result: the simpler model remains the preferred benchmark until improved."
            )
        lines.append("")

    lines.extend(
        [
            "## Methodological note",
            "",
            "The ML models use shifted lag and rolling-window features. This avoids using the current target value "
            "as a predictor for the same month. Optional exogenous variables are also shifted by one month to keep "
            "the default setup conservative.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    args = parse_args()

    data_path = Path(args.data)
    df = pd.read_csv(data_path, parse_dates=["date"])

    target = args.target or default_target(df)
    validate_target_column(df, target, min_observations=args.test_size + max(parse_int_list(args.lags)) + 1)

    exogenous_columns = infer_exogenous_columns(df, target) if args.include_exogenous else None

    comparison, predictions, supervised = train_holdout_ml_models(
        df,
        target=target,
        test_size=args.test_size,
        lags=parse_int_list(args.lags),
        rolling_windows=parse_int_list(args.rolling_windows),
        exogenous_columns=exogenous_columns,
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
        comparison=comparison,
        supervised_rows=len(supervised.y),
        feature_count=supervised.X.shape[1],
        baseline_rmse=args.baseline_rmse,
        baseline_mae=args.baseline_mae,
        include_exogenous=args.include_exogenous,
    )
    output_md.write_text(report, encoding="utf-8")

    print("Advanced model comparison")
    print(comparison.to_string(index=False))
    print(f"\nWrote report: {output_md}")
    print(f"Wrote metrics: {output_csv}")
    print(f"Wrote predictions: {output_predictions}")


if __name__ == "__main__":
    main()
