from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


import argparse

from cement_forecast.data_catalog import load_data_sources
from cement_forecast.download import download_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Download configured public data sources.")
    parser.add_argument("--source", help="Optional source key from data_sources.yml")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    sources = load_data_sources()
    selected = {args.source: sources[args.source]} if args.source else sources

    for key, source in selected.items():
        print(f"Downloading {key}: {source.name}")
        try:
            path = download_file(source, overwrite=args.overwrite)
        except Exception as exc:  # noqa: BLE001 - CLI should report source-specific failures
            print(f"  FAILED: {exc}")
            if source.page_url:
                print(f"  Manual download page: {source.page_url}")
            continue
        print(f"  saved to {path}")


if __name__ == "__main__":
    main()
