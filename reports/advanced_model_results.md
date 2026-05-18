# Advanced Forecasting Model Results

## Modeling setup

- Dataset: `data/processed/monthly_panel_2019_2026.csv`
- Target: `imae_construction_index`
- Supervised rows after lag generation: 72
- Feature count: 13
- Exogenous predictors included: False

## Model comparison

| model                    |       mae |      rmse |     mape |    smape |
|:-------------------------|----------:|----------:|---------:|---------:|
| elasticnet_lagged        |  5.962085 |  7.660280 | 3.483057 | 3.570353 |
| ridge_lagged             |  5.966895 |  7.664062 | 3.485944 | 3.573210 |
| random_forest_lagged     | 11.411720 | 13.199196 | 6.571137 | 6.866466 |
| gradient_boosting_lagged | 13.413567 | 14.686941 | 7.787918 | 8.159800 |

## Best advanced model

The best advanced model by RMSE is `elasticnet_lagged`.

## Comparison against baseline benchmark

- Baseline RMSE: 11.644662
- Best advanced RMSE: 7.660280
- RMSE delta: -3.984382
- Baseline MAE: 10.028941
- Best advanced MAE: 5.962085
- MAE delta: -4.066856

The best advanced model beats the baseline benchmark by RMSE.

## Methodological note

The ML models use shifted lag and rolling-window features. This avoids using the current target value as a predictor for the same month. Optional exogenous variables are also shifted by one month to keep the default setup conservative.
