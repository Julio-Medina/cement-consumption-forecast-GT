# IMAE Construction Baseline Forecasting Results

## Modeling setup

- Dataset: `data/processed/monthly_panel_2019_2026.csv`
- Target: `imae_construction_index`
- Training window: 2019-01-01 to 2024-12-01
- Holdout window: 2025-01-01 to 2025-12-01
- Training observations: 72
- Holdout observations: 12

## Model comparison

| model             |       mae |      rmse |      mape |     smape | status   |
|:------------------|----------:|----------:|----------:|----------:|:---------|
| moving_average_6  | 10.028941 | 11.644662 |  5.795924 |  5.997955 | trained  |
| moving_average_3  | 10.702968 | 12.359946 |  6.177751 |  6.416727 | trained  |
| seasonal_naive_12 | 13.253624 | 14.028940 |  7.800050 |  8.157731 | trained  |
| naive             | 19.528575 | 21.288279 | 11.318186 | 12.117473 | trained  |

## Best baseline

The best baseline by RMSE is `moving_average_6`.

This baseline becomes the benchmark that advanced forecasting models must beat. If a more complex model does not improve on this result, the simpler baseline is preferred.

## Portfolio interpretation

The target is a real public monthly construction-activity indicator from Banguat IMAE. This is more defensible than the earlier exploratory cement-demand proxy because it is directly observed, monthly, and complete over the selected recent modeling window.
