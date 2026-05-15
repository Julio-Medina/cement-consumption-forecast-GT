# Next Steps

## Current status

The repository currently has a working end-to-end development pipeline using a synthetic monthly dataset. The next task is to convert official Banguat and INE files into standardized monthly tables.

## Version 0.2 target

1. Place official downloaded files in `data/raw/`.
2. Run:

   ```bash
   python scripts/profile_raw_data.py
   ```

3. Review `reports/raw_data_inventory.md`.
4. Identify the best `sheet_name` and `header_row` for each source.
5. Build the first real modeling dataset with:

   ```bash
   python scripts/build_modeling_dataset.py \
     --source ine_ipmc:data/raw/<ipmc_file.xlsx>:<sheet_name_or_index>:<header_row> \
     --source banguat_remittances:data/raw/<remittances_file.xlsx>:<sheet_name_or_index>:<header_row>
   ```

## Parser strategy

The first parser layer is intentionally generic. Official files often contain title rows, merged headers, blank rows, and footnotes. Instead of hardcoding assumptions too early, the project now has a profiling script that helps us find the true tabular region.

Once we know the real workbook structures, we should replace the generic calls with source-specific parser functions that encode the exact sheet names, header rows, and required columns.
