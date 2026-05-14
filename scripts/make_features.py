from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


import argparse
from pathlib import Path

import pandas as pd

from cement_forecast.features import make_supervised_monthly_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Create supervised monthly features from a modeling table.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--target", default="cement_demand_proxy")
    args = parser.parse_args()

    df = pd.read_csv(args.input, parse_dates=["date"])
    predictors = [c for c in df.columns if c not in {"date", args.target}]
    featured = make_supervised_monthly_dataset(df, target_col=args.target, predictor_cols=predictors)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    featured.to_csv(output, index=False)
    print(f"Wrote {output} with {len(featured)} rows and {featured.shape[1]} columns.")


if __name__ == "__main__":
    main()
