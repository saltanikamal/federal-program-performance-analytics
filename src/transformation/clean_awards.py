import pandas as pd


# ==========================================================
# REQUIRED AWARD COLUMNS
# ==========================================================

REQUIRED_COLUMNS = [
    "internal_id",
    "award_id",
    "recipient_name",
    "award_amount",
    "generated_internal_id",
]


# ==========================================================
# NUMERIC CONVERSION HELPER
# ==========================================================

def convert_numeric_column(df, column, required=False):
    """
    Convert a DataFrame column to numeric values.

    Invalid nonempty values raise an error instead of
    silently becoming missing values.

    Args:
        df: Input DataFrame.
        column: Column to convert.
        required: Whether the column must exist.

    Returns:
        Updated DataFrame.
    """

    if column not in df.columns:

        if required:
            raise ValueError(
                f"Missing required column: {column}"
            )

        df[column] = pd.NA
        return df

    original = df[column]

    # Treat empty strings as missing values.
    normalized = original.replace(
        r"^\s*$",
        pd.NA,
        regex=True
    )

    converted = pd.to_numeric(
        normalized,
        errors="coerce"
    )

    # Identify invalid values separately from missing values.
    invalid_values = (
        normalized.notna()
        & converted.isna()
    )

    if invalid_values.any():

        raise ValueError(
            f"{column} contains invalid numeric values."
        )

    df[column] = converted

    return df


# ==========================================================
# DATE CONVERSION HELPER
# ==========================================================

def convert_date_column(df, column):
    """
    Convert a DataFrame column to datetime.

    Missing dates remain NaT.
    Invalid nonempty dates raise an error.
    """

    if column not in df.columns:
        df[column] = pd.NaT
        return df

    original = df[column]

    normalized = original.replace(
        r"^\s*$",
        pd.NA,
        regex=True
    )

    converted = pd.to_datetime(
        normalized,
        errors="coerce"
    )

    invalid_dates = (
        normalized.notna()
        & converted.isna()
    )

    if invalid_dates.any():

        raise ValueError(
            f"{column} contains invalid date values."
        )

    df[column] = converted

    return df


# ==========================================================
# MAIN CLEANING FUNCTION
# ==========================================================

def awards_to_dataframe(records):
    """
    Convert USAspending API records into a clean DataFrame.

    Processing steps:

    1. Convert API records to DataFrame.
    2. Rename API columns.
    3. Check required columns.
    4. Clean text fields.
    5. Convert internal identifiers.
    6. Convert financial fields.
    7. Convert date fields.
    8. Standardize output column order.

    Returns:
        pd.DataFrame: Cleaned award records.
    """

    # ------------------------------------------------------
    # 1. Validate input
    # ------------------------------------------------------

    if not isinstance(records, list):
        raise TypeError(
            "Input records must be a list."
        )

    if not records:
        raise ValueError(
            "No award records were provided."
        )

    # ------------------------------------------------------
    # 2. Convert records to DataFrame
    # ------------------------------------------------------

    df = pd.DataFrame(records)

    # ------------------------------------------------------
    # 3. Rename API fields
    # ------------------------------------------------------

    df = df.rename(
        columns={
            "Award ID": "award_id",
            "Recipient Name": "recipient_name",
            "Award Amount": "award_amount",
            "Total Outlays": "total_outlays",
            "Awarding Agency": "awarding_agency",
            "Start Date": "start_date",
            "End Date": "end_date",
            "Description": "description",
        }
    )

    # ------------------------------------------------------
    # 4. Check required columns
    # ------------------------------------------------------

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing required API fields: {missing_columns}"
        )

    # ------------------------------------------------------
    # 5. Clean text fields
    # ------------------------------------------------------

    text_columns = [
        "award_id",
        "recipient_name",
        "generated_internal_id",
        "awarding_agency",
        "description",
    ]

    for column in text_columns:

        if column not in df.columns:
            df[column] = pd.NA

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    # ------------------------------------------------------
    # 6. Convert internal IDs
    # ------------------------------------------------------

    df["internal_id"] = pd.to_numeric(
        df["internal_id"],
        errors="coerce"
    )

    # ------------------------------------------------------
    # 7. Convert financial fields
    # ------------------------------------------------------

    df = convert_numeric_column(
        df,
        "award_amount",
        required=True
    )

    df = convert_numeric_column(
        df,
        "total_outlays",
        required=False
    )

    # ------------------------------------------------------
    # 8. Convert dates
    # ------------------------------------------------------

    df = convert_date_column(
        df,
        "start_date"
    )

    df = convert_date_column(
        df,
        "end_date"
    )

    # ------------------------------------------------------
    # 9. Standardize output columns
    # ------------------------------------------------------

    output_columns = [
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

    return df[output_columns]
