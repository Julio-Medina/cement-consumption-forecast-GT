# Monthly Panel Contract

The main forecasting dataset must be a strict monthly panel.

## Rules

1. The date column must be monthly and use month-start dates.
2. The main modeling period starts at `2019-01-01`.
3. The panel must have one row per month and no gaps.
4. Forecasting columns must have no missing values over the selected period.
5. Sparse or lower-frequency indicators are allowed in exploratory datasets, but they should not be used in the primary forecasting experiments until a complete monthly series is available.
6. No backfilling or forward-filling across unobserved years just to force alignment.

## Recommended workflow

Build the merged dataset first:

```bash
python scripts/build_modeling_dataset.py \
  --source 'banguat_remittances:data/raw/banguat_remesas.xls:2002-2021:9' \
  --source 'ine_ipmc:data/raw/ine_ipmc_historico.xlsx:Publicación Histórico 2026:0' \
  --skip-proxy-target
```

Then build the strict aligned panel:

```bash
python scripts/build_strict_monthly_panel.py \
  --data data/processed/modeling_dataset.csv \
  --start 2019-01-01
```

The script writes:

- `data/processed/monthly_panel_2019_2026.csv`
- `reports/monthly_panel_report.md`

Use this strict panel for the main forecasting experiments.
