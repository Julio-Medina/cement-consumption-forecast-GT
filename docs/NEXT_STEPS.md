# Next Steps

## Current status

The repository has a working parser and modeling pipeline for initial public sources:

- Banguat remittances;
- INE private construction indicators;
- INE IPMC construction-material indices.

The project is now reframed around **observable public targets** rather than a single `cement_demand_proxy`.

## Recommended target hierarchy

Prioritize targets in this order:

1. `cement_import_tons`
2. `cement_export_tons`
3. `net_cement_import_tons`
4. `cement_import_value_usd`
5. `cement_export_value_usd`
6. `construction_area_m2`
7. `construction_cost_gtq`
8. `construction_num_constructions`
9. `imae_construction_index`
10. `cement_demand_proxy` as a documented fallback only

## Immediate development target

The next useful version should add at least one stronger cement-specific target:

```text
cement_import_tons
cement_export_tons
net_cement_import_tons
```

The cleanest way is to obtain cement HS-code quantity data from WITS or UN Comtrade and convert kilograms to tons.

Useful HS codes:

```text
2523      Hydraulic cement group
252310    Cement clinkers
252321    White Portland cement
252329    Portland cement, except white
252330    Aluminous cement
252390    Other hydraulic cements
```

## Banguat product parser

The Banguat monthly product file should still be parsed, but it is likely more useful for trade **values** than tons:

```text
cement_import_value_usd
cement_export_value_usd
net_cement_import_value_usd
```

The file has a multi-row export/import header structure, so this parser should be developed carefully with tests based on extracted rows.

## IMAE parser

Add Banguat IMAE data when available:

```text
imae_general_index
imae_construction_index
imae_general_yoy
imae_construction_yoy
```

These can be used as either targets or predictors, depending on the modeling question.

## Dashboard roadmap

The dashboard should let the user select a forecast target from the available columns instead of assuming a single target.

Minimum dashboard requirements:

- target selector;
- data coverage summary;
- latest values table;
- line chart;
- model comparison when forecast outputs are available;
- methodological note explaining that the project does not claim access to confidential cement consumption data.
