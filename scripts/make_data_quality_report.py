from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import argparse

import pandas as pd

from cement_forecast.config import TARGET_COLUMN


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    return df.to_markdown(index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Markdown quality report for the modeling dataset.")
    parser.add_argument("--data", default="data/processed/modeling_dataset.csv", help="Path to modeling dataset")
    parser.add_argument("--output", default="reports/data_quality_report.md", help="Markdown output path")
    parser.add_argument("--target", default=TARGET_COLUMN, help="Target column")
    args = parser.parse_args()

    df = pd.read_csv(args.data, parse_dates=["date"])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    missing = (
        df.isna()
        .mean()
        .mul(100)
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"index": "column", 0: "missing_pct"})
        .head(25)
    )

    numeric = df.select_dtypes(include="number")
    corr_table = pd.DataFrame(columns=["feature", "correlation_with_target"])
    if args.target in numeric.columns and numeric.shape[1] > 1:
        corr_table = (
            numeric.corr(numeric_only=True)[args.target]
            .drop(args.target, errors="ignore")
            .sort_values(key=lambda s: s.abs(), ascending=False)
            .head(15)
            .reset_index()
            .rename(columns={"index": "feature", args.target: "correlation_with_target"})
        )

    source_count = pd.DataFrame()
    source_col = f"{args.target}_source_count"
    if source_col in df.columns:
        source_count = (
            df[source_col]
            .value_counts()
            .sort_index()
            .reset_index()
            .rename(columns={source_col: "source_count", "count": "rows"})
        )

    target_summary = pd.DataFrame()
    if args.target in df.columns:
        target_summary = df[args.target].describe().reset_index()
        target_summary.columns = ["statistic", "value"]

    content = f"""# Modeling Dataset Quality Report

Generated from `{args.data}`.

## Dataset shape

- Rows: `{len(df)}`
- Columns: `{df.shape[1]}`
- Date range: `{df['date'].min().date()}` to `{df['date'].max().date()}`

## Target summary

{markdown_table(target_summary)}

## Target source-count distribution

{markdown_table(source_count)}

## Highest missing-value columns

{markdown_table(missing)}

## Strongest numeric correlations with target

{markdown_table(corr_table)}

## Interpretation notes

- `cement_demand_proxy` is a public-data proxy, not observed private cement consumption.
- The current observed modeling window starts in 2019 because IPMC historical material indices begin there.
- Construction permit variables are sparse in the current raw download, so they should be treated as exploratory predictors until more years are added.
- Avoid using same-month predictors for forecasting. The ML script creates lagged features to reduce leakage.
"""
    output.write_text(content, encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
