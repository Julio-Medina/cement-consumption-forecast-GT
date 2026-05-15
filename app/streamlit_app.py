from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cement_forecast.targets import (  # noqa: E402
    available_targets,
    default_target,
    numeric_series_columns,
    target_label,
)

st.set_page_config(page_title="Guatemala Cement Trade Forecast", layout="wide")

st.title("Forecasting Cement Trade and Construction Activity in Guatemala")
st.caption(
    "Portfolio project: public-data forecasting for cement-related trade flows, "
    "construction activity, and macroeconomic indicators."
)

preferred_path = Path("data/processed/modeling_dataset.csv")
fallback_path = Path("data/processed/sample_modeling_dataset.csv")

if preferred_path.exists():
    data_path = preferred_path
    data_note = "Using the real modeling dataset built from public official sources."
elif fallback_path.exists():
    data_path = fallback_path
    data_note = "Using the synthetic sample dataset. Build the real modeling dataset to replace it."
else:
    st.warning(
        "No modeling dataset found. Run `python scripts/build_modeling_dataset.py` for official data, "
        "or `python scripts/make_sample_dataset.py` for the synthetic development dataset."
    )
    st.stop()

st.info(data_note)
df = pd.read_csv(data_path, parse_dates=["date"])

series_cols = numeric_series_columns(df)
if not series_cols:
    st.error("No numeric time-series columns were found in the dataset.")
    st.stop()

catalog_targets = available_targets(df)
if catalog_targets:
    st.subheader("Forecastable business targets found")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "column": target.column,
                    "label": target.label,
                    "unit": target.unit,
                    "non_null_observations": int(
                        pd.to_numeric(df[target.column], errors="coerce").notna().sum()
                    ),
                    "description": target.description,
                }
                for target in catalog_targets
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

default = default_target(df)
selected = st.selectbox(
    "Select target or indicator",
    series_cols,
    index=series_cols.index(default) if default in series_cols else 0,
    format_func=target_label,
)

plot_df = df[["date", selected]].dropna()

fig = px.line(plot_df, x="date", y=selected, title=target_label(selected))
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Series summary")
    st.dataframe(plot_df[selected].describe().to_frame("value"), use_container_width=True)

with right:
    st.subheader("Latest available values")
    st.dataframe(
        df[["date", selected]].dropna().tail(12),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Dataset preview")
st.dataframe(df.tail(12), use_container_width=True)

st.subheader("Project note")
st.write(
    "This project is framed around observable public targets: cement import/export quantities or values "
    "when available, INE construction activity variables such as area in square meters and construction cost, "
    "and Banguat economic activity indicators such as IMAE when added. The legacy `cement_demand_proxy` is "
    "kept only as a transparent fallback index, not as a claim of physical domestic cement consumption."
)
