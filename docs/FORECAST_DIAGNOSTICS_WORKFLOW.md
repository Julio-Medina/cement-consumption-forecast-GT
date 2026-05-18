# Forecast Diagnostics Workflow

This workflow turns model metrics into portfolio-ready evidence.

After running the baseline and advanced forecasting scripts, generate a diagnostics report with:

```bash
python scripts/make_forecast_diagnostics.py \
  --data data/processed/monthly_panel_2019_2026.csv \
  --target imae_construction_index \
  --comparison reports/advanced_model_comparison.csv \
  --predictions reports/advanced_model_predictions.csv \
  --baseline-rmse 11.644662 \
  --baseline-mae 10.028941 \
  --output-md reports/forecast_diagnostics_report.md \
  --figures-dir reports/figures
```

The script writes:

```text
reports/forecast_diagnostics_report.md
reports/figures/model_comparison_rmse.png
reports/figures/holdout_actual_vs_predicted.png
reports/figures/holdout_residuals.png
reports/figures/lag_correlation_importance.png
```

## Why this matters

A forecasting portfolio project should not stop at a model-comparison table. It should explain:

1. which model won,
2. whether it beat the baseline,
3. how large the improvement was,
4. whether residuals show obvious errors,
5. which lagged signals are most associated with the target.

## Interpretation rule

Advanced models are only considered useful if they improve on the strongest simple baseline. For this project, the current baseline benchmark is:

```text
moving_average_6
MAE  ≈ 10.03
RMSE ≈ 11.64
```

The advanced model report should explicitly compare against those values.

## Suggested GitHub artifacts

Commit these files:

```text
reports/forecast_diagnostics_report.md
reports/figures/model_comparison_rmse.png
reports/figures/holdout_actual_vs_predicted.png
reports/figures/holdout_residuals.png
reports/figures/lag_correlation_importance.png
```

Do not commit raw data or large generated prediction CSVs unless intentionally publishing them.

## Portfolio message

The final README can summarize this milestone as:

> Built a strict monthly forecasting panel for Guatemala construction activity and compared simple baselines against lagged machine-learning models. ElasticNet with lagged predictors improved holdout RMSE by about 34% versus the strongest moving-average baseline, while diagnostic plots and lag-correlation analysis were used to evaluate model behavior.
diff --git a/scripts/make_forecast_diagnostics.py b/scripts/make_forecast_diagnostics.py
new file mode 100644
index 0000000..0f5c939
--- /dev/null
++ b/scripts/make_forecast_diagnostics.py
