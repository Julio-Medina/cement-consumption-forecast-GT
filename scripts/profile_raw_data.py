#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


from cement_forecast.config import RAW_DATA_DIR, REPORTS_DIR
from cement_forecast.raw_profile import (
    candidates_to_dataframe,
    profile_raw_directory,
    write_markdown_inventory,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile raw official data files.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--output", type=Path, default=REPORTS_DIR / "raw_data_inventory.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    candidates = profile_raw_directory(args.raw_dir)
    write_markdown_inventory(candidates, args.output)

    df = candidates_to_dataframe(candidates)
    if df.empty:
        print(f"No table candidates detected in {args.raw_dir}")
        print(f"Inventory written to {args.output}")
        return

    display_cols = [
        "path",
        "sheet_name",
        "header_row",
        "rows",
        "columns",
        "date_like_columns",
        "numeric_like_columns",
    ]
    print(df[display_cols].to_string(index=False, max_colwidth=80))
    print(f"\nInventory written to {args.output}")


if __name__ == "__main__":
    main()
