from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from cement_forecast.config import DATE_COLUMN, TARGET_COLUMN


@dataclass(frozen=True)
class TargetSpec:
    """Metadata for a forecastable business target."""

    column: str
    label: str
    description: str
    unit: str
    priority: int = 100


TARGET_CATALOG: tuple[TargetSpec, ...] = (
    TargetSpec(
        column="cement_import_tons",
        label="Cement import tons",
        description="Monthly tons of cement-related imports. Add this target after parsing WITS/Comtrade or a quantity source.",
        unit="tons",
        priority=10,
    ),
    TargetSpec(
        column="cement_export_tons",
        label="Cement export tons",
        description="Monthly tons of cement-related exports. Add this target after parsing WITS/Comtrade or a quantity source.",
        unit="tons",
        priority=11,
    ),
    TargetSpec(
        column="net_cement_import_tons",
        label="Net cement import tons",
        description="Cement import tons minus cement export tons.",
        unit="tons",
        priority=12,
    ),
    TargetSpec(
        column="cement_import_value_usd",
        label="Cement import value",
        description="Monthly USD value of cement-related imports. Add this after parsing Banguat product-level trade data.",
        unit="USD",
        priority=20,
    ),
    TargetSpec(
        column="cement_export_value_usd",
        label="Cement export value",
        description="Monthly USD value of cement-related exports. Add this after parsing Banguat product-level trade data.",
        unit="USD",
        priority=21,
    ),
    TargetSpec(
        column="construction_area_m2",
        label="Construction area",
        description="Authorized/registered private construction area from INE, converted to a monthly series when needed.",
        unit="square meters",
        priority=50,
    ),
    TargetSpec(
        column="construction_cost_gtq",
        label="Construction cost",
        description="Approximate private construction cost from INE, converted to a monthly series when needed.",
        unit="GTQ",
        priority=51,
    ),
    TargetSpec(
        column="construction_num_constructions",
        label="Number of constructions",
        description="Number of private construction records from INE, converted to a monthly series when needed.",
        unit="count",
        priority=52,
    ),
    TargetSpec(
        column="imae_construction_index",
        label="IMAE construction index",
        description="Monthly economic activity index for the construction sector from Banguat IMAE components.",
        unit="index",
        priority=30,
    ),
    TargetSpec(
        column="imae_general_index",
        label="IMAE general index",
        description="Monthly general economic activity index from Banguat IMAE components.",
        unit="index",
        priority=31,
    ),
    TargetSpec(
        column="imae_construction_yoy",
        label="IMAE construction YoY",
        description="Year-over-year percentage change of the construction-sector IMAE.",
        unit="percent",
        priority=32,
    ),
    TargetSpec(
        column="imae_general_yoy",
        label="IMAE general YoY",
        description="Year-over-year percentage change of the general IMAE.",
        unit="percent",
        priority=33,
    ),
    TargetSpec(
        column="imae_construction_trend_index",
        label="IMAE construction trend-cycle index",
        description="Trend-cycle index for construction-sector activity from Banguat IMAE components.",
        unit="index",
        priority=34,
    ),
    TargetSpec(
        column="imae_general_trend_index",
        label="IMAE general trend-cycle index",
        description="Trend-cycle index for general economic activity from Banguat IMAE components.",
        unit="index",
        priority=35,
    ),
    TargetSpec(
        column=TARGET_COLUMN,
        label="Legacy cement-related proxy",
        description="Transparent proxy built from cement/construction/material indicators when direct target series are unavailable.",
        unit="standardized index",
        priority=90,
    ),
)


CATALOG_BY_COLUMN = {target.column: target for target in TARGET_CATALOG}


def available_targets(df: pd.DataFrame, *, min_observations: int = 2) -> list[TargetSpec]:
    """Return catalog targets that are present and have enough non-null observations."""
    targets: list[TargetSpec] = []
    for spec in TARGET_CATALOG:
        if spec.column in df.columns:
            values = pd.to_numeric(df[spec.column], errors="coerce")
            if int(values.notna().sum()) >= min_observations:
                targets.append(spec)
    return sorted(targets, key=lambda spec: spec.priority)


def numeric_series_columns(df: pd.DataFrame, *, min_observations: int = 2) -> list[str]:
    """Return numeric columns that can be plotted or modeled as time series."""
    columns: list[str] = []
    for column in df.columns:
        if column == DATE_COLUMN:
            continue
        values = pd.to_numeric(df[column], errors="coerce")
        if int(values.notna().sum()) >= min_observations:
            columns.append(column)
    return columns


def default_target(df: pd.DataFrame) -> str:
    """Choose the most business-relevant available target for the current dataset."""
    targets = available_targets(df)
    if targets:
        return targets[0].column
    numeric = numeric_series_columns(df)
    if not numeric:
        raise ValueError("No numeric target candidates were found")
    return numeric[0]


def target_label(column: str) -> str:
    """Return a human-friendly label for a target/series column."""
    if column in CATALOG_BY_COLUMN:
        return CATALOG_BY_COLUMN[column].label
    return column.replace("_", " ").title()


def validate_target_column(df: pd.DataFrame, target_col: str, *, min_observations: int = 2) -> None:
    """Validate that a target column exists and has enough observations."""
    if target_col not in df.columns:
        available = ", ".join(numeric_series_columns(df, min_observations=min_observations))
        raise ValueError(f"Target column {target_col!r} is missing. Available numeric columns: {available}")
    observed = int(pd.to_numeric(df[target_col], errors="coerce").notna().sum())
    if observed < min_observations:
        raise ValueError(
            f"Target column {target_col!r} has only {observed} non-null observations; "
            f"at least {min_observations} are required."
        )
