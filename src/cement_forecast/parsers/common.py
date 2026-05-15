from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from cement_forecast.cleaning import ensure_month_start, normalize_columns, normalize_column_name


class MonthParseError(ValueError):
    """Raised when a monthly date cannot be constructed from a source file."""


SPANISH_MONTHS = {
    "ene": 1,
    "enero": 1,
    "jan": 1,
    "january": 1,
    "feb": 2,
    "febrero": 2,
    "february": 2,
    "mar": 3,
    "marzo": 3,
    "march": 3,
    "abr": 4,
    "abril": 4,
    "apr": 4,
    "april": 4,
    "may": 5,
    "mayo": 5,
    "jun": 6,
    "junio": 6,
    "june": 6,
    "jul": 7,
    "julio": 7,
    "july": 7,
    "ago": 8,
    "agosto": 8,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "septiembre": 9,
    "setiembre": 9,
    "september": 9,
    "oct": 10,
    "octubre": 10,
    "october": 10,
    "nov": 11,
    "noviembre": 11,
    "november": 11,
    "dic": 12,
    "diciembre": 12,
    "dec": 12,
    "december": 12,
}


def _strip_accents(text: object) -> str:
    out = str(text).strip().lower()
    out = unicodedata.normalize("NFKD", out).encode("ascii", "ignore").decode("ascii")
    return out


def parse_month_name(value: object) -> int:
    """Parse Spanish/English month labels or numeric month values into 1-12."""
    if pd.isna(value):
        raise MonthParseError("month value is missing")

    if isinstance(value, (int, np.integer)) and 1 <= int(value) <= 12:
        return int(value)
    if isinstance(value, float) and value.is_integer() and 1 <= int(value) <= 12:
        return int(value)

    text = _strip_accents(value)
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    if text.isdigit() and 1 <= int(text) <= 12:
        return int(text)

    first_token = text.split()[0] if text else ""
    if text in SPANISH_MONTHS:
        return SPANISH_MONTHS[text]
    if first_token in SPANISH_MONTHS:
        return SPANISH_MONTHS[first_token]

    raise MonthParseError(f"could not parse month value: {value!r}")


def coerce_numeric_series(series: pd.Series) -> pd.Series:
    """Coerce Spanish/English formatted numeric text into floats.

    Handles values like ``"1,234.56"``, ``"1.234,56"``, ``"Q 1,234"`` and blanks.
    """
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    cleaned = series.astype(str).str.strip()
    cleaned = cleaned.replace({"": np.nan, "nan": np.nan, "None": np.nan, "-": np.nan})
    cleaned = cleaned.str.replace(r"[^0-9,\.\-]", "", regex=True)

    def parse_one(value: object) -> float | np.nan:
        if pd.isna(value):
            return np.nan
        text = str(value)
        if not text:
            return np.nan
        # If both separators exist, infer decimal separator from the last one.
        if "," in text and "." in text:
            if text.rfind(",") > text.rfind("."):
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", "")
        elif "," in text:
            # Treat comma as decimal only when there are one or two decimals.
            parts = text.split(",")
            if len(parts[-1]) in {1, 2}:
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", "")
        try:
            return float(text)
        except ValueError:
            return np.nan

    return cleaned.map(parse_one)


def build_monthly_date(
    df: pd.DataFrame,
    *,
    year_col: str | None = None,
    month_col: str | None = None,
    date_col: str | None = None,
) -> pd.Series:
    """Build month-start dates from date or year/month columns."""
    if date_col and date_col in df.columns:
        dates = pd.to_datetime(df[date_col], errors="coerce")
        if dates.notna().any():
            return dates.dt.to_period("M").dt.to_timestamp()

    if not year_col or not month_col or year_col not in df.columns or month_col not in df.columns:
        raise MonthParseError("need either a date column or both year and month columns")

    years = coerce_numeric_series(df[year_col]).astype("Int64")
    months = df[month_col].map(lambda value: parse_month_name(value) if pd.notna(value) else pd.NA).astype(
        "Int64"
    )

    out = []
    for year, month in zip(years, months):
        if pd.isna(year) or pd.isna(month):
            out.append(pd.NaT)
        else:
            out.append(pd.Timestamp(year=int(year), month=int(month), day=1))
    return pd.Series(out, index=df.index, dtype="datetime64[ns]")


def find_first_matching_column(columns: Iterable[str], patterns: Iterable[str]) -> str | None:
    """Return the first normalized column name matching one of the regex patterns."""
    for column in columns:
        normalized = normalize_column_name(column)
        for pattern in patterns:
            if re.search(pattern, normalized):
                return column
    return None


def standardize_monthly_frame(
    df: pd.DataFrame,
    *,
    value_columns: dict[str, str],
    date_col: str | None = None,
    year_col: str | None = None,
    month_col: str | None = None,
) -> pd.DataFrame:
    """Return a canonical monthly dataframe with a ``date`` column.

    Parameters
    ----------
    value_columns:
        Mapping of source column name -> output column name.
    """
    out = normalize_columns(df)
    normalized_value_columns = {
        normalize_column_name(source): normalize_column_name(destination)
        for source, destination in value_columns.items()
    }

    normalized_date_col = normalize_column_name(date_col) if date_col else None
    normalized_year_col = normalize_column_name(year_col) if year_col else None
    normalized_month_col = normalize_column_name(month_col) if month_col else None

    out["date"] = build_monthly_date(
        out,
        date_col=normalized_date_col,
        year_col=normalized_year_col,
        month_col=normalized_month_col,
    )

    keep_cols = ["date"]
    for source, destination in normalized_value_columns.items():
        if source not in out.columns:
            continue
        out[destination] = coerce_numeric_series(out[source])
        keep_cols.append(destination)

    out = out[keep_cols].dropna(subset=["date"])
    value_cols = [col for col in keep_cols if col != "date"]
    if value_cols:
        out = out.groupby("date", as_index=False)[value_cols].sum(min_count=1)
    return ensure_month_start(out, "date")


@dataclass(frozen=True)
class SpreadsheetCandidate:
    """A table candidate found inside an Excel workbook."""

    path: Path
    sheet_name: str
    header_row: int
    rows: int
    columns: int
    column_names: list[str]
    date_like_columns: list[str]
    numeric_like_columns: list[str]
