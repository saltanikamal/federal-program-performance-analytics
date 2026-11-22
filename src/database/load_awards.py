import os
from pathlib import Path
from decimal import Decimal, InvalidOperation

import numpy as np
import pandas as pd

from dotenv import load_dotenv

from sqlalchemy import (
    MetaData,
    Table,
    create_engine,
    func,
)

from sqlalchemy.dialects.postgresql import insert


# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

if not all([DB_NAME, DB_USER, DB_HOST, DB_PORT]):
    raise ValueError(
        "Missing database settings in the .env file."
    )

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}@/{DB_NAME}"
    f"?host={DB_HOST}&port={DB_PORT}"
)

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "awards_sample.csv"
)


# --------------------------------------------------
# 2. DATABASE COLUMN CONFIGURATION
# --------------------------------------------------

REQUIRED_COLUMNS = [
    "internal_id",
    "award_id",
    "recipient_name",
    "award_amount",
    "generated_internal_id",
]

OPTIONAL_COLUMNS = [
    "total_outlays",
    "awarding_agency",
    "start_date",
    "end_date",
    "description",
]

DATABASE_COLUMNS = (
    REQUIRED_COLUMNS + OPTIONAL_COLUMNS
)


# PostgreSQL numeric limits.

AWARD_AMOUNT_LIMIT = 10**13

TOTAL_OUTLAYS_LIMIT = 10**16

BIGINT_MIN = -(2**63)

BIGINT_MAX = (2**63) - 1


# --------------------------------------------------
# 3. VALIDATE REQUIRED VALUES
# --------------------------------------------------

def validate_required_values(df):

    for column in REQUIRED_COLUMNS:

        missing = df[column].isna()

        if column in [
            "award_id",
            "recipient_name",
            "generated_internal_id",
        ]:

            blank = (
                df[column]
                .astype("string")
                .str.strip()
                .eq("")
                .fillna(False)
            )

            missing = missing | blank

        if missing.any():

            raise ValueError(
                f"Required column '{column}' contains "
                f"{missing.sum()} missing or blank values."
            )


# --------------------------------------------------
# 4. VALIDATE INTERNAL IDS
# --------------------------------------------------

def validate_internal_ids(df):

    validated_ids = []

    for value in df["internal_id"]:

        # Reject missing values.

        if pd.isna(value):

            raise ValueError(
                "internal_id contains missing or invalid values."
            )

        # Convert using Decimal to preserve precision.

        try:

            numeric_value = Decimal(str(value).strip())

        except (InvalidOperation, ValueError):

            raise ValueError(
                "internal_id contains missing or invalid values."
            )

        # Reject infinity and NaN.

        if not numeric_value.is_finite():

            raise ValueError(
                "internal_id contains infinite values."
            )

        # Reject fractional values.

        if numeric_value != numeric_value.to_integral_value():

            raise ValueError(
                "internal_id must contain whole numbers."
            )

        # Check PostgreSQL BIGINT boundaries.

        if (
            numeric_value < Decimal(BIGINT_MIN)
            or numeric_value > Decimal(BIGINT_MAX)
        ):

            raise ValueError(
                "internal_id exceeds PostgreSQL BIGINT limits."
            )

        validated_ids.append(
            int(numeric_value)
        )

    # Convert validated IDs to pandas int64.

    df["internal_id"] = pd.Series(
        validated_ids,
        index=df.index,
        dtype="int64",
    )

    # Reject duplicate IDs.

    if df["internal_id"].duplicated().any():

        raise ValueError(
            "The CSV contains duplicate internal_id values."
        )


# --------------------------------------------------
# 5. VALIDATE AWARD AMOUNTS
# --------------------------------------------------

def validate_award_amounts(df):

    df["award_amount"] = pd.to_numeric(
        df["award_amount"],
        errors="coerce",
    )

    if df["award_amount"].isna().any():

        raise ValueError(
            "award_amount contains missing or invalid values."
        )

    if not np.isfinite(
        df["award_amount"]
    ).all():

        raise ValueError(
            "award_amount contains infinite values."
        )

    if (df["award_amount"] < 0).any():

        raise ValueError(
            "award_amount cannot contain negative values."
        )

    if (
        df["award_amount"].abs()
        >= AWARD_AMOUNT_LIMIT
    ).any():

        raise ValueError(
            "award_amount exceeds PostgreSQL NUMERIC(15,2) limits."
        )


# --------------------------------------------------
# 6. VALIDATE TOTAL OUTLAYS
# --------------------------------------------------

