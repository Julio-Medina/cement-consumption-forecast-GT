from pathlib import Path

import pandas as pd

from cement_forecast.parsers.official import (
    parse_banguat_remittances,
    parse_ine_construction,
    parse_ine_ipmc,
)


def test_parse_banguat_remittances_wide_matrix(tmp_path: Path):
    path = tmp_path / "remesas.xlsx"
    df = pd.DataFrame(
        {
            "Mes": ["Enero", "Febrero", "Marzo", "Total"],
            2020: [100.0, 110.0, 120.0, 330.0],
            2021: [130.0, 140.0, 150.0, 420.0],
        }
    )
    with pd.ExcelWriter(path) as writer:
        df.to_excel(writer, sheet_name="2002-2021", index=False, startrow=9)

    result = parse_banguat_remittances(path)

    assert list(result.columns) == ["date", "remittances_usd_millions"]
    assert result.shape[0] == 6
    assert not result["date"].isna().any()
    jan_2020 = result.loc[result["date"].eq(pd.Timestamp("2020-01-01")), "remittances_usd_millions"].iloc[0]
    assert jan_2020 == 100.0


def test_parse_ine_construction_aggregates_quarterly_rows_to_months(tmp_path: Path):
    path = tmp_path / "construction.xlsx"
    df = pd.DataFrame(
        {
            "ano": [2023, 2023],
            "trimestre": [2, 2],
            "departamento": [1, 1],
            "municipio": [1, 2],
            "num_construcciones": [3, 6],
            "area_con_m2": [300, 600],
            "costo_aprox_quetzales": [9000, 18000],
        }
    )
    df.to_excel(path, sheet_name="Hoja1", index=False)

    result = parse_ine_construction(path)

    assert list(result["date"].dt.strftime("%Y-%m-%d")) == [
        "2023-04-01",
        "2023-05-01",
        "2023-06-01",
    ]
    assert result["construction_num_constructions"].tolist() == [3.0, 3.0, 3.0]
    assert result["construction_area_m2"].tolist() == [300.0, 300.0, 300.0]
    assert result["construction_cost_gtq"].tolist() == [9000.0, 9000.0, 9000.0]


def test_parse_ine_ipmc_two_row_year_month_header(tmp_path: Path):
    path = tmp_path / "ipmc.xlsx"
    raw = pd.DataFrame(
        [
            ["No", "Material", "Indice base diciembre 2018", "Indices 2019", None, "Indices 2020", None],
            [None, None, None, "Enero", "Febrero", "Enero", "Febrero"],
            ["C", "Agregados y aglomerantes", None, None, None, None, None],
            [7, "Cemento gris tipo portland", 100, 101.0, 102.0, 103.0, 104.0],
            [8, "Arena de rio", 100, 99.0, 100.0, 101.0, 102.0],
            [9, "Acero estructural", 100, 200.0, 201.0, 202.0, 203.0],
        ]
    )
    with pd.ExcelWriter(path) as writer:
        raw.to_excel(writer, sheet_name="Publicación Histórico 2026", index=False, header=False)

    result = parse_ine_ipmc(path, material_keywords=["cemento", "arena"])

    assert "ipmc_cement_related_index" in result.columns
    assert result.shape[0] == 4
    jan_2019 = result.loc[result["date"].eq(pd.Timestamp("2019-01-01")), "ipmc_cement_related_index"].iloc[0]
    assert jan_2019 == 100.0
