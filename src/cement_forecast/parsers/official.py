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


def _find_row_containing(raw: pd.DataFrame, value: str) -> int | None:
    """Return the first row index containing a case-insensitive text value."""
    needle = normalize_column_name(value)
    for row_idx, row in raw.iterrows():
        normalized_cells = [normalize_column_name(cell) for cell in row.dropna().astype(str).tolist()]
        if any(needle in cell for cell in normalized_cells):
            return int(row_idx)
    return None


def _looks_like_imae_component_sheet(raw: pd.DataFrame) -> bool:
    """Return True when a sheet appears to contain IMAE component tables."""
    normalized_values = " ".join(
        normalize_column_name(value)
        for value in raw.astype(str).replace("nan", "").to_numpy().ravel().tolist()
        if str(value).strip() and str(value).lower() != "nan"
    )
    return (
        "periodo" in normalized_values
        and "construccion" in normalized_values
        and "imae" in normalized_values
    )


def _resolve_imae_sheet_name(path: str | Path, requested_sheet: str | int | None) -> str | int | None:
    """Resolve Banguat IMAE sheet names across workbook versions.

    Older Banguat workbooks use ``IMAE componentes``. Current workbooks may use
    different names, so this helper first honors an existing requested sheet and
    otherwise scans non-chart sheets for the IMAE component table header.
    """
    if requested_sheet is None or isinstance(requested_sheet, int):
        return requested_sheet

    excel = pd.ExcelFile(path)
    if requested_sheet in excel.sheet_names:
        return requested_sheet

    candidate_sheets = [
        sheet for sheet in excel.sheet_names if "graf" not in normalize_column_name(sheet)
    ] or excel.sheet_names

    for sheet in candidate_sheets:
        try:
            preview = pd.read_excel(path, sheet_name=sheet, header=None, nrows=20)
        except Exception:
            continue
        if _looks_like_imae_component_sheet(preview):
            return sheet

    available = ", ".join(str(sheet) for sheet in excel.sheet_names)
    raise ValueError(
        f"Worksheet named {requested_sheet!r} was not found and no IMAE component sheet "
        f"could be auto-detected. Available sheets: {available}"
    )


def _strict_monthly_date_series(values: pd.Series) -> pd.Series:
    """Parse monthly dates without treating ordinary numeric values as dates.

    Pandas will happily convert small numbers to timestamps around 1970 when
    ``pd.to_datetime`` is applied blindly. Banguat IMAE workbooks contain several
    side-by-side numeric tables, so this helper only accepts real datetimes,
    Excel serial dates in a plausible range, or strings that look like dates.
    """
    parsed: list[pd.Timestamp | pd.NaT] = []
    for value in values:
        if pd.isna(value):
            parsed.append(pd.NaT)
            continue

        if isinstance(value, pd.Timestamp):
            parsed.append(value)
            continue

        # Excel serial dates for 2001-2026 are roughly in the 36k-47k range.
        # Keep this path conservative so indicator values like 120.5 are not
        # converted to 1970 timestamps.
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if 30000 <= float(value) <= 60000:
                parsed.append(pd.Timestamp("1899-12-30") + pd.to_timedelta(float(value), unit="D"))
            else:
                parsed.append(pd.NaT)
            continue

        text_value = str(value).strip()
        if not text_value:
            parsed.append(pd.NaT)
            continue

        # Accept ISO-like dates and common slash-separated dates; reject pure
        # numeric strings because they are usually indicator values, not periods.
        if not any(separator in text_value for separator in ("-", "/")):
            parsed.append(pd.NaT)
            continue

        parsed.append(pd.to_datetime(text_value, errors="coerce"))

    out = pd.Series(parsed, index=values.index)
    out = out.where(out.dt.year.between(1900, 2100))
    return out


