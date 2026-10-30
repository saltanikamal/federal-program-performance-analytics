import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.dialects.postgresql import insert


# 1. Find the project folder
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 2. Load database settings
load_dotenv(PROJECT_ROOT / ".env")

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

if not all([DB_NAME, DB_USER, DB_HOST, DB_PORT]):
    raise ValueError("Missing database settings in the .env file.")

# 3. Build the database connection
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}@/{DB_NAME}"
    f"?host={DB_HOST}&port={DB_PORT}"
)

# 4. Locate the processed CSV
CSV_PATH = PROJECT_ROOT / "data" / "processed" / "awards_sample.csv"

# 5. Define the columns to load
REQUIRED_COLUMNS = [
    "internal_id",
    "award_id",
    "recipient_name",
    "award_amount",
    "generated_internal_id",
]

DATABASE_COLUMNS = REQUIRED_COLUMNS + [
    "awarding_agency",
    "start_date",
    "end_date",
    "description",
]


def load_awards():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Processed CSV file not found: {CSV_PATH}"
        )

    df = pd.read_csv(CSV_PATH)

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df.empty:
        print("The CSV contains no records. Nothing to load.")
        return

    # Add optional fields if they are absent from an older CSV.
    for column in DATABASE_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    # Validate internal IDs.
    df["internal_id"] = pd.to_numeric(
        df["internal_id"],
        errors="coerce",
    )

    if df["internal_id"].isna().any():
        raise ValueError("internal_id cannot contain missing or invalid values.")

    if (df["internal_id"] % 1 != 0).any():
        raise ValueError("internal_id must contain whole numbers.")

    df["internal_id"] = df["internal_id"].astype("int64")

    if df["internal_id"].duplicated().any():
        raise ValueError("The CSV contains duplicate internal_id values.")

    # Validate award amounts.
    df["award_amount"] = pd.to_numeric(
        df["award_amount"],
        errors="coerce",
    )

    if df["award_amount"].isna().any():
        raise ValueError("award_amount contains missing or invalid values.")

    if (df["award_amount"] < 0).any():
        raise ValueError("award_amount cannot be negative.")

    # Convert dates to Python date objects for PostgreSQL.
    for column in ["start_date", "end_date"]:
        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
        ).dt.date

    # Convert missing values to None for SQL.
    rows = (
        df[DATABASE_COLUMNS]
        .astype(object)
        .where(pd.notna(df[DATABASE_COLUMNS]), None)
        .to_dict(orient="records")
    )

    print(f"Prepared {len(rows)} records for PostgreSQL.")

    # 6. Insert or update records
    engine = create_engine(DATABASE_URL)

    try:
        metadata = MetaData()

        awards_table = Table(
            "awards",
            metadata,
            autoload_with=engine,
        )

        statement = insert(awards_table).values(rows)

        # Update all columns except the primary key when internal_id matches.
        update_values = {
            column: getattr(statement.excluded, column)
            for column in DATABASE_COLUMNS
            if column != "internal_id"
        }

        statement = statement.on_conflict_do_update(
            index_elements=[awards_table.c.internal_id],
            set_=update_values,
        )

        with engine.begin() as connection:
            result = connection.execute(statement)

        print("Database loading completed successfully.")
        print(f"Records inserted or updated: {result.rowcount}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    load_awards()
