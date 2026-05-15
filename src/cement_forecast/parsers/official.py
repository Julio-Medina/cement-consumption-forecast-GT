from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from cement_forecast.cleaning import aggregate_quarterly_to_monthly, ensure_month_start, normalize_column_name, normalize_columns
from cement_forecast.parsers.common import coerce_numeric_series, parse_month_name
from cement_forecast.parsers.generic import parse_generic_monthly_table

YEAR_RE = re.compile(r"(19|20)\d{2}")


def _extract_year(value: object) -> int | None:
    """Extract a 4-digit year from an Excel header/cell value."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)) and not pd.isna(value):
        year = int(value)
        return year if 1900 <= year <= 2100 else None
    match = YEAR_RE.search(str(value))
    return int(match.group(0)) if match else None


def _first_existing_column(columns: list[str], candidates: list[str]) -> str | None:
    normalized_lookup = {normalize_column_name(column): column for column in columns}
    for candidate in candidates:
        normalized = normalize_column_name(candidate)
        if normalized in normalized_lookup:
            return normalized_lookup[normalized]
    return None


def _safe_parse_month(value: object) -> int | None:
    """Parse month labels and return None for summary rows such as Total."""
    try:
        return parse_month_name(value)
    except Exception:
        return None


def parse_banguat_remittances(
    path: str | Path,
    *,
    sheet_name: str | int | None = "2002-2021",
    header_row: int = 9,
) -> pd.DataFrame:
    """Parse Banguat's wide monthly remittances workbook.

    The source is arranged as month rows and year columns. The parser converts it
    into a long monthly table:

    ``date, remittances_usd_millions``
    """
    df = pd.read_excel(path, sheet_name=sheet_name, header=header_row)
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    df.columns = [normalize_column_name(column) for column in df.columns]

    month_col = _first_existing_column(list(df.columns), ["mes", "month"])
    if month_col is None:
        # Fall back to the first column because Banguat's file uses month labels
        # as row headers.
        month_col = df.columns[0]

    year_cols = [column for column in df.columns if _extract_year(column) is not None]
    if not year_cols:
        raise ValueError("No year columns were found in the Banguat remittances file")

    long = df[[month_col] + year_cols].melt(
        id_vars=month_col,
        value_vars=year_cols,
        var_name="year",
        value_name="remittances_usd_millions",
    )
    long["month"] = long[month_col].map(_safe_parse_month)
    long = long.dropna(subset=["month"]).copy()
    long["year"] = long["year"].map(_extract_year)
    long["remittances_usd_millions"] = coerce_numeric_series(long["remittances_usd_millions"])
    long["date"] = pd.to_datetime(
        dict(year=long["year"].astype("Int64"), month=long["month"].astype("Int64"), day=1),
        errors="coerce",
    )

    out = long[["date", "remittances_usd_millions"]].dropna(subset=["date"])
    out = out.groupby("date", as_index=False).sum(min_count=1)
    return ensure_month_start(out, "date")


def parse_ine_construction(
    path: str | Path,
    *,
    sheet_name: str | int | None = "Hoja1",
    header_row: int = 0,
) -> pd.DataFrame:
    """Parse INE ``Construcciones Particulares`` quarterly data.

    The raw table contains department/municipality rows. This parser aggregates
    all geographic rows by year-quarter and spreads each quarterly total evenly
    across its three months so it can be joined with monthly macro indicators.
    """
    df = pd.read_excel(path, sheet_name=sheet_name, header=header_row)
    df = normalize_columns(df.dropna(axis=0, how="all").dropna(axis=1, how="all"))

    required = ["ano", "trimestre"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required INE construction columns: {missing}")

    rename_map = {
        "num_construcciones": "construction_num_constructions",
        "area_con_m2": "construction_area_m2",
        "area_m2": "construction_area_m2",
        "costo_aprox_quetzales": "construction_cost_gtq",
        "costo_aproximado_quetzales": "construction_cost_gtq",
    }

    value_cols = []
    for source, destination in rename_map.items():
        if source in df.columns:
            df[destination] = coerce_numeric_series(df[source])
            value_cols.append(destination)

    if not value_cols:
        raise ValueError("No construction value columns were found")

    df["ano"] = coerce_numeric_series(df["ano"]).astype("Int64")
    df["trimestre"] = coerce_numeric_series(df["trimestre"]).astype("Int64")
    quarterly = (
        df.dropna(subset=["ano", "trimestre"])
        .groupby(["ano", "trimestre"], as_index=False)[value_cols]
        .sum(min_count=1)
    )

    monthly = aggregate_quarterly_to_monthly(
        quarterly,
        year_col="ano",
        quarter_col="trimestre",
        value_cols=value_cols,
    )
    return ensure_month_start(monthly, "date")


def parse_ine_ipmc(
    path: str | Path,
    *,
    sheet_name: str | int | None = "Publicación Histórico 2026",
    header_row: int = 0,
    material_keywords: list[str] | None = None,
) -> pd.DataFrame:
    """Parse INE IPMC historical wide table into monthly material indices.

    The IPMC workbook uses a two-row time header: one row for year blocks and one
    row for month names. Data rows contain construction materials. By default this
    parser keeps cement/concrete/agglomerate-related rows and returns both a wide
    set of material index columns and an average ``ipmc_cement_related_index``.
    """
    material_keywords = material_keywords or [
        "cemento",
        "cement",
        "concreto",
        "hormigon",
        "mortero",
        "cal",
        "agregado",
        "aglomerante",
    ]

    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    raw = raw.dropna(axis=0, how="all").dropna(axis=1, how="all")
    if raw.shape[0] < 4 or raw.shape[1] < 4:
        raise ValueError("The IPMC workbook does not look like the expected wide historical table")

    year_header = raw.iloc[header_row].ffill()
    month_header = raw.iloc[header_row + 1]
    data = raw.iloc[header_row + 2 :].copy()

    # The first columns are usually: No., Material, Base index. Column 1 is the
    # safest material-name column according to the inventory.
    material_col = data.columns[1]
    data["material_name"] = data[material_col].astype(str)
    data["material_slug"] = data["material_name"].map(normalize_column_name)

    keyword_slugs = [normalize_column_name(keyword) for keyword in material_keywords]
    mask = data["material_slug"].apply(lambda text: any(keyword in text for keyword in keyword_slugs))
    data = data.loc[mask].copy()
    if data.empty:
        raise ValueError("No IPMC material rows matched the selected keywords")

    records: list[dict[str, object]] = []
    for column in data.columns:
        if not isinstance(column, int) or column < 3:
            continue
        year = _extract_year(year_header.iloc[column])
        if year is None:
            continue
        try:
            month = parse_month_name(month_header.iloc[column])
        except Exception:
            continue
        date = pd.Timestamp(year=year, month=month, day=1)
        for _, row in data.iterrows():
            value = coerce_numeric_series(pd.Series([row[column]])).iloc[0]
            if pd.isna(value):
                continue
            records.append(
                {
                    "date": date,
                    "material_slug": row["material_slug"],
                    "ipmc_index": value,
                }
            )

    if not records:
        raise ValueError("No monthly IPMC observations could be parsed")

    long = pd.DataFrame(records)
    wide = long.pivot_table(index="date", columns="material_slug", values="ipmc_index", aggfunc="mean")
    wide.columns = [f"ipmc_{column}_index" for column in wide.columns]
    wide = wide.reset_index()
    ipmc_cols = [column for column in wide.columns if column != "date"]
    wide["ipmc_cement_related_index"] = wide[ipmc_cols].mean(axis=1, skipna=True)
    return ensure_month_start(wide, "date")


def parse_banguat_trade_by_product(
    path: str | Path,
    *,
    sheet_name: str | int | None = "Informe 1",
    header_row: int = 7,
) -> pd.DataFrame:
    """Parse Banguat trade-by-product tables when they are already monthly-long.

    The current downloaded file appears to have multi-row export/import headers
    and only a few months for 2026. Until we inspect the full workbook manually,
    this parser falls back to the generic monthly parser. Treat this as provisional.
    """
    return parse_generic_monthly_table(
        path,
        output_prefix="trade",
        sheet_name=sheet_name,
        header_row=header_row,
        include_keywords=["cement", "valor", "volumen", "peso", "kg", "ton", "import", "export"],
    )
