from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


IMAE_COLUMNS = [
    "imae_construction_index",
    "imae_general_index",
    "imae_construction_yoy",
    "imae_general_yoy",
    "imae_construction_trend_index",
    "imae_general_trend_index",
    "imae_construction_trend_yoy",
    "imae_general_trend_yoy",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check coverage of Banguat IMAE columns in the modeling dataset."
    )
    parser.add_argument(
        "--data",
        default="data/processed/modeling_dataset.csv",
        help="Path to modeling dataset CSV.",
    )
    parser.add_argument(
        "--required-start",
        default="2019-01-01",
        help="Required start date for the modeling panel.",
    )
    parser.add_argument(
        "--required-end",
        default=None,
        help="Optional required end date. If omitted, only observed coverage is reported.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    path = Path(args.data)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path, parse_dates=["date"]).sort_values("date")

    print("\nDataset")
    print(f"Path: {path}")
    print(f"Shape: {df.shape}")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    available = [col for col in IMAE_COLUMNS if col in df.columns]
    missing = [col for col in IMAE_COLUMNS if col not in df.columns]

    print("\nIMAE columns found")
    for col in available:
        s = pd.to_numeric(df[col], errors="coerce")
        non_null = df.loc[s.notna(), ["date", col]]

        if non_null.empty:
            print(f"- {col}: present but all values are missing")
            continue

        print(
            f"- {col}: {len(non_null)} observations, "
            f"{non_null['date'].min().date()} to {non_null['date'].max().date()}"
        )

    if missing:
        print("\nIMAE columns missing")
        for col in missing:
            print(f"- {col}")

    required_start = pd.Timestamp(args.required_start)
    required_end = pd.Timestamp(args.required_end) if args.required_end else df["date"].max()

    expected_dates = pd.date_range(required_start, required_end, freq="MS")

    print("\nRequired monthly window")
    print(f"{required_start.date()} to {required_end.date()}")
    print(f"Expected months: {len(expected_dates)}")

    if "imae_construction_index" not in df.columns:
        raise ValueError("imae_construction_index is missing from the dataset.")

    coverage = (
        df.set_index("date")
        .reindex(expected_dates)["imae_construction_index"]
    )

    missing_months = coverage[coverage.isna()].index

    print("\nimae_construction_index required-window coverage")
    print(f"Available months: {coverage.notna().sum()}")
    print(f"Missing months: {coverage.isna().sum()}")

    if len(missing_months) > 0:
        print("\nFirst missing months")
        for dt in missing_months[:20]:
            print(f"- {dt.date()}")

        raise ValueError(
            "imae_construction_index does not fully cover the required monthly window."
        )

    print("\nCoverage check passed.")


if __name__ == "__main__":
    main()
