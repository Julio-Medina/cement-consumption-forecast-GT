from __future__ import annotations

from functools import reduce
from pathlib import Path

import pandas as pd

from cement_forecast.cleaning import ensure_month_start
from cement_forecast.config import DATE_COLUMN, TARGET_COLUMN


def merge_monthly_frames(frames: list[pd.DataFrame], date_col: str = DATE_COLUMN) -> pd.DataFrame:
    """Outer-merge multiple monthly dataframes on date."""
    valid_frames = []
    for frame in frames:
        if frame is None or frame.empty:
            continue
        if date_col not in frame.columns:
            raise ValueError(f"All frames must contain a {date_col!r} column")
        valid_frames.append(ensure_month_start(frame, date_col))

    if not valid_frames:
        raise ValueError("No non-empty frames were provided")

    merged = reduce(lambda left, right: pd.merge(left, right, on=date_col, how="outer"), valid_frames)
    return merged.sort_values(date_col).reset_index(drop=True)


def build_proxy_target(
    df: pd.DataFrame,
    *,
    candidate_columns: list[str] | None = None,
    target_col: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """Build a transparent cement-demand proxy from available numeric indicators.

    The proxy is the average of z-scored candidate indicators after interpolating
    missing values. This is not a substitute for true cement consumption; it is a
    documented public-data proxy that can be replaced when a direct target is found.
    """
    out = df.copy()
    if candidate_columns is None:
        candidate_columns = [
            column
            for column in out.columns
            if column != "date"
            and any(
                token in column
                for token in [
                    "cement",
                    "construction",
                    "construccion",
                    "area",
                    "costo",
                    "trade",
                    "ipmc",
                ]
            )
        ]

    candidate_columns = [column for column in candidate_columns if column in out.columns]
    if not candidate_columns:
        raise ValueError("Could not build proxy target because no candidate columns were found")

    numeric = out[candidate_columns].apply(pd.to_numeric, errors="coerce")
    numeric = numeric.interpolate(limit_direction="both")
    std = numeric.std(ddof=0).replace(0, pd.NA)
    zscores = (numeric - numeric.mean()) / std
    out[target_col] = zscores.mean(axis=1, skipna=True)
    return out


def save_dataset(df: pd.DataFrame, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
