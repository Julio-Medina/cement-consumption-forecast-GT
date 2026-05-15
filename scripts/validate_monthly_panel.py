#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cement_forecast.monthly_panel import validate_complete_monthly_panel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate that a CSV is a complete monthly panel.")
    parser.add_argument("--data", type=Path, required=True, help="CSV file to validate.")
    parser.add_argument("--start", default="2019-01-01", help="Inclusive panel start month.")
    parser.add_argument("--end", required=True, help="Inclusive panel end month.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.data, parse_dates=["date"])
    validate_complete_monthly_panel(df, start=args.start, end=args.end)
    print(f"OK: {args.data} is a complete monthly panel from {args.start} to {args.end}.")


if __name__ == "__main__":
    main()