def _imae_block_suffix(raw: pd.DataFrame, *, start_col: int, header_row: int) -> str:
    """Infer the output suffix for an IMAE side-by-side table block."""
    title_region = raw.iloc[:header_row, start_col : start_col + 15]
    title_text = " ".join(
        normalize_column_name(value)
        for value in title_region.astype(str).replace("nan", "").to_numpy().ravel().tolist()
        if str(value).strip() and str(value).lower() != "nan"
    )
    has_trend = "tendencia" in title_text or "ciclo" in title_text
    has_yoy = "interanual" in title_text or "variacion" in title_text or "variaciones" in title_text
    if has_trend and has_yoy:
        return "trend_yoy"
    if has_trend:
        return "trend_index"
    if has_yoy:
        return "yoy"
    return "index"


def _candidate_imae_blocks(raw: pd.DataFrame, preferred_header_row: int) -> list[tuple[int, int, str]]:
    """Find IMAE component blocks as (header_row, start_col, suffix).

    Real Banguat workbooks usually identify side-by-side blocks through title
    rows such as original index, year-over-year variation, trend-cycle index,
    and trend-cycle year-over-year variation. Small unit-test workbooks may
    omit those title rows, so when several component blocks are found but the
    suffix inference is ambiguous, we fall back to the conventional block order.
    """
    fallback_suffixes = ["index", "yoy", "trend_index", "trend_yoy"]

    candidate_rows: list[int] = []
    rows_to_scan = list(range(min(len(raw), 40)))
    if 0 <= preferred_header_row < len(raw):
        rows_to_scan = [preferred_header_row] + [row for row in rows_to_scan if row != preferred_header_row]

    for row_idx in rows_to_scan:
        normalized = [normalize_column_name(value) for value in raw.iloc[row_idx].astype(str).tolist()]
        if any("periodo" in value for value in normalized) and any("construccion" in value for value in normalized):
            candidate_rows.append(row_idx)

    blocks: list[tuple[int, int, str]] = []
    seen: set[tuple[int, int]] = set()

    for row_idx in candidate_rows:
        normalized = [normalize_column_name(value) for value in raw.iloc[row_idx].astype(str).tolist()]

        start_cols: list[int] = []
        for col_idx, value in enumerate(normalized):
            if "periodo" not in value:
                continue

            # A valid component block should contain Construcción and IMAE in the
            # nearby header window. This prevents unrelated Periodo columns from
            # being treated as IMAE tables.
            window = normalized[col_idx : col_idx + 20]
            if not any("construccion" in item for item in window):
                continue
            if not any(item == "imae" or item.endswith("_imae") or "imae" == item for item in window):
                continue

            key = (row_idx, col_idx)
            if key in seen:
                continue

            seen.add(key)
            start_cols.append(col_idx)

        if not start_cols:
            continue

        inferred_suffixes = [
            _imae_block_suffix(raw, start_col=start_col, header_row=row_idx)
            for start_col in start_cols
        ]

        # When titles are absent, _imae_block_suffix returns "index" for every
        # block. In that case, preserve the expected Banguat block order.
        ambiguous = len(start_cols) > 1 and len(set(inferred_suffixes)) == 1

        used_suffixes_for_row: set[str] = set()
        for order, start_col in enumerate(start_cols):
            suffix = inferred_suffixes[order]

            if ambiguous or suffix in used_suffixes_for_row:
                if order < len(fallback_suffixes):
                    suffix = fallback_suffixes[order]

            used_suffixes_for_row.add(suffix)
            blocks.append((row_idx, start_col, suffix))

    return blocks


