# Forecasting Cement Trade and Construction Activity in Guatemala

<!-- PORTFOLIO_SUMMARY_START -->

## Portfolio summary

**Project:** Forecasting cement-related construction activity in Guatemala using public macroeconomic, construction-material, and economic-activity indicators.

**Main modeling target:** `imae_construction_index` from Banco de Guatemala's IMAE construction activity series.

**Modeling window:** `2019-01-01` to `2025-12-01` using a strict monthly panel with no missing values in the selected modeling columns.

### Why this project matters

This project demonstrates an end-to-end forecasting workflow for a real economic activity indicator related to Guatemala's construction sector. The project originally explored cement demand proxies, but was reframed around observable public targets because a free public monthly series for domestic physical cement consumption was not available.

The current version focuses on forecasting construction-sector activity through Banguat IMAE, while keeping the architecture ready for cement import/export targets when reliable monthly trade quantity or value series are added.

### Current result

| Benchmark | Model | MAE | RMSE |
|---|---:|---:|---:|
| Strongest baseline | moving_average_6 | 10.028941 | 11.644662 |
| Best advanced model | elasticnet_lagged | 5.962085 | 7.660280 |

- RMSE improvement: 34.22%
- MAE improvement: 40.55%

**RMSE improvement:** 34.22%  
**MAE improvement:** 40.55%

The best advanced model, `elasticnet_lagged`, improved substantially over the strongest simple baseline. This makes the result more meaningful than simply reporting a machine-learning score without a baseline comparison.

### Project highlights

- Public-data ingestion from Banguat and INE sources.
- Robust Excel parsing for messy official workbooks.
- Strict monthly-panel validation from 2019 onward.
- Baseline forecasting with naïve, seasonal-naïve, and moving-average models.
- Advanced lagged ML forecasting with regularized regression and tree-based models.
- Forecast diagnostics: model comparison, actual-vs-predicted plot, residual analysis, and lag-correlation analysis.
- Portfolio-ready Markdown reports and reproducible scripts.

### Key reports

- `reports/imae_baseline_results.md`
- `reports/advanced_model_results.md`
- `reports/forecast_diagnostics_report.md`
- `docs/MONTHLY_PANEL_CONTRACT.md`
- `docs/FORECAST_DIAGNOSTICS_WORKFLOW.md`

<!-- PORTFOLIO_SUMMARY_END -->


This repository is a professional data science portfolio project focused on **public-data forecasting for Guatemala's cement-related trade flows and construction activity**.

The project is intentionally framed around observable public targets rather than confidential industry sales data. The main forecast targets are designed to include:

- cement import tons;
- cement export tons;
- net cement import tons;
- cement import/export value;
- construction area in square meters;
- construction cost in quetzales;
- number of private constructions;
- IMAE construction/economic activity indices when added.

A legacy `cement_demand_proxy` can still be built as a transparent fallback index, but it is **not** treated as actual physical domestic cement consumption.

## Business problem

Cement demand is linked to construction, housing, infrastructure, remittances, credit, exchange rates, imports/exports, and construction-material costs. However, a free public monthly series for actual physical cement consumption in Guatemala is not currently available in this project.

Therefore, the project focuses on targets that can be defended publicly:

1. **Cement trade quantities and values** from trade sources such as Banguat, WITS, or UN Comtrade.
2. **Construction activity indicators** from INE, such as construction area, approximate cost, and number of constructions.
3. **Macroeconomic activity indicators** such as IMAE, remittances, and exchange rate.
4. **Construction-material price indices** such as INE IPMC cement/concrete-related materials.

## Portfolio objective

The final project should answer:

> Can we forecast cement-related trade flows and construction activity in Guatemala using public trade, construction, and macroeconomic indicators?

This is a stronger and more defensible portfolio framing than claiming direct access to private cement-consumption data.

## Core data sources

See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) and [`data_sources.yml`](data_sources.yml).

Planned and/or parsed sources include:

- Banco de Guatemala: monthly exports/imports by product.
- Banco de Guatemala: remittances.
- Banco de Guatemala: exchange-rate web service.
- Banco de Guatemala: IMAE and economic activity indicators.
- INE Guatemala: Índice de Precios de Materiales de Construcción, IPMC.
- INE Guatemala open-data portal: construcciones particulares.
- Optional: WITS / UN Comtrade cement HS-code trade quantities.
- Optional: World Bank indicators.

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

## Data workflow

Profile raw official files after downloading or manually placing files in `data/raw`:

```bash
python scripts/profile_raw_data.py
```

This creates `reports/raw_data_inventory.md`, which helps identify sheet names, likely header rows, date columns, and numeric columns before writing source-specific parsers.

Build a real modeling dataset once the correct sheet/header combinations are known:

```bash
python scripts/build_modeling_dataset.py \
  --source 'banguat_remittances:data/raw/banguat_remesas.xls:2002-2021:9' \
  --source 'ine_construction:data/raw/ine_construcciones_particulares_gt.xlsx:Hoja1:0' \
  --source 'ine_ipmc:data/raw/ine_ipmc_historico.xlsx:Publicación Histórico 2026:0' \
  --drop-missing-target
```

If you want a dataset with only observable parsed series and no legacy proxy target, use:

```bash
python scripts/build_modeling_dataset.py \
  --source 'banguat_remittances:data/raw/banguat_remesas.xls:2002-2021:9' \
  --source 'ine_construction:data/raw/ine_construcciones_particulares_gt.xlsx:Hoja1:0' \
  --source 'ine_ipmc:data/raw/ine_ipmc_historico.xlsx:Publicación Histórico 2026:0' \
  --skip-proxy-target
```

Generate a synthetic sample dataset so the pipeline can run immediately:

```bash
python scripts/make_sample_dataset.py
```

## Modeling examples

Train baseline models for the legacy proxy:

```bash
python scripts/train_baseline.py \
  --data data/processed/modeling_dataset.csv \
  --target cement_demand_proxy
```

Train baseline models for a direct construction activity target:

```bash
python scripts/train_baseline.py \
  --data data/processed/modeling_dataset.csv \
  --target construction_area_m2 \
  --test-size 3
```

Use a smaller `--test-size` when a target has few observations, such as quarterly construction data converted to monthly values.

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

### Version 0.3

- Finalize source-specific parsers after inspecting official files.
- Build the first real monthly modeling table.

### Version 0.4

- Improve target quality and avoid extrapolating proxy values into missing periods.

### Version 0.5+

- Add target-specific modeling for cement trade, construction activity, and IMAE.
- Parse cement import/export quantities from WITS/Comtrade or another quantity source.
- Parse Banguat product-level trade values.
- Add SARIMAX and tree-based models.
- Add walk-forward validation.
- Add feature importance / SHAP.
- Improve Streamlit dashboard with real target selection.
- Produce final technical report.

## Ethical and methodological note

This project is not claiming access to confidential cement-sales data. When direct domestic cement-consumption data is unavailable, the project forecasts observable public targets such as cement trade, construction area, construction cost, and activity indices. Any proxy target is explicitly documented as a proxy, not as measured physical cement consumption.
