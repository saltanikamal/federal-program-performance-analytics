import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load database settings from the project's .env file.
load_dotenv(PROJECT_ROOT / ".env")

# Read database configuration.
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Validate database configuration.
if not all([DB_NAME, DB_USER, DB_HOST, DB_PORT]):
    raise ValueError(
        "Missing database settings in the .env file."
    )

# Build PostgreSQL connection URL.
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}@/{DB_NAME}"
    f"?host={DB_HOST}&port={DB_PORT}"
)


# --------------------------------------------------
# 2. DATABASE CONNECTION TEST
# --------------------------------------------------

def test_connection():
    """Test the PostgreSQL database connection."""

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT current_database(), current_user")
            )

            database, user = result.fetchone()

            print("Database connection successful!")
            print(f"Database: {database}")
            print(f"User: {user}")

    finally:
        engine.dispose()


# --------------------------------------------------
# 3. EXECUTION
# --------------------------------------------------

if __name__ == "__main__":
    test_connection()
