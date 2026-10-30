import pandas as pd


REQUIRED_COLUMNS = [
    "internal_id",
    "award_id",
    "recipient_name",
    "award_amount",
    "generated_internal_id",
]

OPTIONAL_COLUMNS = [
    "awarding_agency",
    "start_date",
    "end_date",
    "description",
]


def validate_awards(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate federal award records.

    Checks:
    1. The DataFrame is not empty.
    2. Required columns exist.
    3. Required fields are not missing.
    4. Internal IDs are valid and unique.
    5. Generated internal IDs are present and unique.
    6. Award amounts are numeric and non-negative.
    7. Optional date fields contain valid dates when supplied.
    8. Duplicate award IDs are reported as a warning.

    Returns a validated copy of the DataFrame.
    Raises ValueError when critical checks fail.
    """

    # CHECK 1: Ensure records exist.
    if df.empty:
        raise ValueError(
            "Cannot validate an empty DataFrame."
        )

    # CHECK 2: Ensure required columns exist.
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    validated_df = df.copy()

    # Add optional columns if they are absent.
    for column in OPTIONAL_COLUMNS:
        if column not in validated_df.columns:
            validated_df[column] = pd.NA

    # CHECK 3: Clean text fields.
    text_fields = [
        "award_id",
        "recipient_name",
        "generated_internal_id",
        "awarding_agency",
        "description",
    ]

    for column in text_fields:
        validated_df[column] = (
            validated_df[column]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    # CHECK 4: Validate internal IDs.
    internal_ids = pd.to_numeric(
        validated_df["internal_id"],
        errors="coerce",
    )

    invalid_internal_ids = (
        internal_ids.isna()
        | (internal_ids % 1 != 0)
    )

    if invalid_internal_ids.any():
        raise ValueError(
            "Validation failed: internal_id must contain "
            "valid integer identifiers."
        )

    if internal_ids.duplicated().any():
        raise ValueError(
            "Validation failed: duplicate internal_id values."
        )

    validated_df["internal_id"] = internal_ids.astype("int64")

    # CHECK 5: Validate generated identifiers.
    generated_ids = validated_df["generated_internal_id"]

    if generated_ids.isna().any():
        raise ValueError(
            "Validation failed: generated_internal_id "
            "cannot be missing."
        )

    if generated_ids.duplicated().any():
        raise ValueError(
            "Validation failed: duplicate generated_internal_id "
            "values."
        )

    # CHECK 6: Validate award amounts.
    validated_df["award_amount"] = pd.to_numeric(
        validated_df["award_amount"],
        errors="coerce",
    )

    invalid_amounts = (
        validated_df["award_amount"].isna()
        | (validated_df["award_amount"] < 0)
    )

    if invalid_amounts.any():
        raise ValueError(
            "Validation failed: award_amount must be numeric "
            "and non-negative."
        )

    # CHECK 7: Validate required text fields.
    required_text_fields = [
        "award_id",
        "recipient_name",
        "generated_internal_id",
    ]

    missing_required = (
        validated_df[required_text_fields]
        .isna()
        .any(axis=1)
    )

    if missing_required.any():
        invalid_count = int(missing_required.sum())

        raise ValueError(
            f"Validation failed: {invalid_count} record(s) "
            "have missing required fields."
        )

    # CHECK 8: Validate dates when present.
    for column in ["start_date", "end_date"]:
        original_values = validated_df[column]

        parsed_dates = pd.to_datetime(
            original_values,
            errors="coerce",
        )

        invalid_dates = (
            original_values.notna()
            & parsed_dates.isna()
        )

        if invalid_dates.any():
            raise ValueError(
                f"Validation failed: {column} contains "
                "invalid date values."
            )

        validated_df[column] = parsed_dates

    # Warn about duplicate award IDs without stopping the pipeline.
    duplicate_awards = validated_df["award_id"].duplicated(
        keep=False
    )

    duplicate_award_count = int(
        validated_df.loc[
            duplicate_awards, "award_id"
        ].nunique()
    )

    print(
        f"Validation passed: {len(validated_df)} records "
        "passed critical checks."
    )

    print(
        f"Unique internal IDs: "
        f"{validated_df['internal_id'].nunique()}"
    )

    print(
        f"Unique generated internal IDs: "
        f"{validated_df['generated_internal_id'].nunique()}"
    )

    if duplicate_award_count:
        print(
            "WARNING: "
            f"{duplicate_award_count} award ID value(s) "
            "appear in multiple records."
        )
    else:
        print("No duplicate award IDs detected.")

    return validated_df
