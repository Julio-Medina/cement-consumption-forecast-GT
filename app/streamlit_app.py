from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Guatemala Cement Demand Forecast", layout="wide")

st.title("Forecasting Cement Demand and Construction Activity in Guatemala")
st.caption("Portfolio project: public-data forecasting, macroeconomic indicators, and construction-sector analytics.")

sample_path = Path("data/processed/modeling_dataset.csv")

if not sample_path.exists():
    st.warning("No modeling dataset found. Run the build_modeling_dataset.py script first.")
    st.stop()

df = pd.read_csv(sample_path, parse_dates=["date"])

metric_cols = [c for c in df.columns if c != "date"]
selected = st.selectbox("Select series", metric_cols, index=metric_cols.index("cement_demand_proxy"))

fig = px.line(df, x="date", y=selected, title=selected.replace("_", " ").title())
st.plotly_chart(fig, use_container_width=True)

st.subheader("Latest values")
st.dataframe(df.tail(12), use_container_width=True)

st.subheader("Project note")
st.write(
    "This dashboard uses a public-data proxy for cement-related construction/material demand in Guatemala. "
    "The target is built from official public indicators and should be interpreted as a proxy, not as private "
    "industry cement consumption."
)
