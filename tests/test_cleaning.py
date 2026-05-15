import pandas as pd

from cement_forecast.cleaning import normalize_column_name, normalize_columns, aggregate_quarterly_to_monthly


def test_normalize_column_name_removes_accents_and_symbols():
    assert normalize_column_name("Costo aprox. quetzales") == "costo_aprox_quetzales"
    assert normalize_column_name("Año") == "ano"
    assert normalize_column_name(" Área Con M2 ") == "area_con_m2"


def test_normalize_columns_returns_new_column_names():
    df = pd.DataFrame({"Año": [2024], "Costo aprox. quetzales": [1000]})
    out = normalize_columns(df)
    assert list(out.columns) == ["ano", "costo_aprox_quetzales"]


def test_aggregate_quarterly_to_monthly_spreads_values():
    df = pd.DataFrame({"ano": [2024], "trimestre": [2], "num_construcciones": [90]})
    out = aggregate_quarterly_to_monthly(df, value_cols=["num_construcciones"])
    assert len(out) == 3
    assert list(out["date"]) == [
        pd.Timestamp("2024-04-01"),
        pd.Timestamp("2024-05-01"),
        pd.Timestamp("2024-06-01"),
    ]
    assert out["num_construcciones"].sum() == 90
