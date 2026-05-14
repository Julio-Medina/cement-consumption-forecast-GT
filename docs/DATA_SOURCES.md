# Data Sources

This file documents the first public data sources planned for the cement-demand forecasting project.

## 1. Banco de Guatemala: exports/imports by product

- Page: https://banguat.gob.gt/page/exportaciones-e-importaciones-mensuales-por-producto
- Excel URL observed from the download link: https://banguat.gob.gt/sites/default/files/banguat/estaeco/comercio/por_producto/prod_mens.xlsx
- Why it matters: may contain cement-related product categories such as cement, plaster, stone/cement/gypsum manufactures, or related construction inputs.
- Candidate features:
  - cement_import_value_usd
  - cement_export_value_usd
  - stone_cement_gypsum_manufactures_import_value_usd
  - related_materials_trade_value_usd

## 2. INE Guatemala: IPMC construction-material price index

- Page: https://www.ine.gob.gt/indice-de-materiales-de-construccion/
- Excel URL observed from the download link as of 2026-05-14: https://www.ine.gob.gt/wp-content/uploads/2026/04/HISTORICO-MARZO-2026.xlsx
- Why it matters: the IPMC measures monthly price variation for 89 materials and services used in construction.
- Candidate features:
  - cement_price_index
  - concrete_price_index
  - steel_price_index
  - aggregate_materials_index
  - overall_construction_material_index

## 3. INE Guatemala open data: construcciones particulares

- Page: https://datos.ine.gob.gt/dataset/construcciones-particulares-nivel-departamental/resource/aae2a8a8-2643-42bc-b5ae-67cc5613b1dd
- Excel URL: https://datos.ine.gob.gt/dataset/cc9e7fa8-334f-4fe3-8bb2-e0d5fa826206/resource/aae2a8a8-2643-42bc-b5ae-67cc5613b1dd/download/bd-construcciones-particulares-departamento-de-guatemala.xlsx
- Variables visible in the data dictionary:
  - Año
  - Trimestre
  - Departamento
  - Municipio
  - Num_Construcciones
  - Area_Con_M2
  - Costo_aprox_quetzales
- Why it matters: this can be used as a construction-activity target or predictor.

## 4. Banco de Guatemala: remittances

- Page: https://banguat.gob.gt/page/remesas-familiares-0
- Excel URL observed from the download link: https://banguat.gob.gt/sites/default/files/banguat/estaeco/remesas/remfam2010_2021.xls
- Why it matters: remittances are a strong macroeconomic driver of household consumption and may influence housing and construction demand.

## 5. Banco de Guatemala: exchange rate

- Web service: https://www.banguat.gob.gt/variables/ws/tipocambio.asmx
- General exchange-rate page: https://www.banguat.gob.gt/tipo_cambio
- Why it matters: exchange-rate movements affect imported construction materials and input costs.

## 6. Optional external data

### World Bank API

- Country: Guatemala, code `GTM`
- Example indicators:
  - NY.GDP.MKTP.KD.ZG: GDP growth
  - FP.CPI.TOTL.ZG: inflation
  - BX.TRF.PWKR.CD.DT: personal remittances received

### Google Trends

Potential search terms:

- cemento
- construcción
- vivienda
- materiales de construcción

Google Trends data should be treated as experimental and documented carefully.
