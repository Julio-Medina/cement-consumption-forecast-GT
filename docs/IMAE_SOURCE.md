# Banguat IMAE source

The main construction-activity target should use the current **Banco de Guatemala**
IMAE workbook with **Año de Referencia 2013**, not the older 2001-reference
workbook.

## Why this matters

The old workbook can stop before the recent modeling period. If the parsed IMAE
columns end around 2019, the dataset is not suitable for the portfolio's main
modeling contract:

```text
monthly, recent, aligned, 2019 onward, no missing values
```

## Download

Use:

```bash
python scripts/download_banguat_imae.py
```

This creates:

```text
data/raw/banguat_imae_2013.xlsx
```

The script discovers the current Excel link from the Banguat IMAE 2013 page and
falls back to the March 2026 workbook URL when discovery fails.

## Build the modeling dataset

```bash
python scripts/build_modeling_dataset.py \
  --source 'banguat_imae:data/raw/banguat_imae_2013.xlsx:IMAE componentes:6' \
  --source 'ine_ipmc:data/raw/ine_ipmc_historico.xlsx:Publicación Histórico 2026:0' \
  --source 'banguat_remittances:data/raw/banguat_remesas.xls:2002-2021:9' \
  --skip-proxy-target
```

Then verify coverage:

```bash
