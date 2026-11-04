"""Tests for transaction obligation accounting and federal fiscal-year boundaries."""
import pandas as pd
import pytest

from src.analytics.transaction_obligations import (
    prepare_transactions,
    summarize_transactions,
)


def sample():
    return pd.DataFrame([
        {"id": "a", "action_date": "2017-05-30",
         "federal_action_obligation": "-792802800", "action_type_description": "FUNDING ONLY ACTION"},
        {"id": "b", "action_date": "2017-05-31",
         "federal_action_obligation": -554346900, "action_type_description": "FUNDING ONLY ACTION"},
        {"id": "c", "action_date": "2017-06-01",
         "federal_action_obligation": 516070700.39, "action_type_description": "FUNDING ONLY ACTION"},
        {"id": "d", "action_date": "2017-07-06",
         "federal_action_obligation": 0, "action_type_description": "OTHER ADMINISTRATIVE ACTION"},
        {"id": "e", "action_date": "2017-10-31",
         "federal_action_obligation": -100, "action_type_description": "FUNDING ONLY ACTION"},
    ])


def test_signed_totals_and_zero_actions():
    result = summarize_transactions(sample(), year=2017)
    assert result["transaction_count"] == 5
    assert result["positive_obligations"] == pytest.approx(516070700.39)
    assert result["negative_obligations"] == pytest.approx(-1347149800.0)
    assert result["net_obligations"] == pytest.approx(-831079099.61)
    assert result["zero_dollar_transactions"] == 1
    assert result["largest_reductions"][0]["id"] == "a"


def test_fiscal_year_boundary():
    fiscal = summarize_transactions(sample(), year=2017, year_basis="fiscal")
    assert fiscal["transaction_count"] == 4
    assert fiscal["negative_obligations"] == pytest.approx(-1347149700)
    october = summarize_transactions(sample(), year=2018, year_basis="fiscal")
    assert october["transaction_count"] == 1
    assert october["net_obligations"] == -100


def test_invalid_year_basis():
    with pytest.raises(ValueError, match="year_basis"):
        summarize_transactions(sample(), year_basis="other")


def test_duplicate_id_rejected():
    df = sample()
    df.loc[1, "id"] = "a"
    with pytest.raises(ValueError, match="Duplicate"):
        prepare_transactions(df)


def test_invalid_dates_and_non_numeric_amounts_rejected():
    df = sample()
    df.loc[0, "action_date"] = "not-a-date"
    with pytest.raises(ValueError, match="action_date"):
        prepare_transactions(df)
    df = sample()
    df.loc[0, "federal_action_obligation"] = "not-an-amount"
    with pytest.raises(ValueError, match="Non-numeric"):
        prepare_transactions(df)


def test_empty_input_with_expected_columns():
    result = summarize_transactions(
        pd.DataFrame(columns=["id", "action_date", "federal_action_obligation"])
    )
    assert result["transaction_count"] == 0
    assert result["net_obligations"] == 0
    assert result["monthly"] == []