def _parse_imae_component_block(
    raw: pd.DataFrame,
    *,
    start_col: int,
    header_row: int,
    value_suffix: str,
) -> pd.DataFrame:
    """Parse one IMAE component block from Banguat's workbook.

    Only blocks whose first column contains real monthly dates are accepted.
    This prevents numeric indicator columns from being mis-parsed as dates.
    """
    block_width = min(15, raw.shape[1] - start_col)
    if block_width < 2:
        raise ValueError(f"IMAE block starting at column {start_col} is too narrow")

    headers = raw.iloc[header_row, start_col : start_col + block_width].tolist()
    data = raw.iloc[header_row + 1 :, start_col : start_col + block_width].copy()
    data.columns = [normalize_column_name(header) for header in headers]

    period_name = data.columns[0]
    data = data.rename(columns={period_name: "date"})
    data["date"] = _strict_monthly_date_series(data["date"])
    data = data.dropna(subset=["date"])
    data = data.loc[data["date"].dt.year.between(1900, 2100)].copy()

    # Reject blocks with no real dates. Do not require a large minimum number of
    # observations here: unit-test workbooks may contain only one or two rows,
    # while production coverage is validated separately by check_imae_coverage.py
    # and the strict monthly panel workflow.
    if data["date"].nunique() == 0:
        raise ValueError(f"No valid dated IMAE observations found at column {start_col}")

    selected: dict[str, str] = {
        "construccion": f"imae_construction_{value_suffix}",
        "imae": f"imae_general_{value_suffix}",
    }
    out = data[["date"]].copy()
    found = False
    for source_col, output_col in selected.items():
        if source_col in data.columns:
            out[output_col] = coerce_numeric_series(data[source_col])
            found = True
    if not found:
        raise ValueError(
            f"Neither Construcción nor IMAE columns were found in the IMAE block starting at column {start_col}"
        )

    out = ensure_month_start(out, "date")
    value_cols = [column for column in out.columns if column != "date"]
    out = (
        out.groupby("date", as_index=False)[value_cols]
        .mean(numeric_only=True)
        .sort_values("date")
        .reset_index(drop=True)
    )
    return out


def parse_banguat_imae(
    path: str | Path,
    *,
    sheet_name: str | int | None = "IMAE componentes",
    header_row: int = 6,
) -> pd.DataFrame:
    """Parse Banguat IMAE component data.

    The official workbook has component tables that may appear as side-by-side
    blocks. Workbook versions differ, so the parser discovers blocks by finding
    header rows containing both ``Período`` and ``Construcción``. It extracts the
    construction-sector and general IMAE columns when available.
    """
    resolved_sheet = _resolve_imae_sheet_name(path, sheet_name)
    raw = pd.read_excel(path, sheet_name=resolved_sheet, header=None)

    blocks = _candidate_imae_blocks(raw, preferred_header_row=header_row)
    if not blocks:
        detected = _find_row_containing(raw, "Construcción")
        if detected is None:
            raise ValueError("Could not find the IMAE component header row containing 'Construcción'")
        blocks = _candidate_imae_blocks(raw, preferred_header_row=detected)

    frames: list[pd.DataFrame] = []
    used_columns: set[str] = set()
    for block_header_row, start_col, suffix in blocks:
        try:
            frame = _parse_imae_component_block(
                raw,
                start_col=start_col,
                header_row=block_header_row,
                value_suffix=suffix,
            )
        except ValueError:
            continue

        # Avoid duplicate block types when a workbook repeats the same section.
        value_columns = [column for column in frame.columns if column != "date"]
        new_columns = [column for column in value_columns if column not in used_columns]
        if not new_columns:
            continue
        used_columns.update(new_columns)
        frames.append(frame[["date"] + new_columns])

    if not frames:
        raise ValueError("No valid dated IMAE component blocks could be parsed")

    parsed = frames[0]
    for frame in frames[1:]:
        parsed = parsed.merge(frame, on="date", how="outer")

    value_cols = [column for column in parsed.columns if column != "date"]
    parsed[value_cols] = parsed[value_cols].apply(coerce_numeric_series)
    parsed = ensure_month_start(parsed, "date")
    parsed = (
        parsed.groupby("date", as_index=False)[value_cols]
        .mean(numeric_only=True)
        .sort_values("date")
        .reset_index(drop=True)
    )
    return parsed



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

