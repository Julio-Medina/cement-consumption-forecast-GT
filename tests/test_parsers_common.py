import pandas as pd
import pytest

from cement_forecast.parsers.common import (
    MonthParseError,
    build_monthly_date,
    coerce_numeric_series,
    parse_month_name,
)


def test_parse_month_name_spanish_and_numeric():
    assert parse_month_name("enero") == 1
    assert parse_month_name("Septiembre") == 9
    assert parse_month_name("dic") == 12
    assert parse_month_name(4) == 4


def test_parse_month_name_invalid_raises():
    with pytest.raises(MonthParseError):
        parse_month_name("not a month")


def test_coerce_numeric_series_handles_spanish_decimal_format():
    values = pd.Series(["1.234,50", "Q 2,000.25", "-", "3,500"])
    result = coerce_numeric_series(values)
    assert result.iloc[0] == pytest.approx(1234.50)
    assert result.iloc[1] == pytest.approx(2000.25)
    assert pd.isna(result.iloc[2])
    assert result.iloc[3] == pytest.approx(3500.0)


def test_build_monthly_date_from_year_and_month_name():
    df = pd.DataFrame({"ano": [2024, 2024], "mes": ["enero", "febrero"]})
    dates = build_monthly_date(df, year_col="ano", month_col="mes")
    assert list(dates.dt.strftime("%Y-%m-%d")) == ["2024-01-01", "2024-02-01"]
