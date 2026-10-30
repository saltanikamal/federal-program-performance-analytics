import json
from pathlib import Path

from src.ingestion.usa_spending_api import fetch_awards
from src.transformation.clean_awards import awards_to_dataframe
from src.transformation.validate_awards import validate_awards
from src.database.load_awards import load_awards


def run_pipeline():
    """
    Run the complete federal spending analytics pipeline.

    Pipeline stages:
    1. Fetch data from USAspending.gov.
    2. Save raw data as JSON.
    3. Transform and clean the data.
    4. Validate transformed records.
    5. Perform additional data-quality checks.
    6. Save validated data as CSV.
    7. Load records into PostgreSQL.
    8. Report pipeline results.
    """

    # STEP 1: Identify the project root.
    project_root = Path(__file__).resolve().parents[2]

    # STEP 2: Define output file paths.
    raw_file = (
        project_root
        / "data"
        / "raw"
        / "awards_sample.json"
    )

    processed_file = (
        project_root
        / "data"
        / "processed"
        / "awards_sample.csv"
    )

    # STEP 3: Create output directories if necessary.
    raw_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    processed_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # STEP 4: Fetch data from USAspending.gov.
    print("\nSTEP 1: DATA INGESTION")

    records = fetch_awards()

    if not records:
        raise ValueError(
            "No award records returned by the API."
        )

    print(
        f"Fetched {len(records)} records from "
        "USAspending API."
    )

    # STEP 5: Save the original API response.
    print("\nSTEP 2: SAVE RAW DATA")

    with raw_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            records,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Raw data saved to: {raw_file}")

    # STEP 6: Transform and clean the records.
    print("\nSTEP 3: DATA TRANSFORMATION")

    df = awards_to_dataframe(records)

    if df.empty:
        raise ValueError(
            "The transformation produced an empty DataFrame."
        )

    print(f"Transformed {len(df)} records.")

    # STEP 7: Validate the transformed records.
    print("\nSTEP 4: DATA VALIDATION")

    df = validate_awards(df)

    # STEP 8: Perform additional data-quality reporting.
    print("\nSTEP 5: DATA QUALITY REPORT")

    print(f"\nDataFrame dimensions: {df.shape}")

    print("\nColumn names:")
    print(df.columns.tolist())

    print("\nColumn data types:")
    print(df.dtypes)

    print("\nMissing values per column:")
    print(df.isna().sum())

    duplicate_count = int(df.duplicated().sum())

    print(f"\nDuplicate rows: {duplicate_count}")

    # STEP 9: Save validated data as CSV.
    print("\nSTEP 6: SAVE PROCESSED DATA")

    df.to_csv(
        processed_file,
        index=False,
    )

    print(f"Processed data saved to: {processed_file}")

    # STEP 10: Load the processed data into PostgreSQL.
    print("\nSTEP 7: DATABASE LOADING")

    load_awards()

    # STEP 11: Report pipeline completion.
    print("\n" + "=" * 50)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 50)

    print(f"Records fetched: {len(records)}")
    print(f"Records transformed: {len(df)}")
    print(f"Records validated: {len(df)}")
    print(f"Duplicate rows detected: {duplicate_count}")

    print(f"\nRaw data: {raw_file}")
    print(f"Processed data: {processed_file}")

    print("\nDatabase: federal_spending")
    print("Table: awards")


if __name__ == "__main__":
    run_pipeline()
