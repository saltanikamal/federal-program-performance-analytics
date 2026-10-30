from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# 1. Locate the project directory.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 2. Locate the agency summary CSV file.
INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "agency_spending_summary.csv"
)

# 3. Define where the charts will be saved.
OUTPUT_DIR = PROJECT_ROOT / "reports"


def create_spending_charts():
    """Create charts from the agency spending summary."""

    # Create the output directory if necessary.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Read the CSV report into a Pandas DataFrame.
    df = pd.read_csv(INPUT_FILE)

    # Check that the expected columns exist.
    required_columns = [
        "awarding_agency",
        "number_of_awards",
        "total_award_value",
        "average_award_value",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("The agency summary CSV is empty.")

    # Sort agencies from highest to lowest total award value.
    df = df.sort_values(
        "total_award_value",
        ascending=False,
    )

    # ------------------------------------------
    # Chart 1: Total award value by agency
    # ------------------------------------------
    plt.figure(figsize=(10, 6))

    plt.bar(
        df["awarding_agency"],
        df["total_award_value"] / 1_000_000_000,
    )

    plt.title("Total Award Value by Federal Agency")
    plt.xlabel("Federal Agency")
    plt.ylabel("Total Award Value ($ billions)")
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()

    chart_1_path = OUTPUT_DIR / "total_award_value_by_agency.png"

    plt.savefig(chart_1_path, dpi=150)
    plt.close()

    # ------------------------------------------
    # Chart 2: Number of awards by agency
    # ------------------------------------------
    plt.figure(figsize=(10, 6))

    plt.bar(
        df["awarding_agency"],
        df["number_of_awards"],
    )

    plt.title("Number of Awards by Federal Agency")
    plt.xlabel("Federal Agency")
    plt.ylabel("Number of Awards")
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()

    chart_2_path = OUTPUT_DIR / "number_of_awards_by_agency.png"

    plt.savefig(chart_2_path, dpi=150)
    plt.close()

    # Display a summary.
    print("Spending charts created successfully.")
    print(f"Agencies analyzed: {len(df)}")
    print(f"Chart 1: {chart_1_path}")
    print(f"Chart 2: {chart_2_path}")


if __name__ == "__main__":
    create_spending_charts()
