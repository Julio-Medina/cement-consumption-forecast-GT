# Strict Monthly Panel Report

This report validates the modeling panel used for forecasting experiments.

## Period

- Start: `2019-01-01`
- End: `2025-12-01`
- Expected monthly rows: `84`
- Actual rows: `84`
- Complete panel: `True`

## Selected complete columns

- `imae_construction_index`
- `imae_general_index_x`
- `imae_construction_yoy`
- `imae_general_yoy_x`
- `imae_general_index_y`
- `imae_general_yoy_y`
- `imae_general_trend_index`
- `ipmc_1_1_lamina_de_acero_galvanizado_estructural_troquelada_calibre_26_de_1_08_m_ancho_index`
- `ipmc_1_2_lamina_tipo_losacero_calibre_22_0_95_m_de_ancho_index`
- `ipmc_1_3_lamina_para_techo_curvo_de_aluzinc_calibre_26_30_5_cm_de_ancho_index`
- `ipmc_1_cemento_gris_cemento_hidraulico_tipo_ugc_para_uso_general_en_la_construccion_index`
- `ipmc_1_mezcladora_de_concreto_de_un_saco_index`
- `ipmc_2_block_de_concreto_de_14_x_19_x_39_cm_50_kg_index`
- `ipmc_2_cemento_blanco_cemento_hidraulico_tipo_bl_index`
- `ipmc_2_malla_de_alambre_galvanizado_calibre_12_con_agujero_de_2_12_index`
- `ipmc_3_alambre_espigado_calibre_15_index`
- `ipmc_3_concreto_de_3000_psi_index`
- `ipmc_3_poste_de_concreto_6_m_de_largo_300_dan_300_kg_de_resistencia_index`
- `ipmc_3_tubo_de_metal_corrugado_redondo_de_24_x_0_86_m_calibre_16_incluye_accesorios_index`
- `ipmc_4_1_tubo_de_concreto_vibro_prensado_1_m_largo_x_6_diametro_index`
- `ipmc_4_2_tubo_de_concreto_no_reforzado_1_m_largo_x_18_diametro_index`
- `ipmc_4_3_tubo_de_concreto_reforzado_1_m_largo_x_42_diametro_index`
- `ipmc_4_4_tuberia_perforada_concreto_simple_10_diametro_index`
- `ipmc_4_alambre_de_acero_calibre_16_de_amarre_index`
- `ipmc_4_cal_hidratada_index`
- `ipmc_5_1_teja_de_concreto_42_x_32_cm_tipo_veneciana_con_color_index`
- `ipmc_5_muros_prefabricados_5_cm_espesor_concreto_de_315_kg_cm2_liso_ambas_caras_index`
- `ipmc_6_adoquin_de_concreto_tipo_cruz_de_22_x_25_x_8_cm_42_5_kg_cm2_resistencia_a_la_flexion_index`
- `ipmc_cement_related_index`

## Dropped incomplete columns

- `imae_general_trend_yoy`: 84 missing month(s)
- `remittances_usd_millions`: 51 missing month(s)

## Methodological rule

The main modeling panel must be monthly, recent, aligned, and free of missing values. Sparse or lower-frequency variables can be documented separately, but they should not be used in the primary forecasting experiments until a complete aligned series is available.
