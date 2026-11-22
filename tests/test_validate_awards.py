import pandas as pd
import pytest

from src.transformation.validate_awards import validate_awards


# --------------------------------------------------
# Sample award data
# --------------------------------------------------

def create_sample_awards():

    return pd.DataFrame({
        "internal_id": [1001, 1002, 1003],
        "award_id": [
            "DEAC0494AL85000",
            "DEAC0494AL85001",
            "DEAC0494AL85002"
        ],
        "recipient_name": [
            "Lockheed Martin Corp",
            "Boeing Company",
            "General Dynamics"
        ],
        "award_amount": [
            1000000.00,
            2000000.00,
            3000000.00
        ],
        "generated_internal_id": [
            "ID001",
            "ID002",
            "ID003"
        ]
    })


# --------------------------------------------------
# Test 1: Successful validation
# --------------------------------------------------

def test_valid_awards_pass():

    df = create_sample_awards()

    result = validate_awards(df)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert result["internal_id"].is_unique


# --------------------------------------------------
# Test 2: Missing required column
# --------------------------------------------------

def test_missing_required_column_fails():

    df = create_sample_awards()

    df = df.drop(columns=["recipient_name"])

    with pytest.raises(ValueError, match="Missing required columns"):

        validate_awards(df)


# --------------------------------------------------
# Test 3: Missing required value
# --------------------------------------------------

def test_missing_required_value_fails():

    df = create_sample_awards()

    df.loc[0, "recipient_name"] = None

    with pytest.raises(ValueError, match="missing values"):

        validate_awards(df)


# --------------------------------------------------
# Test 4: Negative award amount
# --------------------------------------------------

def test_negative_award_amount_fails():

    df = create_sample_awards()

    df.loc[0, "award_amount"] = -1000.00

    with pytest.raises(ValueError, match="negative values"):

        validate_awards(df)


# --------------------------------------------------
# Test 5: Non-numeric award amount
# --------------------------------------------------

def test_non_numeric_award_amount_fails():

    df = create_sample_awards()

    # Construct a new object column instead of assigning
    # a string into an existing float64 column.

    df["award_amount"] = df["award_amount"].astype(object)

    df.loc[0, "award_amount"] = "invalid"

    with pytest.raises(ValueError, match="valid numeric values"):

        validate_awards(df)


# --------------------------------------------------
# Test 6: Duplicate internal IDs
# --------------------------------------------------

def test_duplicate_internal_id_fails():

    df = create_sample_awards()

    df.loc[1, "internal_id"] = 1001

    with pytest.raises(ValueError, match="duplicate"):

        validate_awards(df)


# --------------------------------------------------
# Test 7: Non-integer internal ID
# --------------------------------------------------

def test_non_integer_internal_id_fails():

    df = create_sample_awards()

    # Use object dtype to allow testing an invalid ID.

    df["internal_id"] = df["internal_id"].astype(object)

    df.loc[0, "internal_id"] = 1001.5

    with pytest.raises(ValueError, match="integer"):

        validate_awards(df)


# --------------------------------------------------
# Test 8: Duplicate award ID generates warning
# --------------------------------------------------

def test_duplicate_award_id_generates_warning():

    df = create_sample_awards()

    df.loc[1, "award_id"] = "DEAC0494AL85000"

    with pytest.warns(UserWarning, match="Duplicate award_id"):

        result = validate_awards(df)

    assert len(result) == 3


# --------------------------------------------------
# Test 9: Zero award amount is valid
# --------------------------------------------------

def test_zero_award_amount_passes():

    df = create_sample_awards()

    df.loc[0, "award_amount"] = 0

    result = validate_awards(df)

    assert result.loc[0, "award_amount"] == 0


# --------------------------------------------------
# Test 10: Original DataFrame remains unchanged
# --------------------------------------------------

def test_validation_does_not_modify_original_dataframe():

    df = create_sample_awards()

    original_df = df.copy(deep=True)

    validate_awards(df)

    pd.testing.assert_frame_equal(df, original_df)
