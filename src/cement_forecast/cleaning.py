from __future__ import annotations

import re
import unicodedata

import pandas as pd


def normalize_column_name(column: object) -> str:
    """Convert messy Spanish/Excel column names into snake_case names."""
    text = str(column).strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "unnamed"


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of a dataframe with normalized column names."""
    out = df.copy()
    out.columns = [normalize_column_name(column) for column in out.columns]
    return out


def ensure_month_start(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Normalize a date column to month-start timestamps."""
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col]).dt.to_period("M").dt.to_timestamp()
    return out.sort_values(date_col).reset_index(drop=True)


def aggregate_quarterly_to_monthly(
    df: pd.DataFrame,
    year_col: str = "ano",
    quarter_col: str = "trimestre",
    value_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Spread quarterly values evenly across the three months of each quarter.

    This is a pragmatic bridge when using quarterly construction-permit data as a
    monthly predictor. The transformation must be documented in the final report.
    """
    if value_cols is None:
        value_cols = [c for c in df.columns if c not in {year_col, quarter_col}]

    records: list[dict[str, object]] = []
    for _, row in df.iterrows():
        year = int(row[year_col])
        quarter = int(row[quarter_col])
        start_month = 3 * (quarter - 1) + 1
        for month in range(start_month, start_month + 3):
            record = {"date": pd.Timestamp(year=year, month=month, day=1)}
            for col in value_cols:
                record[col] = row[col] / 3 if pd.notna(row[col]) else pd.NA
            records.append(record)
    return pd.DataFrame(records)
