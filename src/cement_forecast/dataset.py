from __future__ import annotations

from functools import reduce
from pathlib import Path

import pandas as pd

from cement_forecast.cleaning import ensure_month_start
from cement_forecast.config import DATE_COLUMN, TARGET_COLUMN


DEFAULT_PROXY_KEYWORDS = [
    "cement",
    "construction",
    "construccion",
    "area",
    "costo",
    "trade",
    "ipmc",
]


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


def infer_proxy_candidate_columns(df: pd.DataFrame, date_col: str = DATE_COLUMN) -> list[str]:
    """Infer construction/cement-related columns that can contribute to the proxy target.

    Macroeconomic drivers such as remittances are intentionally excluded from the
    proxy target by default. They should be predictors, not part of the dependent
    variable we are trying to forecast.
    """
    candidates: list[str] = []
    for column in df.columns:
        if column == date_col:
            continue
        if any(token in column for token in DEFAULT_PROXY_KEYWORDS):
            candidates.append(column)
    return candidates


def build_proxy_target(
    df: pd.DataFrame,
    *,
    candidate_columns: list[str] | None = None,
    target_col: str = TARGET_COLUMN,
    min_observed_indicators: int = 1,
    interpolate_inside_gaps: bool = False,
) -> pd.DataFrame:
    """Build a transparent cement-demand proxy from observed public indicators.

    The proxy is the row-wise average of z-scored candidate indicators. Unlike the
    first scaffold version, this function does *not* extrapolate indicators across
    long missing periods. This prevents early years from receiving artificial proxy
    values when the construction/IPMC indicators were not observed.

    Parameters
    ----------
    df:
        Monthly dataframe containing a ``date`` column and numeric indicators.
    candidate_columns:
        Columns to use in the proxy. If omitted, construction/cement/IPMC-related
        columns are inferred by name.
    min_observed_indicators:
        Minimum number of observed candidate indicators required for a row to have
        a non-null target. Use a higher value when more official target components
        are available.
    interpolate_inside_gaps:
        If True, interpolate only internal gaps inside each indicator series. It
        will not backfill before the first observation or forward-fill after the
        last observation.
    """
    out = df.copy()
    if candidate_columns is None:
        candidate_columns = infer_proxy_candidate_columns(out)

    candidate_columns = [column for column in candidate_columns if column in out.columns]
    if not candidate_columns:
        raise ValueError("Could not build proxy target because no candidate columns were found")

    numeric = out[candidate_columns].apply(pd.to_numeric, errors="coerce")
    if interpolate_inside_gaps:
        numeric = numeric.interpolate(limit_area="inside")

    observed_indicator_count = numeric.notna().sum(axis=1)
    std = numeric.std(ddof=0).replace(0, pd.NA)
    zscores = (numeric - numeric.mean()) / std
    out[target_col] = zscores.mean(axis=1, skipna=True)
    out[f"{target_col}_source_count"] = observed_indicator_count
    out.loc[observed_indicator_count < min_observed_indicators, target_col] = pd.NA
    return out


def keep_rows_with_target(
    df: pd.DataFrame,
    *,
    target_col: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """Return only rows that have an observed/modelable target value."""
    if target_col not in df.columns:
        raise ValueError(f"Target column {target_col!r} is missing")
    return df.dropna(subset=[target_col]).reset_index(drop=True)


def save_dataset(df: pd.DataFrame, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
