from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from cement_forecast.cleaning import ensure_month_start
from cement_forecast.config import DATE_COLUMN


@dataclass(frozen=True)
class MonthlyPanelReport:
    """Summary of a strict monthly panel build or validation."""

    start: pd.Timestamp
    end: pd.Timestamp
    expected_months: int
    rows: int
    selected_columns: tuple[str, ...]
    dropped_columns: tuple[str, ...]
    missing_by_column: dict[str, int]

    @property
    def is_complete(self) -> bool:
        return self.rows == self.expected_months and all(self.missing_by_column.get(col, 0) == 0 for col in self.selected_columns)


def _as_month_start(value: str | pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(value).to_period("M").to_timestamp()


def monthly_index(start: str | pd.Timestamp, end: str | pd.Timestamp) -> pd.DatetimeIndex:
    """Return an inclusive monthly-start date index."""
    start_ts = _as_month_start(start)
    end_ts = _as_month_start(end)
    if end_ts < start_ts:
        raise ValueError("end must be greater than or equal to start")
    return pd.date_range(start_ts, end_ts, freq="MS")


def prepare_monthly_frame(df: pd.DataFrame, *, date_col: str = DATE_COLUMN) -> pd.DataFrame:
    """Normalize dates, sort, and aggregate duplicate months by numeric mean.

    Official sources can occasionally produce duplicate months after parsing or
    joining multiple sheets. For strict panel construction, one row per month is
    required. Non-numeric columns are ignored because this project models numeric
    time-series indicators.
    """
    if date_col not in df.columns:
        raise ValueError(f"Input dataframe must contain {date_col!r}")

    out = ensure_month_start(df, date_col).copy()
    numeric_cols = [col for col in out.columns if col != date_col and pd.api.types.is_numeric_dtype(pd.to_numeric(out[col], errors="coerce"))]
    if not numeric_cols:
        raise ValueError("No numeric series columns were found")

    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    grouped = out[[date_col, *numeric_cols]].groupby(date_col, as_index=False).mean(numeric_only=True)
    return grouped.sort_values(date_col).reset_index(drop=True)


def build_strict_monthly_panel(
    df: pd.DataFrame,
    *,
    start: str | pd.Timestamp = "2019-01-01",
    end: str | pd.Timestamp | None = None,
    columns: Iterable[str] | None = None,
    required_columns: Iterable[str] | None = None,
    drop_incomplete_columns: bool = True,
    date_col: str = DATE_COLUMN,
) -> tuple[pd.DataFrame, MonthlyPanelReport]:
    """Build a complete monthly panel with no missing values.

    Parameters
    ----------
    df:
        Input dataframe containing a monthly date column and numeric series.
    start, end:
        Inclusive monthly panel bounds. If ``end`` is omitted, the latest
        available month in the input is used.
    columns:
        Optional candidate columns. If omitted, all numeric columns are candidates.
    required_columns:
        Columns that must be present and complete. If any required column has
        missing values in the selected period, the function raises ``ValueError``.
    drop_incomplete_columns:
        If True, non-required incomplete columns are dropped. If False, any
        missing value in a selected column raises ``ValueError``.
    """
    prepared = prepare_monthly_frame(df, date_col=date_col)
    if end is None:
        end = prepared[date_col].max()
    idx = monthly_index(start, end)

    numeric_cols = [col for col in prepared.columns if col != date_col]
    if columns is None:
        candidate_cols = numeric_cols
    else:
        candidate_cols = list(columns)

    required = list(required_columns or [])
    missing_required = [col for col in required if col not in prepared.columns]
    if missing_required:
        raise ValueError(f"Required columns are missing from input data: {missing_required}")

    missing_candidates = [col for col in candidate_cols if col not in prepared.columns]
    if missing_candidates:
        raise ValueError(f"Requested columns are missing from input data: {missing_candidates}")

    # Required columns are always considered candidates.
    candidate_cols = list(dict.fromkeys([*candidate_cols, *required]))

    panel = prepared.set_index(date_col).reindex(idx)
    panel.index.name = date_col

    missing_by_column = {col: int(panel[col].isna().sum()) for col in candidate_cols}
    incomplete_cols = [col for col, missing in missing_by_column.items() if missing > 0]

    required_incomplete = [col for col in required if missing_by_column.get(col, 0) > 0]
    if required_incomplete:
        details = {col: missing_by_column[col] for col in required_incomplete}
        raise ValueError(f"Required columns are not complete over the panel period: {details}")

    if incomplete_cols and not drop_incomplete_columns:
        details = {col: missing_by_column[col] for col in incomplete_cols}
        raise ValueError(f"Selected columns contain missing values over the panel period: {details}")

    if drop_incomplete_columns:
        selected_cols = [col for col in candidate_cols if missing_by_column[col] == 0]
        dropped_cols = [col for col in candidate_cols if missing_by_column[col] > 0]
    else:
        selected_cols = candidate_cols
        dropped_cols = []

    if not selected_cols:
        raise ValueError("No complete numeric columns are available for the selected monthly period")

    out = panel[selected_cols].reset_index()
    report = MonthlyPanelReport(
        start=idx[0],
        end=idx[-1],
        expected_months=len(idx),
        rows=len(out),
        selected_columns=tuple(selected_cols),
        dropped_columns=tuple(dropped_cols),
        missing_by_column=missing_by_column,
    )
    validate_complete_monthly_panel(out, start=idx[0], end=idx[-1], date_col=date_col)
    return out, report


def validate_complete_monthly_panel(
    df: pd.DataFrame,
    *,
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
    date_col: str = DATE_COLUMN,
) -> None:
    """Raise if a dataframe is not an aligned complete monthly panel."""
    if date_col not in df.columns:
        raise ValueError(f"Panel must contain {date_col!r}")

    expected = monthly_index(start, end)
    dates = pd.to_datetime(df[date_col]).dt.to_period("M").dt.to_timestamp()
    observed = pd.DatetimeIndex(dates)

    if len(observed) != len(expected):
        raise ValueError(f"Panel has {len(observed)} rows but expected {len(expected)} monthly rows")
    if not observed.equals(expected):
        missing_months = expected.difference(observed)
        extra_months = observed.difference(expected)
        raise ValueError(
            "Panel dates are not the expected continuous monthly sequence. "
            f"Missing months: {[d.strftime('%Y-%m-%d') for d in missing_months[:10]]}; "
            f"extra months: {[d.strftime('%Y-%m-%d') for d in extra_months[:10]]}"
        )

    missing = df.drop(columns=[date_col]).isna().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        raise ValueError(f"Panel contains missing values: {missing.to_dict()}")


def write_monthly_panel_report(report: MonthlyPanelReport, output_path: str | Path) -> None:
    """Write a markdown report for GitHub/review."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    selected = "\n".join(f"- `{col}`" for col in report.selected_columns)
    dropped = "\n".join(f"- `{col}`: {report.missing_by_column[col]} missing month(s)" for col in report.dropped_columns)
    if not dropped:
        dropped = "- None"

    text = f"""# Strict Monthly Panel Report

This report validates the modeling panel used for forecasting experiments.

## Period

- Start: `{report.start.strftime('%Y-%m-%d')}`
- End: `{report.end.strftime('%Y-%m-%d')}`
- Expected monthly rows: `{report.expected_months}`
- Actual rows: `{report.rows}`
- Complete panel: `{report.is_complete}`

## Selected complete columns

{selected}

## Dropped incomplete columns

{dropped}

## Methodological rule

The main modeling panel must be monthly, recent, aligned, and free of missing values. Sparse or lower-frequency variables can be documented separately, but they should not be used in the primary forecasting experiments until a complete aligned series is available.
"""
    output.write_text(text, encoding="utf-8")
