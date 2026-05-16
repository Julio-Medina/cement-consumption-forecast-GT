# Modeling Dataset Quality Report

Generated from `data/processed/modeling_dataset.csv`.

## Dataset shape

- Rows: `87`
- Columns: `29`
- Date range: `2019-01-01` to `2026-03-01`

## Target summary

| statistic   |      value |
|:------------|-----------:|
| count       | 87         |
| mean        | -0.0115411 |
| std         |  0.908413  |
| min         | -1.36517   |
| 25%         | -1.27851   |
| 50%         |  0.522118  |
| 75%         |  0.731262  |
| max         |  0.84322   |

## Target source-count distribution

|   source_count |   rows |
|---------------:|-------:|
|             22 |     75 |
|             25 |     12 |

## Highest missing-value columns

| column                                                                                            |   missing_pct |
|:--------------------------------------------------------------------------------------------------|--------------:|
| construction_num_constructions                                                                    |       86.2069 |
| construction_area_m2                                                                              |       86.2069 |
| construction_cost_gtq                                                                             |       86.2069 |
| remittances_usd_millions                                                                          |       62.069  |
| date                                                                                              |        0      |
| ipmc_4_1_tubo_de_concreto_vibro_prensado_1_m_largo_x_6_diametro_index                             |        0      |
| cement_demand_proxy                                                                               |        0      |
| ipmc_cement_related_index                                                                         |        0      |
| ipmc_6_adoquin_de_concreto_tipo_cruz_de_22_x_25_x_8_cm_42_5_kg_cm2_resistencia_a_la_flexion_index |        0      |
| ipmc_5_muros_prefabricados_5_cm_espesor_concreto_de_315_kg_cm2_liso_ambas_caras_index             |        0      |
| ipmc_5_1_teja_de_concreto_42_x_32_cm_tipo_veneciana_con_color_index                               |        0      |
| ipmc_4_cal_hidratada_index                                                                        |        0      |
| ipmc_4_alambre_de_acero_calibre_16_de_amarre_index                                                |        0      |
| ipmc_4_4_tuberia_perforada_concreto_simple_10_diametro_index                                      |        0      |
| ipmc_4_3_tubo_de_concreto_reforzado_1_m_largo_x_42_diametro_index                                 |        0      |
| ipmc_4_2_tubo_de_concreto_no_reforzado_1_m_largo_x_18_diametro_index                              |        0      |
| ipmc_3_concreto_de_3000_psi_index                                                                 |        0      |
| ipmc_3_tubo_de_metal_corrugado_redondo_de_24_x_0_86_m_calibre_16_incluye_accesorios_index         |        0      |
| ipmc_3_poste_de_concreto_6_m_de_largo_300_dan_300_kg_de_resistencia_index                         |        0      |
| ipmc_3_alambre_espigado_calibre_15_index                                                          |        0      |
| ipmc_2_malla_de_alambre_galvanizado_calibre_12_con_agujero_de_2_12_index                          |        0      |
| ipmc_2_cemento_blanco_cemento_hidraulico_tipo_bl_index                                            |        0      |
| ipmc_2_block_de_concreto_de_14_x_19_x_39_cm_50_kg_index                                           |        0      |
| ipmc_1_mezcladora_de_concreto_de_un_saco_index                                                    |        0      |
| ipmc_1_cemento_gris_cemento_hidraulico_tipo_ugc_para_uso_general_en_la_construccion_index         |        0      |

## Strongest numeric correlations with target

| feature                                                                                           |   correlation_with_target |
|:--------------------------------------------------------------------------------------------------|--------------------------:|
| ipmc_cement_related_index                                                                         |                  0.991363 |
| ipmc_1_cemento_gris_cemento_hidraulico_tipo_ugc_para_uso_general_en_la_construccion_index         |                  0.987875 |
| ipmc_4_cal_hidratada_index                                                                        |                  0.977016 |
| ipmc_3_tubo_de_metal_corrugado_redondo_de_24_x_0_86_m_calibre_16_incluye_accesorios_index         |                  0.964778 |
| ipmc_4_1_tubo_de_concreto_vibro_prensado_1_m_largo_x_6_diametro_index                             |                  0.959426 |
| ipmc_5_1_teja_de_concreto_42_x_32_cm_tipo_veneciana_con_color_index                               |                  0.95445  |
| ipmc_3_poste_de_concreto_6_m_de_largo_300_dan_300_kg_de_resistencia_index                         |                  0.954449 |
| ipmc_3_alambre_espigado_calibre_15_index                                                          |                  0.931818 |
| construction_area_m2                                                                              |                  0.931323 |
| ipmc_4_2_tubo_de_concreto_no_reforzado_1_m_largo_x_18_diametro_index                              |                  0.930479 |
| ipmc_4_3_tubo_de_concreto_reforzado_1_m_largo_x_42_diametro_index                                 |                  0.917279 |
| ipmc_1_mezcladora_de_concreto_de_un_saco_index                                                    |                  0.907685 |
| construction_cost_gtq                                                                             |                  0.907603 |
| ipmc_6_adoquin_de_concreto_tipo_cruz_de_22_x_25_x_8_cm_42_5_kg_cm2_resistencia_a_la_flexion_index |                  0.904368 |
| ipmc_2_cemento_blanco_cemento_hidraulico_tipo_bl_index                                            |                  0.902858 |

## Interpretation notes

- `cement_demand_proxy` is a public-data proxy, not observed private cement consumption.
- The current observed modeling window starts in 2019 because IPMC historical material indices begin there.
- Construction permit variables are sparse in the current raw download, so they should be treated as exploratory predictors until more years are added.
- Avoid using same-month predictors for forecasting. The ML script creates lagged features to reduce leakage.
