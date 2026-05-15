#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


import pandas as pd

from cement_forecast.config import PROCESSED_DATA_DIR
from cement_forecast.dataset import build_proxy_target, merge_monthly_frames, save_dataset
from cement_forecast.parsers.official import (
    parse_banguat_remittances,
    parse_banguat_trade_by_product,
    parse_ine_construction,
    parse_ine_ipmc,
)

PARSER_REGISTRY = {
    "banguat_remittances": parse_banguat_remittances,
    "banguat_trade_by_product": parse_banguat_trade_by_product,
    "ine_construction": parse_ine_construction,
    "ine_ipmc": parse_ine_ipmc,
}


def parse_source_spec(spec: str) -> tuple[str, Path, str | int, int]:
    """Parse CLI source specs.

    Format:
        parser_name:path[:sheet_name][:header_row]

    Examples:
        ine_ipmc:data/raw/ipmc.xls:Cuadro 1:5
        banguat_remittances:data/raw/remesas.xlsx:0:3
    """
    parts = spec.split(":")
    if len(parts) < 2:
        raise ValueError("source spec must have at least parser_name:path")
    parser_name = parts[0]
    path = Path(parts[1])
    sheet_name: str | int = 0
    header_row = 0
    if len(parts) >= 3 and parts[2] != "":
        sheet_name = int(parts[2]) if parts[2].isdigit() else parts[2]
    if len(parts) >= 4 and parts[3] != "":
        header_row = int(parts[3])
    return parser_name, path, sheet_name, header_row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the monthly modeling dataset.")
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help=(
            "Source specification parser_name:path[:sheet_name][:header_row]. "
            "Repeat this argument for multiple official files."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DATA_DIR / "modeling_dataset.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.source:
        raise SystemExit(
            "No sources provided. First run scripts/profile_raw_data.py, then pass one or more "
            "--source parser_name:path[:sheet_name][:header_row] values."
        )

    frames: list[pd.DataFrame] = []
    for spec in args.source:
        parser_name, path, sheet_name, header_row = parse_source_spec(spec)
        if parser_name not in PARSER_REGISTRY:
            valid = ", ".join(sorted(PARSER_REGISTRY))
            raise SystemExit(f"Unknown parser {parser_name!r}. Valid parsers: {valid}")
        frame = PARSER_REGISTRY[parser_name](path, sheet_name=sheet_name, header_row=header_row)
        print(
            f"Parsed {parser_name} from {path} "
            f"(sheet={sheet_name!r}, header_row={header_row}) -> {frame.shape}"
        )
        frames.append(frame)

    merged = merge_monthly_frames(frames)
    modeled = build_proxy_target(merged)
    save_dataset(modeled, args.output)
    print(f"Saved modeling dataset to {args.output} with shape {modeled.shape}")


if __name__ == "__main__":
    main()
