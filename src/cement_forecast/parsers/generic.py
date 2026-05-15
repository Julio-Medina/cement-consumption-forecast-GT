from __future__ import annotations

from pathlib import Path

import pandas as pd

from cement_forecast.cleaning import normalize_column_name
from cement_forecast.parsers.common import (
    MonthParseError,
    build_monthly_date,
    coerce_numeric_series,
    find_first_matching_column,
)

DATE_COLUMN_PATTERNS = [r"^fecha$", r"date", r"periodo", r"mes_ano", r"ano_mes"]
YEAR_COLUMN_PATTERNS = [r"^ano$", r"^anio$", r"year", r"ejercicio"]
MONTH_COLUMN_PATTERNS = [r"^mes$", r"month"]


def read_table_with_header(
    path: str | Path,
    *,
    sheet_name: str | int | None = 0,
    header_row: int = 0,
) -> pd.DataFrame:
    """Read a spreadsheet/CSV table using a known sheet and header row."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".xls", ".xlsx", ".xlsm"}:
        return pd.read_excel(path, sheet_name=sheet_name, header=header_row)
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(path)
    raise ValueError(f"Unsupported file type: {path.suffix}")


def parse_generic_monthly_table(
    path: str | Path,
    *,
    output_prefix: str,
    sheet_name: str | int | None = 0,
    header_row: int = 0,
    include_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
) -> pd.DataFrame:
    """Parse a table that has a monthly date or year/month columns.

    This is intentionally generic. Once the exact Banguat/INE file structures are
    known, source-specific parsers can wrap this function with fixed sheet names,
    header rows, and value-column filters.
    """
    include_keywords = [normalize_column_name(item) for item in (include_keywords or [])]
    exclude_keywords = [normalize_column_name(item) for item in (exclude_keywords or [])]

    df = read_table_with_header(path, sheet_name=sheet_name, header_row=header_row)
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    df.columns = [normalize_column_name(column) for column in df.columns]

    date_col = find_first_matching_column(df.columns, DATE_COLUMN_PATTERNS)
    year_col = find_first_matching_column(df.columns, YEAR_COLUMN_PATTERNS)
    month_col = find_first_matching_column(df.columns, MONTH_COLUMN_PATTERNS)

    try:
        dates = build_monthly_date(df, date_col=date_col, year_col=year_col, month_col=month_col)
    except MonthParseError as exc:
        raise MonthParseError(
            f"Could not build monthly dates for {path}. Try a different sheet/header_row."
        ) from exc

    out = pd.DataFrame({"date": dates})
    date_cols = {column for column in [date_col, year_col, month_col] if column}

    for column in df.columns:
        if column in date_cols:
            continue
        normalized = normalize_column_name(column)
        if include_keywords and not any(keyword in normalized for keyword in include_keywords):
            continue
        if exclude_keywords and any(keyword in normalized for keyword in exclude_keywords):
            continue
        values = coerce_numeric_series(df[column])
        if values.notna().sum() == 0:
            continue
        out[f"{output_prefix}_{normalized}"] = values

    out = out.dropna(subset=["date"])
    value_cols = [column for column in out.columns if column != "date"]
    if not value_cols:
        raise ValueError(f"No numeric value columns found in {path}")
    return out.groupby("date", as_index=False)[value_cols].sum(min_count=1).sort_values("date")
