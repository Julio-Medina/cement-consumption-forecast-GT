# Forecast Diagnostics and Model Interpretation

## Modeling target

- Dataset: `data/processed/monthly_panel_2019_2026.csv`
- Target: `imae_construction_index`
- Best advanced model: `elasticnet_lagged`

## Model comparison

| model                    |       mae |      rmse |     mape |    smape |
|:-------------------------|----------:|----------:|---------:|---------:|
| elasticnet_lagged        |  5.962085 |  7.660280 | 3.483057 | 3.570353 |
| ridge_lagged             |  5.966895 |  7.664062 | 3.485944 | 3.573210 |
| random_forest_lagged     | 11.411720 | 13.199196 | 6.571137 | 6.866466 |
| gradient_boosting_lagged | 13.413567 | 14.686941 | 7.787918 | 8.159800 |

## Improvement over baseline

- Baseline RMSE: 11.644662
- Best advanced RMSE: 7.660280
- RMSE improvement: 34.22%
- Baseline MAE: 10.028941
- Best advanced MAE: 5.962085
- MAE improvement: 40.55%

## Diagnostic figures

- model_comparison_rmse: `reports/figures/model_comparison_rmse.png`
- holdout_actual_vs_predicted: `reports/figures/holdout_actual_vs_predicted.png`
- holdout_residuals: `reports/figures/holdout_residuals.png`
- lag_correlation_importance: `reports/figures/lag_correlation_importance.png`

## Lag-correlation diagnostics

| feature                                                               |   lag |   correlation |   abs_correlation |   observations |
|:----------------------------------------------------------------------|------:|--------------:|------------------:|---------------:|
| ipmc_4_1_tubo_de_concreto_vibro_prensado_1_m_largo_x_6_diametro_index |     1 |      0.875165 |          0.875165 |             83 |
| ipmc_2_block_de_concreto_de_14_x_19_x_39_cm_50_kg_index               |     1 |      0.873060 |          0.873060 |             83 |
| ipmc_4_1_tubo_de_concreto_vibro_prensado_1_m_largo_x_6_diametro_index |     2 |      0.872827 |          0.872827 |             82 |
| ipmc_2_block_de_concreto_de_14_x_19_x_39_cm_50_kg_index               |     2 |      0.869004 |          0.869004 |             82 |
| ipmc_4_1_tubo_de_concreto_vibro_prensado_1_m_largo_x_6_diametro_index |     3 |      0.863839 |          0.863839 |             81 |
| ipmc_4_4_tuberia_perforada_concreto_simple_10_diametro_index          |     4 |      0.861839 |          0.861839 |             80 |
| ipmc_2_block_de_concreto_de_14_x_19_x_39_cm_50_kg_index               |     3 |      0.860622 |          0.860622 |             81 |
| ipmc_4_1_tubo_de_concreto_vibro_prensado_1_m_largo_x_6_diametro_index |     4 |      0.859465 |          0.859465 |             80 |
| ipmc_3_concreto_de_3000_psi_index                                     |     1 |      0.859370 |          0.859370 |             83 |
| ipmc_4_2_tubo_de_concreto_no_reforzado_1_m_largo_x_18_diametro_index  |     2 |      0.857807 |          0.857807 |             82 |

## Interpretation

The advanced lagged forecasting workflow is evaluated against the strongest simple baseline. The result is only considered useful if it improves on that benchmark. In the current experiment, the best advanced model is compared directly against the moving-average baseline using MAE and RMSE.
