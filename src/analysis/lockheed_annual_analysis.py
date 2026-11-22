import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. FILE PATHS AND SETTINGS
# --------------------------------------------------

INPUT_FILE = Path(
    "data/raw/lockheed_award_transactions.json"
)

OUTPUT_FILE = Path(
    "reports/lockheed_annual_obligation_analysis.csv"
)

TARGET_AWARD_ID = "DEAC0494AL85000"


# --------------------------------------------------
# 2. FINANCIAL PRECISION HELPERS
# --------------------------------------------------

def to_cents(value):
    """
    Convert a financial amount into integer cents.

    Reject missing, non-finite, and amounts with
    more than two decimal places.
    """

    if value is None:
        raise ValueError("Missing financial amount found.")

    try:
        amount = Decimal(str(value))

    except (InvalidOperation, ValueError):
        raise ValueError(
            f"Invalid financial amount: {value}"
        )

    if not amount.is_finite():
        raise ValueError(
            f"Non-finite financial amount: {value}"
        )

    if amount != amount.quantize(Decimal("0.01")):
        raise ValueError(
            f"Amount has more than two decimal places: {value}"
        )

    return int(amount * 100)


def format_cents(cents):
    """Convert integer cents into a two-decimal dollar string."""

    return f"{Decimal(int(cents)) / Decimal(100):.2f}"


# --------------------------------------------------
# 3. LOAD RAW TRANSACTION DATA
# --------------------------------------------------

with INPUT_FILE.open() as file:

    data = json.load(
        file,
        parse_float=Decimal
    )


if "results" not in data:
    raise ValueError(
        "JSON file is missing the results field."
    )


df = pd.DataFrame(data["results"])


if df.empty:
    raise ValueError(
        "No transaction records found."
    )


print("\nTRANSACTIONS LOADED:", len(df))


# --------------------------------------------------
# 4. VALIDATE REQUIRED DATA
# --------------------------------------------------

required_columns = [
    "id",
    "action_date",
    "federal_action_obligation"
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


# --------------------------------------------------
# 5. VALIDATE TRANSACTION IDENTIFIERS
# --------------------------------------------------

if df["id"].isna().any():

    raise ValueError(
        "Missing transaction IDs found."
    )


if df["id"].duplicated().any():

    raise ValueError(
        "Duplicate transaction IDs found."
    )


# Validate that every transaction belongs
# to the target award.

if not df["id"].astype(str).str.contains(
    TARGET_AWARD_ID,
    regex=False
).all():

    raise ValueError(
        "Unexpected award ID found in transaction IDs."
    )


# --------------------------------------------------
# 6. VALIDATE TRANSACTION DATES
# --------------------------------------------------

df["action_date"] = pd.to_datetime(
    df["action_date"],
    errors="coerce"
)


if df["action_date"].isna().any():

    raise ValueError(
        "Invalid transaction dates found."
    )


# --------------------------------------------------
# 7. CONVERT FINANCIAL AMOUNTS TO INTEGER CENTS
# --------------------------------------------------

df["obligation_cents"] = df[
    "federal_action_obligation"
].apply(to_cents)


# Separate positive and negative obligations.

df["positive_obligation_cents"] = (
    df["obligation_cents"].clip(lower=0)
)


df["negative_obligation_cents"] = (
    df["obligation_cents"].clip(upper=0)
)


# --------------------------------------------------
# 8. CREATE ANNUAL FINANCIAL ANALYSIS
# --------------------------------------------------

df["year"] = df["action_date"].dt.year


annual = df.groupby("year").agg(

    transaction_count=("id", "count"),

    gross_positive_cents=(
        "positive_obligation_cents",
        "sum"
    ),

    gross_negative_cents=(
        "negative_obligation_cents",
        "sum"
    ),

    net_obligation_change_cents=(
        "obligation_cents",
        "sum"
    )
)


# Include calendar years with zero transactions.

all_years = range(
    df["year"].min(),
    df["year"].max() + 1
)


annual = annual.reindex(
    all_years,
    fill_value=0
)


annual.index.name = "year"


# --------------------------------------------------
# 9. FINANCIAL RECONCILIATION
# --------------------------------------------------

annual["reconciliation_cents"] = (
    annual["gross_positive_cents"]
    + annual["gross_negative_cents"]
)


if not annual["reconciliation_cents"].equals(
    annual["net_obligation_change_cents"]
):

    raise ValueError(
        "Annual gross obligations do not reconcile with net obligations."
    )


# --------------------------------------------------
# 10. COMPARE ANNUAL TOTALS WITH RAW TRANSACTIONS
# --------------------------------------------------

total_transactions = len(df)


total_positive_cents = int(
    df["positive_obligation_cents"].sum()
)


total_negative_cents = int(
    df["negative_obligation_cents"].sum()
)


total_net_cents = int(
    df["obligation_cents"].sum()
)


if int(annual["transaction_count"].sum()) != total_transactions:

    raise ValueError(
        "Annual transaction counts do not match raw transaction count."
    )


if int(annual["gross_positive_cents"].sum()) != total_positive_cents:

    raise ValueError(
        "Annual positive obligations do not reconcile."
    )


if int(annual["gross_negative_cents"].sum()) != total_negative_cents:

    raise ValueError(
        "Annual negative obligations do not reconcile."
    )


if int(annual["net_obligation_change_cents"].sum()) != total_net_cents:

    raise ValueError(
        "Annual net obligations do not reconcile."
    )


# --------------------------------------------------
# 11. PREPARE FINANCIAL REPORT
# --------------------------------------------------

report = annual.drop(
    columns=["reconciliation_cents"]
).copy()


financial_columns = [
    "gross_positive_cents",
    "gross_negative_cents",
    "net_obligation_change_cents"
]


for column in financial_columns:

    report[column.replace("_cents", "")] = (
        report[column].apply(format_cents)
    )


report = report.drop(
    columns=financial_columns
)


report = report[
    [
        "transaction_count",
        "gross_positive",
        "gross_negative",
        "net_obligation_change"
    ]
]


# --------------------------------------------------
# 12. EXPORT ANNUAL REPORT
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


report.to_csv(OUTPUT_FILE)


# --------------------------------------------------
# 13. DISPLAY RESULTS
# --------------------------------------------------

print("\n" + "=" * 90)

print(
    "LOCKHEED MARTIN - ANNUAL OBLIGATION ANALYSIS"
)

print("=" * 90)


print("\nANNUAL RESULTS")

print(report.to_string())


print("\n" + "-" * 90)

print("FINANCIAL RECONCILIATION")


print(
    "Total transactions:",
    total_transactions
)


print(
    "Gross positive obligations: $",
    format_cents(total_positive_cents),
    sep=""
)


print(
    "Gross negative obligations: $",
    format_cents(total_negative_cents),
    sep=""
)


print(
    "Net obligation change: $",
    format_cents(total_net_cents),
    sep=""
)


print(
    "\nReconciliation:",
    "PASSED"
)


print(
    "\nCSV exported to:",
    OUTPUT_FILE
)


print("\n" + "=" * 90)
