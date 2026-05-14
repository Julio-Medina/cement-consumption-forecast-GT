from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


import numpy as np
import pandas as pd

from cement_forecast.config import PROCESSED_DATA_DIR


def main() -> None:
    """Create a realistic synthetic monthly dataset for pipeline development.

    This lets the repository run before all official Excel parsers are finalized.
    The synthetic data should be replaced by the real public-data table in later versions.
    """
    rng = np.random.default_rng(42)
    dates = pd.date_range("2012-01-01", "2026-03-01", freq="MS")
    t = np.arange(len(dates))

    seasonality = 8 * np.sin(2 * np.pi * dates.month / 12)
    trend = 0.18 * t
    remittances = 450 + 8.5 * t + 35 * np.sin(2 * np.pi * dates.month / 12 + 0.6) + rng.normal(0, 20, len(dates))
    exchange_rate = 7.65 + 0.08 * np.sin(2 * np.pi * t / 48) + rng.normal(0, 0.025, len(dates))
    ipmc_cement_index = 92 + 0.35 * t + rng.normal(0, 2.0, len(dates))
    construction_area_m2 = 80_000 + 700 * t + 6000 * np.sin(2 * np.pi * dates.month / 12 - 0.2) + rng.normal(0, 5000, len(dates))

    cement_demand_proxy = (
        120
        + trend
        + seasonality
        + 0.025 * remittances
        - 0.8 * (exchange_rate - exchange_rate.mean())
        - 0.06 * ipmc_cement_index
        + 0.00012 * construction_area_m2
        + rng.normal(0, 5, len(dates))
    )

    df = pd.DataFrame(
        {
            "date": dates,
            "cement_demand_proxy": cement_demand_proxy,
            "remittances_usd_millions": remittances,
            "exchange_rate_gtq_usd": exchange_rate,
            "ipmc_cement_index": ipmc_cement_index,
            "construction_area_m2": construction_area_m2,
        }
    )

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output = PROCESSED_DATA_DIR / "sample_modeling_dataset.csv"
    df.to_csv(output, index=False)
    print(f"Wrote {output} with {len(df)} monthly rows.")


if __name__ == "__main__":
    main()
