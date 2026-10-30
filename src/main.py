import json
from pathlib import Path

from src.ingestion.usa_spending_api import fetch_awards
from src.transformation.clean_awards import awards_to_dataframe


def main():
    # Find the project folder from this file's location.
    project_root = Path(__file__).resolve().parent.parent

    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    print("Starting ingestion...")
    records = fetch_awards()

    # Save the original award records before cleaning.
    raw_path = raw_dir / "awards_sample.json"
    with raw_path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, ensure_ascii=False)

    df = awards_to_dataframe(records)

    # Save the prepared data.
    processed_path = processed_dir / "awards_sample.csv"
    df.to_csv(processed_path, index=False)

    print("\nPrepared data:")
    print(df.head())

    print("\nRows and columns:")
    print(df.shape)

    print("\nColumn data types:")
    print(df.dtypes)

    print("\nMissing values:")
    print(df.isna().sum())

    print("\nDuplicate rows:")
    print(df.duplicated().sum())

    print(f"\nRaw records saved to: {raw_path}")
    print(f"Prepared data saved to: {processed_path}")


if __name__ == "__main__":
    main()