# ---------------------------------------------------------------------------
# Robust Banguat IMAE parser override
# ---------------------------------------------------------------------------
# This final definition intentionally overrides earlier parse_banguat_imae
# versions in this module. It is designed to handle:
# - old workbook sheet name: "IMAE componentes"
# - current workbook sheet names that changed
# - side-by-side IMAE blocks
# - minimal unit-test workbooks with no title rows
# - avoiding numeric cells accidentally parsed as 1970 dates

def _imae_safe_month(value):
    from datetime import date, datetime
    import re
    import pandas as pd

    if pd.isna(value):
        return pd.NaT

    if isinstance(value, pd.Timestamp):
        dt = value
    elif isinstance(value, (datetime, date)):
        dt = pd.Timestamp(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return pd.NaT

        # Accept clear date-like strings only. Avoid converting arbitrary numbers.
        date_like = (
            re.match(r"^\d{4}[-/]\d{1,2}([-/]\d{1,2})?$", text)
            or re.match(r"^\d{1,2}[-/]\d{1,2}[-/]\d{4}$", text)
        )
        if not date_like:
            return pd.NaT

        dt = pd.to_datetime(text, errors="coerce")
    else:
        # Important: do not parse numeric cells as dates.
        return pd.NaT

    if pd.isna(dt):
        return pd.NaT

    dt = pd.Timestamp(dt).to_period("M").to_timestamp()

    # Banguat IMAE is modern monthly data. Reject impossible dates.
    if dt.year < 1990 or dt.year > 2035:
        return pd.NaT

    return dt


def _imae_norm(value) -> str:
    import re
    import unicodedata
    import pandas as pd

    if pd.isna(value):
        return ""

    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _imae_find_component_sheet(path, requested_sheet=None):
    import pandas as pd

    xl = pd.ExcelFile(path)

    if requested_sheet in xl.sheet_names:
        return requested_sheet

    best_sheet = None
    best_score = -1

    for sheet in xl.sheet_names:
        try:
            raw = pd.read_excel(path, sheet_name=sheet, header=None, nrows=80)
        except Exception:
            continue

        values = [_imae_norm(v) for v in raw.to_numpy().ravel()]
        joined = " ".join(values)

        score = 0
        score += joined.count("construccion") * 5
        score += joined.count("periodo") * 3
        score += joined.count("imae") * 2
        score += joined.count("indices") * 1
        score += joined.count("componentes") * 2

        if score > best_score:
            best_score = score
            best_sheet = sheet

    if best_sheet is None or best_score <= 0:
        raise ValueError(
            f"Could not auto-detect IMAE component sheet. Available sheets: {xl.sheet_names}"
        )

    return best_sheet


def _imae_suffix_from_title(raw, header_row: int, start_col: int) -> str:
    pieces = []

    for row in range(max(0, header_row - 6), header_row):
        for col in range(start_col, min(start_col + 16, raw.shape[1])):
            pieces.append(_imae_norm(raw.iat[row, col]))

    title = " ".join(pieces)

    has_trend = "tendencia" in title or "ciclo" in title
    has_yoy = "interanual" in title or "variacion" in title or "variaciones" in title

    if has_trend and has_yoy:
        return "trend_yoy"
    if has_trend:
        return "trend_index"
    if has_yoy:
        return "yoy"
    return "index"


def _imae_candidate_blocks(raw, preferred_header_row: int = 6):
    fallback_suffixes = ["index", "yoy", "trend_index", "trend_yoy"]

    candidate_rows = []
    rows_to_scan = list(range(min(raw.shape[0], 120)))

    if 0 <= preferred_header_row < raw.shape[0]:
        rows_to_scan = [preferred_header_row] + [
            row for row in rows_to_scan if row != preferred_header_row
        ]

    for row_idx in rows_to_scan:
        row_norm = [_imae_norm(v) for v in raw.iloc[row_idx].tolist()]

        if not any("periodo" == v or v.endswith("_periodo") or "periodo" in v for v in row_norm):
            continue
        if not any("construccion" in v for v in row_norm):
            continue

        starts = []
        for col_idx, value in enumerate(row_norm):
            if "periodo" not in value:
                continue

            window = row_norm[col_idx : col_idx + 20]
            if not any("construccion" in item for item in window):
                continue
            if not any(item == "imae" or item.endswith("_imae") or "imae" in item for item in window):
                continue

            starts.append(col_idx)

        if not starts:
            continue

        inferred = [
            _imae_suffix_from_title(raw, header_row=row_idx, start_col=start)
            for start in starts
        ]

        ambiguous = len(starts) > 1 and len(set(inferred)) == 1

        blocks = []
        used = set()
        for order, start in enumerate(starts):
            suffix = inferred[order]

            if ambiguous or suffix in used:
                if order < len(fallback_suffixes):
                    suffix = fallback_suffixes[order]

            used.add(suffix)
            blocks.append((row_idx, start, suffix))

        return blocks

    return []


def _imae_parse_block(raw, header_row: int, start_col: int, suffix: str):
    import pandas as pd

    row_norm = [_imae_norm(v) for v in raw.iloc[header_row].tolist()]
    window = row_norm[start_col : min(start_col + 20, raw.shape[1])]

    rel_construction = None
    rel_general = None

    for rel, name in enumerate(window):
        if rel_construction is None and "construccion" in name:
            rel_construction = rel

        # Usually the general IMAE column is exactly "IMAE" and appears near the end.
        if name == "imae" or name.endswith("_imae"):
            rel_general = rel

    if rel_construction is None:
        raise ValueError("Construction column not found in IMAE block")

    date_col = start_col
    construction_col = start_col + rel_construction
    general_col = start_col + rel_general if rel_general is not None else None

    data = raw.iloc[header_row + 1 :].copy()
    dates = data.iloc[:, date_col].map(_imae_safe_month)

    parsed = pd.DataFrame({"date": dates})
    parsed = parsed[parsed["date"].notna()].copy()

    if parsed.empty:
        raise ValueError("No valid dated IMAE observations found")

    if suffix == "index":
        construction_name = "imae_construction_index"
        general_name = "imae_general_index"
    elif suffix == "yoy":
        construction_name = "imae_construction_yoy"
        general_name = "imae_general_yoy"
    elif suffix == "trend_index":
        construction_name = "imae_construction_trend_index"
        general_name = "imae_general_trend_index"
    elif suffix == "trend_yoy":
        construction_name = "imae_construction_trend_yoy"
        general_name = "imae_general_trend_yoy"
    else:
        raise ValueError(f"Unknown IMAE suffix: {suffix}")

    values = raw.iloc[header_row + 1 :, construction_col]
    parsed[construction_name] = pd.to_numeric(values.loc[parsed.index], errors="coerce")

    if general_col is not None:
        values = raw.iloc[header_row + 1 :, general_col]
        parsed[general_name] = pd.to_numeric(values.loc[parsed.index], errors="coerce")

    parsed = parsed.dropna(subset=[construction_name], how="all")
    parsed = parsed.groupby("date", as_index=False).first()
    return parsed


def parse_banguat_imae(
    path,
    *,
    sheet_name="IMAE componentes",
    header_row: int = 6,
):
    """Robust parser for Banguat IMAE component workbooks.

    Returns monthly columns such as:
    - imae_construction_index
    - imae_general_index
    - imae_construction_yoy
    - imae_general_yoy
    - imae_construction_trend_index
    - imae_general_trend_index
    - imae_construction_trend_yoy
    - imae_general_trend_yoy
    """
    import pandas as pd
    from functools import reduce

    resolved_sheet = _imae_find_component_sheet(path, requested_sheet=sheet_name)
    raw = pd.read_excel(path, sheet_name=resolved_sheet, header=None)

    blocks = _imae_candidate_blocks(raw, preferred_header_row=header_row)

    if not blocks:
        raise ValueError(
            f"No IMAE component blocks found in sheet {resolved_sheet!r}. "
            "Expected a header row containing Periodo, Construcción, and IMAE."
        )

    frames = []
    for block_header_row, start_col, suffix in blocks:
        try:
            frame = _imae_parse_block(
                raw,
                header_row=block_header_row,
                start_col=start_col,
                suffix=suffix,
            )
        except ValueError:
            continue

        frames.append(frame)

    if not frames:
        raise ValueError("No valid dated IMAE component blocks could be parsed")

    result = reduce(lambda left, right: pd.merge(left, right, on="date", how="outer"), frames)
    result = result.groupby("date", as_index=False).first()
    result = result.sort_values("date").reset_index(drop=True)

    # Keep only plausible monthly dates.
    result = result[(result["date"].dt.year >= 1990) & (result["date"].dt.year <= 2035)]
    result = result.reset_index(drop=True)

    return result

# ---------------------------------------------------------------------------
# Final Banguat IMAE parser override for current 2013-reference workbook
# ---------------------------------------------------------------------------
# Handles current workbook layout with sheets C.1 and C.2:
# - C.1: aggregate IMAE original/trend series
# - C.2: component IMAE original and YoY series
# Also keeps a fallback for older "IMAE componentes" style test fixtures.

def _final_imae_norm(value) -> str:
    import re
    import unicodedata
    import pandas as pd

    if pd.isna(value):
        return ""

    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _final_imae_safe_month(value):
    from datetime import date, datetime
    import re
    import pandas as pd

    if pd.isna(value):
        return pd.NaT

    if isinstance(value, pd.Timestamp):
        dt = value
    elif isinstance(value, (datetime, date)):
        dt = pd.Timestamp(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return pd.NaT

        if not (
            re.match(r"^\d{4}[-/]\d{1,2}([-/]\d{1,2})?$", text)
            or re.match(r"^\d{1,2}[-/]\d{1,2}[-/]\d{4}$", text)
        ):
            return pd.NaT

        dt = pd.to_datetime(text, errors="coerce")
    else:
        # Critical: never parse arbitrary numeric cells as dates.
        return pd.NaT

    if pd.isna(dt):
        return pd.NaT

    dt = pd.Timestamp(dt).to_period("M").to_timestamp()

    if dt.year < 1990 or dt.year > 2035:
        return pd.NaT

    return dt


def _final_parse_c1_aggregate_imae(path):
    import pandas as pd

    raw = pd.read_excel(path, sheet_name="C.1", header=None)

    date_col = 0
    first_data_row = None

    for row_idx in range(len(raw)):
        candidate = _final_imae_safe_month(raw.iat[row_idx, date_col])
        if pd.notna(candidate):
            first_data_row = row_idx
            break

    if first_data_row is None:
        return pd.DataFrame(columns=["date"])

    data = raw.iloc[first_data_row:].copy()
    dates = data.iloc[:, date_col].map(_final_imae_safe_month)

    result = pd.DataFrame({"date": dates})
    result = result[result["date"].notna()].copy()

    if result.empty:
        return pd.DataFrame(columns=["date"])

    # Current C.1 layout:
    # col 1 = original index
    # col 2 = original YoY
    # col 3 = trend-cycle index
    # col 4 = trend-cycle YoY
    column_map = {
        1: "imae_general_index",
        2: "imae_general_yoy",
        3: "imae_general_trend_index",
        4: "imae_general_trend_yoy",
    }

    for col_idx, name in column_map.items():
        if col_idx < raw.shape[1]:
            values = pd.to_numeric(data.iloc[:, col_idx], errors="coerce")
            result[name] = values.loc[result.index]

    result = result.groupby("date", as_index=False).first()
    return result.sort_values("date").reset_index(drop=True)


def _final_parse_c2_component_imae(path):
    import pandas as pd
    from functools import reduce

    raw = pd.read_excel(path, sheet_name="C.2", header=None)

    # In current C.2:
    # row 6 has "Período", A, B, C, ..., IMAE
    # row 7 has component names, including "Construcción"
    period_starts = []
    for col_idx in range(raw.shape[1]):
        if "periodo" in _final_imae_norm(raw.iat[6, col_idx]):
            period_starts.append(col_idx)

    frames = []

    for order, start_col in enumerate(period_starts):
        next_start = period_starts[order + 1] if order + 1 < len(period_starts) else raw.shape[1]
        end_col = min(next_start, start_col + 25)

        title_text = " ".join(
            _final_imae_norm(raw.iat[row_idx, col_idx])
            for row_idx in range(0, min(6, raw.shape[0]))
            for col_idx in range(start_col, end_col)
        )

        if "variacion" in title_text or "interanual" in title_text:
            suffix = "yoy"
        else:
            suffix = "index"

        header_row_code = [_final_imae_norm(v) for v in raw.iloc[6, start_col:end_col].tolist()]
        header_row_names = [_final_imae_norm(v) for v in raw.iloc[7, start_col:end_col].tolist()]

        construction_rel = None
        general_rel = None

        for rel, name in enumerate(header_row_names):
            if construction_rel is None and "construccion" in name:
                construction_rel = rel

        for rel, name in enumerate(header_row_code):
            if name == "imae" or name.endswith("_imae") or "imae" == name:
                general_rel = rel

        if construction_rel is None:
            continue

        date_col = start_col
        construction_col = start_col + construction_rel
        general_col = start_col + general_rel if general_rel is not None else None

        data = raw.iloc[8:].copy()
        dates = data.iloc[:, date_col].map(_final_imae_safe_month)

        frame = pd.DataFrame({"date": dates})
        frame = frame[frame["date"].notna()].copy()

        if frame.empty:
            continue

        if suffix == "index":
            construction_name = "imae_construction_index"
            general_name = "imae_general_index"
        else:
            construction_name = "imae_construction_yoy"
            general_name = "imae_general_yoy"

        construction_values = pd.to_numeric(data.iloc[:, construction_col], errors="coerce")
        frame[construction_name] = construction_values.loc[frame.index]

        if general_col is not None:
            general_values = pd.to_numeric(data.iloc[:, general_col], errors="coerce")
            frame[general_name] = general_values.loc[frame.index]

        frame = frame.dropna(subset=[construction_name], how="all")
        frame = frame.groupby("date", as_index=False).first()
        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=["date"])

    result = reduce(lambda left, right: pd.merge(left, right, on="date", how="outer"), frames)
    result = result.groupby("date", as_index=False).first()
    return result.sort_values("date").reset_index(drop=True)


def _final_parse_old_component_layout(path, sheet_name="IMAE componentes", header_row: int = 6):
    import pandas as pd
    from functools import reduce

    xl = pd.ExcelFile(path)

    if sheet_name not in xl.sheet_names:
        # Auto-detect a sheet containing the old-style component table.
        candidate_sheet = None
        for sheet in xl.sheet_names:
            sample = pd.read_excel(path, sheet_name=sheet, header=None, nrows=80)
            text = " ".join(_final_imae_norm(v) for v in sample.to_numpy().ravel())
            if "periodo" in text and "construccion" in text and "imae" in text:
                candidate_sheet = sheet
                break

        if candidate_sheet is None:
            return pd.DataFrame(columns=["date"])

        sheet_name = candidate_sheet

    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)

    fallback_suffixes = ["index", "yoy", "trend_index", "trend_yoy"]

    starts = []
    for col_idx in range(raw.shape[1]):
        if "periodo" not in _final_imae_norm(raw.iat[header_row, col_idx]):
            continue

        window = [
            _final_imae_norm(v)
            for v in raw.iloc[header_row, col_idx : min(col_idx + 20, raw.shape[1])].tolist()
        ]

        if any("construccion" in v for v in window) and any(v == "imae" or v.endswith("_imae") for v in window):
            starts.append(col_idx)

    frames = []

    for order, start_col in enumerate(starts):
        suffix = fallback_suffixes[order] if order < len(fallback_suffixes) else "index"

        end_col = starts[order + 1] if order + 1 < len(starts) else min(start_col + 20, raw.shape[1])
        header = [_final_imae_norm(v) for v in raw.iloc[header_row, start_col:end_col].tolist()]

        construction_rel = None
        general_rel = None

        for rel, name in enumerate(header):
            if construction_rel is None and "construccion" in name:
                construction_rel = rel
            if name == "imae" or name.endswith("_imae"):
                general_rel = rel

        if construction_rel is None:
            continue

        data = raw.iloc[header_row + 1:].copy()
        dates = data.iloc[:, start_col].map(_final_imae_safe_month)

        frame = pd.DataFrame({"date": dates})
        frame = frame[frame["date"].notna()].copy()

        if frame.empty:
            continue

        if suffix == "index":
            construction_name = "imae_construction_index"
            general_name = "imae_general_index"
        elif suffix == "yoy":
            construction_name = "imae_construction_yoy"
            general_name = "imae_general_yoy"
        elif suffix == "trend_index":
            construction_name = "imae_construction_trend_index"
            general_name = "imae_general_trend_index"
        else:
            construction_name = "imae_construction_trend_yoy"
            general_name = "imae_general_trend_yoy"

        construction_values = pd.to_numeric(data.iloc[:, start_col + construction_rel], errors="coerce")
        frame[construction_name] = construction_values.loc[frame.index]

        if general_rel is not None:
            general_values = pd.to_numeric(data.iloc[:, start_col + general_rel], errors="coerce")
            frame[general_name] = general_values.loc[frame.index]

        frame = frame.dropna(subset=[construction_name], how="all")
        frame = frame.groupby("date", as_index=False).first()
        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=["date"])

    result = reduce(lambda left, right: pd.merge(left, right, on="date", how="outer"), frames)
    result = result.groupby("date", as_index=False).first()
    return result.sort_values("date").reset_index(drop=True)


