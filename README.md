# Forecasting Cement Demand and Construction Activity in Guatemala

This project builds an end-to-end forecasting system for cement demand / construction activity in Guatemala using public economic indicators.

The project is designed as a professional data science portfolio repository: it includes data ingestion, cleaning, feature engineering, baseline and machine-learning forecasting models, evaluation, explainability, and an optional dashboard.

## Business problem

Cement consumption is closely related to construction, housing, infrastructure, remittances, credit, exchange rates, and construction-material costs. Exact monthly cement-consumption data may not be public, so the first version of this project uses a transparent public-data strategy:

1. Use cement-related import/export/product data where available.
2. Use INE construction-material price indices, including cement/concrete-related materials, as cost-pressure signals.
3. Use construction-permit style data such as number of constructions, area in square meters, and approximate construction cost.
4. Use macroeconomic predictors such as remittances, exchange rate, inflation, and economic activity.
5. Build a forecasting target named `cement_demand_proxy` when direct consumption is not available.

## Portfolio objective

The final project should answer:

> Can we forecast short-term cement demand / construction activity in Guatemala using macroeconomic and construction-sector indicators?

## Core data sources

See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) and [`data_sources.yml`](data_sources.yml).

Planned sources include:

- Banco de Guatemala: monthly exports/imports by product.
- Banco de Guatemala: remittances.
- Banco de Guatemala: exchange-rate web service.
- INE Guatemala: Índice de Precios de Materiales de Construcción, IPMC.
- INE Guatemala open-data portal: construcciones particulares.
- Optional: World Bank indicators.
- Optional: Google Trends terms such as `cemento`, `construcción`, `vivienda`.

## Repository structure

```text
cement-consumption-forecast-guatemala/
  app/                      # Streamlit dashboard
  data/                     # raw/interim/processed data, ignored by git
  docs/                     # documentation and data-source notes
  notebooks/                # exploratory notebooks
  reports/                  # final figures and written report
  scripts/                  # command-line scripts
  src/cement_forecast/      # reusable Python package
  tests/                    # unit tests
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run tests:

```bash
pytest -q
```

Profile raw official files after downloading or manually placing files in `data/raw`:

```bash
python scripts/profile_raw_data.py
```

This creates `reports/raw_data_inventory.md`, which helps identify sheet names, likely header rows, date columns, and numeric columns before writing source-specific parsers.

Build a real modeling dataset once the correct sheet/header combinations are known:

```bash
python scripts/build_modeling_dataset.py \
  --source ine_ipmc:data/raw/<ipmc_file.xlsx>:<sheet_name_or_index>:<header_row> \
  --source banguat_remittances:data/raw/<remittances_file.xlsx>:<sheet_name_or_index>:<header_row>
```

Generate a sample dataset so the pipeline can run immediately:

```bash
python scripts/make_sample_dataset.py
```

Train baseline models:

```bash
python scripts/train_baseline.py --data data/processed/sample_modeling_dataset.csv
```

Launch dashboard:

```bash
streamlit run app/streamlit_app.py
```

## Modeling roadmap

### Version 0.1

- Create public-data catalog.
- Build reproducible repository structure.
- Generate a sample monthly dataset for development.
- Implement time-series features.
- Implement baseline models: naive, seasonal naive, moving average.
- Add evaluation metrics: MAE, RMSE, MAPE, sMAPE.

### Version 0.2

- Add raw-data profiling for messy official Excel/CSV files.
- Add parser scaffolding for Banguat and INE sources.
- Add a reproducible `build_modeling_dataset.py` script.
- Build a transparent `cement_demand_proxy` from available public indicators.

### Version 0.3

- Finalize source-specific parsers after inspecting official files.
- Build the first real monthly modeling table.
- Add SARIMAX and tree-based models.
- Add walk-forward validation.

### Version 0.4

- Add XGBoost/LightGBM if useful.
- Add feature importance / SHAP.
- Improve Streamlit dashboard with real data.
- Produce final technical report.

## Ethical and methodological note

This project is not claiming access to confidential cement-sales data. When direct cement-consumption data is unavailable, the target is explicitly modeled as a public-data proxy. This is intentional and transparent.
