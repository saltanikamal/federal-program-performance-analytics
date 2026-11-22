import pandas as pd
import pytest

from src.transformation.clean_awards import awards_to_dataframe


@pytest.fixture
def sample_awards():
    return [
        {
            "internal_id": 1001,
            "Award ID": "  DEAC0494AL85000  ",
            "Recipient Name": "  Lockheed Martin Corporation  ",
            "Award Amount": "1000000.50",
            "Total Outlays": "500000.25",
            "generated_internal_id": "GEN-1001",
            "Awarding Agency": "Department of Energy",
            "Start Date": "2020-01-15",
            "End Date": "2025-01-15",
            "Description": "  Defense contract  ",
        }
    ]


def test_awards_to_dataframe_returns_dataframe(sample_awards):

    df = awards_to_dataframe(sample_awards)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1


def test_api_columns_are_renamed(sample_awards):

    df = awards_to_dataframe(sample_awards)

    expected_columns = [
        "internal_id",
        "award_id",
        "recipient_name",
        "award_amount",
        "total_outlays",
        "generated_internal_id",
        "awarding_agency",
        "start_date",
        "end_date",
        "description",
    ]

    assert list(df.columns) == expected_columns


def test_text_fields_are_trimmed(sample_awards):

    df = awards_to_dataframe(sample_awards)

    assert df.loc[0, "award_id"] == "DEAC0494AL85000"

    assert (
        df.loc[0, "recipient_name"]
        == "Lockheed Martin Corporation"
    )

    assert df.loc[0, "description"] == "Defense contract"


def test_financial_fields_are_numeric(sample_awards):

    df = awards_to_dataframe(sample_awards)

    assert pd.api.types.is_numeric_dtype(df["award_amount"])

    assert pd.api.types.is_numeric_dtype(df["total_outlays"])

    assert df.loc[0, "award_amount"] == 1000000.50

    assert df.loc[0, "total_outlays"] == 500000.25


def test_dates_are_converted_to_datetime(sample_awards):

    df = awards_to_dataframe(sample_awards)

    assert pd.api.types.is_datetime64_any_dtype(df["start_date"])

    assert pd.api.types.is_datetime64_any_dtype(df["end_date"])

    assert df.loc[0, "start_date"] == pd.Timestamp("2020-01-15")

    assert df.loc[0, "end_date"] == pd.Timestamp("2025-01-15")


def test_missing_optional_columns_are_created():

    records = [
        {
            "internal_id": 1002,
            "Award ID": "TEST-001",
            "Recipient Name": "Test Corporation",
            "Award Amount": 500000,
            "generated_internal_id": "GEN-1002",
        }
    ]

    df = awards_to_dataframe(records)

    assert "total_outlays" in df.columns
    assert "awarding_agency" in df.columns
    assert "start_date" in df.columns
    assert "end_date" in df.columns
    assert "description" in df.columns

    assert pd.isna(df.loc[0, "total_outlays"])


def test_missing_required_column_raises_error():

    records = [
        {
            "internal_id": 1003,
            "Award ID": "TEST-002",
            "Recipient Name": "Test Corporation",
            "Award Amount": 500000,
        }
    ]

    with pytest.raises(ValueError, match="Missing required API fields"):

        awards_to_dataframe(records)
