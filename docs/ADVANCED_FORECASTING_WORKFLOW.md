# Advanced Forecasting Workflow

This workflow trains leakage-aware tabular machine-learning models for the strict monthly panel.

The current benchmark from the IMAE construction baseline report is the six-month moving average. Advanced models should be evaluated against that simple benchmark rather than accepted automatically.

## Run advanced models

```bash
python scripts/train_advanced_models.py \
  --data data/processed/monthly_panel_2019_2026.csv \
  --target imae_construction_index \
  --test-size 12 \
  --baseline-rmse 11.644662 \
  --baseline-mae 10.028941
```

This writes:

```text
reports/advanced_model_results.md
reports/advanced_model_comparison.csv
reports/advanced_model_predictions.csv
```

## Leakage policy

The advanced models use shifted lag and rolling-window features. Optional exogenous variables are also shifted by one month, which keeps the default setup conservative.

## Interpretation rule

If the advanced models do not beat the moving-average baseline, the README and report should say so explicitly. A simple model that performs better is a valid and valuable forecasting result.