def parse_banguat_imae(
    path,
    *,
    sheet_name="IMAE componentes",
    header_row: int = 6,
):
    """Parse Banguat IMAE data from either current C.1/C.2 workbook or old layout.

    Current 2013-reference workbook:
    - C.1 contains aggregate IMAE original/trend series.
    - C.2 contains IMAE by economic component, including Construcción.

    Older workbook/test layout:
    - IMAE componentes contains side-by-side component blocks.
    """
    import pandas as pd
    from functools import reduce

    xl = pd.ExcelFile(path)

    frames = []

    if "C.2" in xl.sheet_names:
        c2 = _final_parse_c2_component_imae(path)
        if not c2.empty:
            frames.append(c2)

    if "C.1" in xl.sheet_names:
        c1 = _final_parse_c1_aggregate_imae(path)
        if not c1.empty:
            frames.append(c1)

    if not frames:
        old = _final_parse_old_component_layout(path, sheet_name=sheet_name, header_row=header_row)
        if not old.empty:
            frames.append(old)

    if not frames:
        raise ValueError(
            f"No valid IMAE data could be parsed. Available sheets: {xl.sheet_names}"
        )

    result = reduce(lambda left, right: pd.merge(left, right, on="date", how="outer"), frames)
    result = result.groupby("date", as_index=False).first()
    result = result.sort_values("date").reset_index(drop=True)

    result = result[(result["date"].dt.year >= 1990) & (result["date"].dt.year <= 2035)]
    result = result.reset_index(drop=True)

    return result