def validate_total_outlays(df):

    original_outlays = df["total_outlays"].copy()

    df["total_outlays"] = pd.to_numeric(
        original_outlays,
        errors="coerce",
    )

    invalid_outlays = (
        original_outlays.notna()
        & df["total_outlays"].isna()
    )

    if invalid_outlays.any():

        raise ValueError(
            f"Found {invalid_outlays.sum()} invalid "
            "total_outlays values."
        )

    valid_outlays = df["total_outlays"].dropna()

    if not np.isfinite(valid_outlays).all():

        raise ValueError(
            "total_outlays contains infinite values."
        )

    if (
        valid_outlays.abs()
        >= TOTAL_OUTLAYS_LIMIT
    ).any():

        raise ValueError(
            "total_outlays exceeds PostgreSQL NUMERIC(18,2) limits."
        )

    negative_outlays = (
        df["total_outlays"] < 0
    ).sum()

    if negative_outlays > 0:

        print(
            f"WARNING: {negative_outlays} record(s) "
            "contain negative total outlays. "
            "Values will be retained."
        )


# --------------------------------------------------
# 7. CONVERT DATE COLUMNS
# --------------------------------------------------

def validate_dates(df):
    """
    Convert date columns to datetime and reject invalid dates.

    Checks:
    1. Converts start_date and end_date to datetime.
    2. Allows missing dates.
    3. Supports mixed date formats.
    4. Rejects invalid non-missing dates.
    """

    for column in ["start_date", "end_date"]:

        original_dates = df[column].copy()

        # Convert dates while supporting mixed formats.

        df[column] = pd.to_datetime(
            original_dates,
            format="mixed",
            errors="coerce",
        )

        # Identify invalid dates.

        invalid_dates = (
            original_dates.notna()
            & df[column].isna()
        )

        if invalid_dates.any():

            raise ValueError(
                f"Column '{column}' contains "
                f"{invalid_dates.sum()} invalid dates."
            )

        # Convert datetime values to Python date objects.

        df[column] = df[column].dt.date

    return df


# --------------------------------------------------
# 8. PREPARE DATABASE RECORDS
# --------------------------------------------------

def prepare_database_records(df):

    records_df = df[DATABASE_COLUMNS].copy()

    records_df = (
        records_df
        .astype(object)
        .where(pd.notna(records_df), None)
    )

    return records_df.to_dict(
        orient="records"
    )


# --------------------------------------------------
# 9. LOAD AWARDS INTO POSTGRESQL
# --------------------------------------------------

def load_awards():

    # Check processed CSV.

    if not CSV_PATH.exists():

        raise FileNotFoundError(
            f"Processed CSV file not found: {CSV_PATH}"
        )

    # Read processed data.

    df = pd.read_csv(CSV_PATH)

    # Check required columns.

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Handle empty CSV.

    if df.empty:

        print(
            "The CSV contains no records. Nothing to load."
        )

        return

    # Add optional columns if missing.

    for column in OPTIONAL_COLUMNS:

        if column not in df.columns:

            df[column] = pd.NA

    # --------------------------------------------------
    # DATA VALIDATION
    # --------------------------------------------------

    validate_required_values(df)

    validate_internal_ids(df)

    validate_award_amounts(df)

    validate_total_outlays(df)

    validate_dates(df)

    # --------------------------------------------------
    # PREPARE DATABASE RECORDS
    # --------------------------------------------------

    rows = prepare_database_records(df)

    print(
        f"Prepared {len(rows)} records for PostgreSQL."
    )

    # --------------------------------------------------
    # 10. CONNECT TO POSTGRESQL
    # --------------------------------------------------

    engine = create_engine(
        DATABASE_URL
    )

    try:

        metadata = MetaData()

        awards_table = Table(
            "awards",
            metadata,
            autoload_with=engine,
        )

        # Confirm database columns.

        missing_database_columns = [
            column
            for column in DATABASE_COLUMNS
            if column not in awards_table.c
        ]

        if missing_database_columns:

            raise ValueError(
                "Database table is missing columns: "
                f"{missing_database_columns}"
            )

        # --------------------------------------------------
        # 11. INSERT OR UPDATE RECORDS (UPSERT)
        # --------------------------------------------------

        statement = insert(
            awards_table
        ).values(rows)

        update_values = {}

        for column in DATABASE_COLUMNS:

            if column == "internal_id":
                continue

            incoming_value = getattr(
                statement.excluded,
                column,
            )

            # Required values replace existing values.

            if column in REQUIRED_COLUMNS:

                update_values[column] = incoming_value

            # Optional NULL values preserve existing data.

            else:

                update_values[column] = func.coalesce(
                    incoming_value,
                    awards_table.c[column],
                )

        statement = statement.on_conflict_do_update(
            index_elements=[
                awards_table.c.internal_id
            ],
            set_=update_values,
        )

        # --------------------------------------------------
        # 12. EXECUTE DATABASE TRANSACTION
        # --------------------------------------------------

        with engine.begin() as connection:

            result = connection.execute(
                statement
            )

        print(
            "Database loading completed successfully."
        )

        print(
            f"Records inserted or updated: {result.rowcount}"
        )

    finally:

        engine.dispose()


# --------------------------------------------------
# 13. RUN SCRIPT DIRECTLY
# --------------------------------------------------

if __name__ == "__main__":

    load_awards()
