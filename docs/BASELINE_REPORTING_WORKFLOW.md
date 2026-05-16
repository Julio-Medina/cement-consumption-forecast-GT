# Baseline Reporting Workflow

This project compares simple time-series baselines before adding advanced
machine-learning models. This is intentional: a forecasting model is only useful
if it beats transparent alternatives.

The first serious target is:

```text
imae_construction_index
```

This is the Banguat IMAE construction-sector activity index. It is a real
monthly public indicator, unlike the earlier exploratory `cement_demand_proxy`.

## Recommended command

```bash
python scripts/make_baseline_report.py \
  --data data/processed/monthly_panel_2019_2026.csv \
  --target imae_construction_index \
  --test-size 12 \
  --output-md reports/imae_baseline_results.md \
  --output-csv reports/imae_baseline_comparison.csv \
  --output-predictions reports/imae_baseline_predictions.csv
```

If your strict monthly panel is named `monthly_panel_2019_2025.csv`, use that
file instead.

## Outputs

The script writes:

```text
reports/imae_baseline_results.md
reports/imae_baseline_comparison.csv
reports/imae_baseline_predictions.csv
```

The Markdown file is intended to be committed as a portfolio artifact. The CSV
outputs are useful for charts, dashboards, and later model comparison.

## Interpretation rules

- Prefer MAE and RMSE for model selection.
- MAPE and sMAPE are reported for communication, but they are secondary.
- The best baseline becomes the benchmark that advanced models must beat.
- If an advanced model does not beat the best simple baseline, the honest
  conclusion is that the simpler model is preferred.

