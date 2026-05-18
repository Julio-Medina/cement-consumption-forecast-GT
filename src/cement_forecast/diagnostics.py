from __future__ import annotations

from pathlib import Path

import pandas as pd


def percentage_improvement(baseline_value: float, model_value: float) -> float:
    """Return percentage improvement of a lower-is-better metric."""
    if baseline_value == 0:
        return float("nan")
    return float((baseline_value - model_value) / baseline_value * 100)


def trained_model_rows(comparison: pd.DataFrame) -> pd.DataFrame:
    """Return model-comparison rows that contain valid RMSE values."""
    frame = comparison.copy()
    if "status" in frame.columns:
        frame = frame[frame["status"].astype(str).str.lower().eq("trained")]
    frame = frame[pd.to_numeric(frame["rmse"], errors="coerce").notna()]
    return frame.copy()


def best_model_row(comparison: pd.DataFrame) -> pd.Series:
    """Return the best trained model row by RMSE."""
    trained = trained_model_rows(comparison)
    if trained.empty:
        raise ValueError("No trained models with valid RMSE were found.")
    return trained.sort_values("rmse").iloc[0]


def filter_predictions_for_model(predictions: pd.DataFrame, model_name: str) -> pd.DataFrame:
    """Return holdout predictions for one model, sorted by date."""
    frame = predictions[predictions["model"].astype(str).eq(str(model_name))].copy()
    if frame.empty:
        raise ValueError(f"No predictions found for model {model_name!r}.")
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.sort_values("date").reset_index(drop=True)


def compute_lag_correlations(
    df: pd.DataFrame,
    *,
    target: str,
    max_lag: int = 12,
    min_observations: int = 24,
) -> pd.DataFrame:
    """Compute lagged correlations between numeric features and the target.

    The feature is shifted by lag months, so correlation(feature[t-lag], target[t])
    is estimated. This is a leakage-safe diagnostic because only past feature
    values are compared with the current target.
    """
    if target not in df.columns:
        raise ValueError(f"Target column {target!r} was not found.")

    ordered = df.copy()
    if "date" in ordered.columns:
        ordered["date"] = pd.to_datetime(ordered["date"])
        ordered = ordered.sort_values("date")

    numeric_cols = [
        col
        for col in ordered.columns
        if col != "date" and pd.api.types.is_numeric_dtype(ordered[col])
    ]

    rows: list[dict[str, float | int | str]] = []

    for feature in numeric_cols:
        for lag in range(1, max_lag + 1):
            pair = pd.DataFrame(
                {
                    "target": pd.to_numeric(ordered[target], errors="coerce"),
                    "feature_lag": pd.to_numeric(ordered[feature], errors="coerce").shift(lag),
                }
            ).dropna()

            if len(pair) < min_observations:
                continue

            corr = pair["target"].corr(pair["feature_lag"])
            if pd.isna(corr):
                continue

            rows.append(
                {
                    "feature": feature,
                    "lag": lag,
                    "correlation": float(corr),
                    "abs_correlation": float(abs(corr)),
                    "observations": int(len(pair)),
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=["feature", "lag", "correlation", "abs_correlation", "observations"]
        )

    return pd.DataFrame(rows).sort_values("abs_correlation", ascending=False).reset_index(drop=True)


def save_model_comparison_plot(comparison: pd.DataFrame, output_path: str | Path) -> Path:
    """Save a bar chart comparing trained models by RMSE."""
    import matplotlib.pyplot as plt

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    trained = trained_model_rows(comparison).sort_values("rmse")
    if trained.empty:
        raise ValueError("No trained model rows available for plotting.")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(trained["model"].astype(str), trained["rmse"])
    ax.set_title("Advanced model comparison by RMSE")
    ax.set_ylabel("RMSE")
    ax.set_xlabel("Model")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def save_actual_vs_predicted_plot(
    predictions: pd.DataFrame,
    *,
    model_name: str,
    output_path: str | Path,
) -> Path:
    """Save a holdout actual-vs-predicted line chart for one model."""
    import matplotlib.pyplot as plt

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    frame = filter_predictions_for_model(predictions, model_name)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(frame["date"], frame["actual"], marker="o", label="Actual")
    ax.plot(frame["date"], frame["prediction"], marker="o", label="Prediction")
    ax.set_title(f"Holdout actual vs predicted: {model_name}")
    ax.set_ylabel("Target value")
    ax.set_xlabel("Date")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def save_residual_plot(
    predictions: pd.DataFrame,
    *,
    model_name: str,
    output_path: str | Path,
) -> Path:
    """Save a holdout residual plot for one model."""
    import matplotlib.pyplot as plt

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    frame = filter_predictions_for_model(predictions, model_name)
    residuals = frame["actual"] - frame["prediction"]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axhline(0, linewidth=1)
    ax.plot(frame["date"], residuals, marker="o")
    ax.set_title(f"Holdout residuals: {model_name}")
    ax.set_ylabel("Actual - prediction")
    ax.set_xlabel("Date")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def save_lag_correlation_plot(correlations: pd.DataFrame, output_path: str | Path, top_n: int = 12) -> Path:
    """Save a horizontal bar chart of top absolute lag correlations."""
    import matplotlib.pyplot as plt

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    top = correlations.head(top_n).copy()
    if top.empty:
        raise ValueError("No lag correlations available for plotting.")

    top["label"] = top["feature"].astype(str) + " lag " + top["lag"].astype(str)
    top = top.iloc[::-1]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top["label"], top["abs_correlation"])
    ax.set_title("Top leakage-safe lag correlations")
    ax.set_xlabel("Absolute correlation")
