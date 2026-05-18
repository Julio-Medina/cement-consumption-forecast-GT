from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cement_forecast.diagnostics import (  # noqa: E402
    best_model_row,
    compute_lag_correlations,
    filter_predictions_for_model,
    percentage_improvement,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create forecast diagnostics figures and a Markdown interpretation report."
    )
    parser.add_argument(
        "--data",
        default="data/processed/monthly_panel_2019_2026.csv",
        help="Strict monthly panel CSV.",
    )
    parser.add_argument(
        "--target",
        default="imae_construction_index",
        help="Target column used for forecasting.",
    )
    parser.add_argument(
        "--comparison",
        default="reports/advanced_model_comparison.csv",
        help="CSV with model comparison metrics.",
    )
    parser.add_argument(
        "--predictions",
        default="reports/advanced_model_predictions.csv",
        help="CSV with holdout predictions.",
    )
    parser.add_argument(
        "--baseline-rmse",
        type=float,
        required=True,
        help="RMSE of the strongest baseline model.",
    )
    parser.add_argument(
        "--baseline-mae",
        type=float,
        required=True,
        help="MAE of the strongest baseline model.",
    )
    parser.add_argument(
        "--output-md",
        default="reports/forecast_diagnostics_report.md",
        help="Output Markdown report path.",
    )
    parser.add_argument(
        "--figures-dir",
        default="reports/figures",
        help="Directory where diagnostic figures are written.",
    )
    return parser.parse_args()


def _prepare_comparison(comparison: pd.DataFrame) -> pd.DataFrame:
    comparison = comparison.copy()

    for col in ["mae", "rmse", "mape", "smape"]:
        if col in comparison.columns:
            comparison[col] = pd.to_numeric(comparison[col], errors="coerce")

    if "status" in comparison.columns:
        trained = comparison[comparison["status"].eq("trained")].copy()
        if not trained.empty:
            comparison = trained

    return comparison.sort_values("rmse").reset_index(drop=True)


def _plot_model_comparison_rmse(comparison: pd.DataFrame, output_path: Path) -> None:
    comparison = _prepare_comparison(comparison)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(comparison["model"], comparison["rmse"])
    ax.set_title("Advanced model comparison by RMSE")
    ax.set_xlabel("Model")
    ax.set_ylabel("RMSE")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _plot_holdout_actual_vs_predicted(
    predictions: pd.DataFrame,
    best_model: str,
    output_path: Path,
) -> None:
    best_predictions = filter_predictions_for_model(predictions, best_model)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(best_predictions["date"], best_predictions["actual"], marker="o", label="Actual")
    ax.plot(
        best_predictions["date"],
        best_predictions["prediction"],
        marker="o",
        label="Predicted",
    )
    ax.set_title("Holdout actual vs predicted")
    ax.set_xlabel("Date")
    ax.set_ylabel("Target value")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _plot_holdout_residuals(
    predictions: pd.DataFrame,
    best_model: str,
    output_path: Path,
) -> None:
    best_predictions = filter_predictions_for_model(predictions, best_model).copy()
    best_predictions["residual"] = (
        best_predictions["actual"] - best_predictions["prediction"]
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axhline(0.0, linewidth=1)
    ax.plot(best_predictions["date"], best_predictions["residual"], marker="o")
    ax.set_title("Holdout residuals")
    ax.set_xlabel("Date")
    ax.set_ylabel("Actual - predicted")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _plot_lag_correlation_importance(
    correlations: pd.DataFrame,
    output_path: Path,
    top_n: int = 15,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))

    if correlations.empty:
        ax.text(0.5, 0.5, "No lag correlations available", ha="center", va="center")
        ax.set_axis_off()
    else:
        plot_df = correlations.sort_values("abs_correlation", ascending=False).head(top_n).copy()
        plot_df["label"] = plot_df["feature"] + " (lag " + plot_df["lag"].astype(str) + ")"
        plot_df = plot_df.sort_values("abs_correlation")

        ax.barh(plot_df["label"], plot_df["abs_correlation"])
        ax.set_title("Top lag correlations with target")
        ax.set_xlabel("Absolute correlation")

    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def make_figures(
    *,
    comparison: pd.DataFrame,
    predictions: pd.DataFrame,
    correlations: pd.DataFrame,
    best_model: str,
    figures_dir: Path,
) -> Dict[str, Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)

    figure_paths = {
        "model_comparison_rmse": figures_dir / "model_comparison_rmse.png",
        "holdout_actual_vs_predicted": figures_dir / "holdout_actual_vs_predicted.png",
        "holdout_residuals": figures_dir / "holdout_residuals.png",
        "lag_correlation_importance": figures_dir / "lag_correlation_importance.png",
    }

    _plot_model_comparison_rmse(comparison, figure_paths["model_comparison_rmse"])
    _plot_holdout_actual_vs_predicted(
        predictions,
        best_model,
        figure_paths["holdout_actual_vs_predicted"],
    )
    _plot_holdout_residuals(
        predictions,
        best_model,
        figure_paths["holdout_residuals"],
    )
    _plot_lag_correlation_importance(
        correlations,
        figure_paths["lag_correlation_importance"],
    )

    return figure_paths


