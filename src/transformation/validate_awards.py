import warnings

import numpy as np
import pandas as pd


# ==========================================================
# REQUIRED COLUMNS
# ==========================================================

REQUIRED_COLUMNS = [
    "internal_id",
    "award_id",
    "recipient_name",
    "award_amount",
    "generated_internal_id",
]


# ==========================================================
# MAIN VALIDATION FUNCTION
# ==========================================================

def validate_awards(df):
    """
    Validate cleaned federal award records.

    Validation checks:

    1. Input must be a pandas DataFrame.
    2. DataFrame cannot be empty.
    3. Required columns must exist.
    4. Required fields cannot contain missing values.
    5. Required text fields cannot be empty.
    6. Internal IDs must be positive integers.
    7. Internal IDs must be unique.
    8. Award amounts must be numeric and finite.
    9. Award amounts cannot be negative.
    10. Duplicate award IDs generate warnings.
    11. Optional total outlays must be numeric and finite.

    Returns:
        pd.DataFrame: Validated copy of the input DataFrame.
    """

    # ------------------------------------------------------
    # 1. Validate input type
    # ------------------------------------------------------

    if not isinstance(df, pd.DataFrame):

        raise TypeError(
            "Input must be a pandas DataFrame."
        )

    # ------------------------------------------------------
    # 2. Check empty DataFrame
    # ------------------------------------------------------

    if df.empty:

        raise ValueError(
            "Award DataFrame cannot be empty."
        )

    # Work on a copy to protect original data.
    validated_df = df.copy(deep=True)

    # ------------------------------------------------------
    # 3. Check required columns
    # ------------------------------------------------------

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in validated_df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # ------------------------------------------------------
    # 4. Check missing and empty values
    # ------------------------------------------------------

    for column in REQUIRED_COLUMNS:

        if validated_df[column].isna().any():

            raise ValueError(
                f"{column} contains missing values."
            )

        empty_values = (
            validated_df[column]
            .astype("string")
            .str.strip()
            .eq("")
        )

        if empty_values.any():

            raise ValueError(
                f"{column} contains empty values."
            )

    # ------------------------------------------------------
    # 5. Validate internal IDs
    # ------------------------------------------------------

    internal_ids = pd.to_numeric(
        validated_df["internal_id"],
        errors="coerce"
    )

    if internal_ids.isna().any():

        raise ValueError(
            "internal_id must contain valid integer identifiers."
        )

    if not np.isfinite(
        internal_ids.to_numpy()
    ).all():

        raise ValueError(
            "internal_id must contain finite numeric values."
        )

    if not (internal_ids % 1 == 0).all():

        raise ValueError(
            "internal_id must contain integer identifiers."
        )

    if (internal_ids <= 0).any():

        raise ValueError(
            "internal_id must contain positive integer identifiers."
        )

    # Check uniqueness.
    if internal_ids.duplicated().any():

        raise ValueError(
            "internal_id contains duplicate identifiers."
        )

    validated_df["internal_id"] = internal_ids.astype("int64")

    # ------------------------------------------------------
    # 6. Validate award amounts
    # ------------------------------------------------------

    award_amounts = pd.to_numeric(
        validated_df["award_amount"],
        errors="coerce"
    )

    if award_amounts.isna().any():

        raise ValueError(
            "award_amount must contain valid numeric values."
        )

    if not np.isfinite(
        award_amounts.to_numpy()
    ).all():

        raise ValueError(
            "award_amount must contain finite numeric values."
        )

    if (award_amounts < 0).any():

        raise ValueError(
            "award_amount cannot contain negative values."
        )

    validated_df["award_amount"] = award_amounts

    # ------------------------------------------------------
    # 7. Check duplicate award IDs
    # ------------------------------------------------------

    if validated_df["award_id"].duplicated().any():

        warnings.warn(
            "Duplicate award_id values detected.",
            UserWarning
        )

    # ------------------------------------------------------
    # 8. Validate optional total outlays
    # ------------------------------------------------------

    if "total_outlays" in validated_df.columns:

        outlays = pd.to_numeric(
            validated_df["total_outlays"],
            errors="coerce"
        )

        # Identify invalid values while allowing missing values.
        invalid_outlays = (
            validated_df["total_outlays"].notna()
            & outlays.isna()
        )

        if invalid_outlays.any():

            raise ValueError(
                "total_outlays must contain numeric values."
            )

        # Reject infinity and negative infinity.
        if not np.isfinite(
            outlays.dropna().to_numpy()
        ).all():

            raise ValueError(
                "total_outlays must contain finite numeric values."
            )

        validated_df["total_outlays"] = outlays

    # ------------------------------------------------------
    # 9. Validation summary
    # ------------------------------------------------------

    print("Award validation successful.")

    print(
        f"Total records validated: {len(validated_df)}"
    )

    print(
        f"Unique internal IDs: "
        f"{validated_df['internal_id'].nunique()}"
    )

    print(
        f"Unique award IDs: "
        f"{validated_df['award_id'].nunique()}"
    )

    print(
        f"Unique generated internal IDs: "
        f"{validated_df['generated_internal_id'].nunique()}"
    )

    # ------------------------------------------------------
    # 10. Return validated DataFrame
    # ------------------------------------------------------

    return validated_df
