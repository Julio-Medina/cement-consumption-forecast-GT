#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cement_forecast.config import PROCESSED_DATA_DIR
from cement_forecast.monthly_panel import build_strict_monthly_panel, write_monthly_panel_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a strict complete monthly panel for forecasting."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=PROCESSED_DATA_DIR / "modeling_dataset.csv",
        help="Input merged modeling dataset CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DATA_DIR / "monthly_panel_2019_2026.csv",
        help="Output complete monthly panel CSV.",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=Path("reports/monthly_panel_report.md"),
        help="Markdown report describing selected and dropped columns.",
    )
    parser.add_argument("--start", default="2019-01-01", help="Inclusive panel start month.")
    parser.add_argument(
        "--end",
        default=None,
        help="Inclusive panel end month. If omitted, uses the latest month in the input data.",
    )
    parser.add_argument(
        "--column",
        action="append",
        default=None,
        help="Candidate column to include. Repeat for multiple columns. If omitted, all numeric columns are candidates.",
    )
    parser.add_argument(
        "--required-column",
        action="append",
        default=[],
        help="Column that must exist and be complete over the selected period. Repeat for multiple columns.",
    )
    parser.add_argument(
        "--fail-on-incomplete-columns",
        action="store_true",
        help="Fail instead of dropping non-required incomplete columns.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.data, parse_dates=["date"])

    panel, report = build_strict_monthly_panel(
        df,
        start=args.start,
        end=args.end,
        columns=args.column,
        required_columns=args.required_column,
        drop_incomplete_columns=not args.fail_on_incomplete_columns,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(args.output, index=False)
    write_monthly_panel_report(report, args.report_output)

    print(f"Saved strict monthly panel to {args.output} with shape {panel.shape}")
    print(f"Saved report to {args.report_output}")
    print(f"Period: {report.start.date()} to {report.end.date()}")
    print(f"Selected complete columns: {len(report.selected_columns)}")
    print(f"Dropped incomplete columns: {len(report.dropped_columns)}")


if __name__ == "__main__":
    main()