def build_report(
    *,
    data_path: Path,
    target: str,
    comparison: pd.DataFrame,
    correlations: pd.DataFrame,
    best_model: str,
    baseline_rmse: float,
    baseline_mae: float,
    figure_paths: Dict[str, Path],
) -> str:
    comparison = _prepare_comparison(comparison)
    best = comparison[comparison["model"].eq(best_model)].iloc[0]

    rmse_improvement = percentage_improvement(baseline_rmse, float(best["rmse"]))
    mae_improvement = percentage_improvement(baseline_mae, float(best["mae"]))

    lines = [
        "# Forecast Diagnostics and Model Interpretation",
        "",
        "## Modeling target",
        "",
        f"- Dataset: `{data_path}`",
        f"- Target: `{target}`",
        f"- Best advanced model: `{best_model}`",
        "",
        "## Model comparison",
        "",
        comparison.to_markdown(index=False, floatfmt=".6f"),
        "",
        "## Improvement over baseline",
        "",
        f"- Baseline RMSE: {baseline_rmse:.6f}",
        f"- Best advanced RMSE: {float(best['rmse']):.6f}",
        f"- RMSE improvement: {rmse_improvement:.2f}%",
        f"- Baseline MAE: {baseline_mae:.6f}",
        f"- Best advanced MAE: {float(best['mae']):.6f}",
        f"- MAE improvement: {mae_improvement:.2f}%",
        "",
        "## Diagnostic figures",
        "",
    ]

    if figure_paths:
        for name, path in figure_paths.items():
            lines.append(f"- {name}: `{path}`")
    else:
        lines.append("- No figure paths were provided.")

    lines.extend(
        [
            "",
            "## Lag-correlation diagnostics",
            "",
        ]
    )

    if correlations.empty:
        lines.append("No lag-correlation diagnostics were available.")
    else:
        top = correlations.sort_values("abs_correlation", ascending=False).head(10)
        lines.append(top.to_markdown(index=False, floatfmt=".6f"))

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The advanced lagged forecasting workflow is evaluated against the strongest "
            "simple baseline. The result is only considered useful if it improves on that "
            "benchmark. In the current experiment, the best advanced model is compared "
            "directly against the moving-average baseline using MAE and RMSE.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    args = parse_args()

    data_path = Path(args.data)
    comparison_path = Path(args.comparison)
    predictions_path = Path(args.predictions)
    output_md = Path(args.output_md)
    figures_dir = Path(args.figures_dir)

    data = pd.read_csv(data_path, parse_dates=["date"])
    comparison = pd.read_csv(comparison_path)
    predictions = pd.read_csv(predictions_path, parse_dates=["date"])

    comparison = _prepare_comparison(comparison)
    best = best_model_row(comparison)
    best_model = str(best["model"])

    correlations = compute_lag_correlations(
        data,
        target=args.target,
        max_lag=12,
        min_observations=24,
    )

    figure_paths = make_figures(
        comparison=comparison,
        predictions=predictions,
        correlations=correlations,
        best_model=best_model,
        figures_dir=figures_dir,
    )

    report = build_report(
        data_path=data_path,
        target=args.target,
        comparison=comparison,
        correlations=correlations,
        best_model=best_model,
        baseline_rmse=args.baseline_rmse,
        baseline_mae=args.baseline_mae,
        figure_paths=figure_paths,
    )

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(report, encoding="utf-8")

    print(f"Wrote diagnostics report: {output_md}")
    for name, path in figure_paths.items():
        print(f"Wrote {name}: {path}")


if __name__ == "__main__":
    main()
