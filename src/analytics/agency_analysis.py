import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# 1. Locate the project directory.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 2. Load database configuration.
load_dotenv(PROJECT_ROOT / ".env")

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

if not all([DB_NAME, DB_USER, DB_HOST, DB_PORT]):
    raise ValueError(
        "Missing database settings in the .env file."
    )

# 3. Build the PostgreSQL connection URL.
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}@/{DB_NAME}"
    f"?host={DB_HOST}&port={DB_PORT}"
)

# 4. Define the output directory.
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"


def export_spending_reports():
    """Export agency and recipient summaries to CSV files."""

    # Create the output directory if necessary.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Connect to PostgreSQL.
    engine = create_engine(DATABASE_URL)

    try:
        # 5. Retrieve agency spending results.
        agency_query = text("""
            SELECT *
            FROM agency_spending_summary
            ORDER BY total_award_value DESC
        """)

        with engine.connect() as connection:
            agency_df = pd.read_sql_query(
                agency_query,
                connection,
            )

            # 6. Retrieve recipient spending results.
            recipient_query = text("""
                SELECT *
                FROM recipient_spending_summary
                ORDER BY total_award_value DESC
            """)

            recipient_df = pd.read_sql_query(
                recipient_query,
                connection,
            )

        # 7. Export both reports.
        agency_path = (
            OUTPUT_DIR / "agency_spending_summary.csv"
        )

        recipient_path = (
            OUTPUT_DIR / "recipient_spending_summary.csv"
        )

        agency_df.to_csv(agency_path, index=False)
        recipient_df.to_csv(recipient_path, index=False)

        # 8. Display results.
        print("Spending reports exported successfully.")
        print(f"Agency records exported: {len(agency_df)}")
        print(f"Recipient records exported: {len(recipient_df)}")
        print(f"Agency report: {agency_path}")
        print(f"Recipient report: {recipient_path}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    export_spending_reports()
