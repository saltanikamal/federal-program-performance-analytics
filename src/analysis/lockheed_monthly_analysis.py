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
    "reports/lockheed_monthly_obligation_analysis.csv"
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
        raise ValueError(f"Invalid financial amount: {value}")

    if not amount.is_finite():
        raise ValueError(f"Non-finite financial amount: {value}")

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
    data = json.load(file, parse_float=Decimal)


if "results" not in data:
    raise ValueError("JSON file is missing the results field.")


df = pd.DataFrame(data["results"])


if df.empty:
    raise ValueError("No transaction records found.")


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
    raise ValueError("Missing transaction IDs found.")


if df["id"].duplicated().any():
    raise ValueError("Duplicate transaction IDs found.")


# Validate award identifier using transaction IDs.

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
    raise ValueError("Invalid transaction dates found.")


# --------------------------------------------------
# 7. CONVERT FINANCIAL AMOUNTS TO INTEGER CENTS
# --------------------------------------------------

df["obligation_cents"] = df[
    "federal_action_obligation"
].apply(to_cents)


df["positive_obligation_cents"] = (
    df["obligation_cents"].clip(lower=0)
)


df["negative_obligation_cents"] = (
    df["obligation_cents"].clip(upper=0)
)


# Count transaction types.

df["positive_transaction"] = (
    df["obligation_cents"] > 0
)

df["negative_transaction"] = (
    df["obligation_cents"] < 0
)

df["zero_transaction"] = (
    df["obligation_cents"] == 0
)


# Convert dates into monthly periods.

df["month"] = df["action_date"].dt.to_period("M")


# --------------------------------------------------
# 8. MONTHLY FINANCIAL ANALYSIS
# --------------------------------------------------

monthly = df.groupby("month").agg(

    transaction_count=("id", "count"),

    positive_transaction_count=(
        "positive_transaction",
        "sum"
    ),

    negative_transaction_count=(
        "negative_transaction",
        "sum"
    ),

    zero_transaction_count=(
        "zero_transaction",
        "sum"
    ),

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


# Include months with zero recorded transactions.

all_months = pd.period_range(
    start=df["month"].min(),
    end=df["month"].max(),
    freq="M"
)


monthly = monthly.reindex(
    all_months,
    fill_value=0
)


monthly.index.name = "month"


# --------------------------------------------------
# 9. FINANCIAL RECONCILIATION
# --------------------------------------------------

monthly["reconciliation_cents"] = (
    monthly["gross_positive_cents"]
    + monthly["gross_negative_cents"]
)


if not monthly["reconciliation_cents"].equals(
    monthly["net_obligation_change_cents"]
):
    raise ValueError(
        "Monthly gross obligations do not reconcile with net obligations."
    )


# Compare monthly totals against raw transactions.

raw_total_cents = int(df["obligation_cents"].sum())


monthly_total_cents = int(
    monthly["net_obligation_change_cents"].sum()
)


if monthly_total_cents != raw_total_cents:
    raise ValueError(
        "Monthly net obligations do not match raw transaction total."
    )


if int(monthly["transaction_count"].sum()) != len(df):
    raise ValueError(
        "Monthly transaction counts do not match raw transaction count."
    )


# Verify positive, negative, and zero transaction counts.

if int(monthly["positive_transaction_count"].sum()) != int(
    df["positive_transaction"].sum()
):
    raise ValueError("Positive transaction counts do not reconcile.")


if int(monthly["negative_transaction_count"].sum()) != int(
    df["negative_transaction"].sum()
):
    raise ValueError("Negative transaction counts do not reconcile.")


if int(monthly["zero_transaction_count"].sum()) != int(
    df["zero_transaction"].sum()
):
    raise ValueError("Zero transaction counts do not reconcile.")


# --------------------------------------------------
# 10. CALCULATE CUMULATIVE NET OBLIGATIONS
# --------------------------------------------------

monthly["cumulative_net_obligation_cents"] = (
    monthly["net_obligation_change_cents"].cumsum()
)


# --------------------------------------------------
# 11. IDENTIFY MONTHS WITHOUT TRANSACTIONS
# --------------------------------------------------

missing_months = monthly[
    monthly["transaction_count"] == 0
].index.astype(str).tolist()


# --------------------------------------------------
# 12. IDENTIFY LARGEST MONTHLY CHANGES
# --------------------------------------------------

largest_positive_month = (
    monthly["net_obligation_change_cents"].idxmax()
)


largest_negative_month = (
    monthly["net_obligation_change_cents"].idxmin()
)


# --------------------------------------------------
# 13. PREPARE MONTHLY REPORT
# --------------------------------------------------

report = monthly.copy()


financial_columns = [
    "gross_positive_cents",
    "gross_negative_cents",
    "net_obligation_change_cents",
    "cumulative_net_obligation_cents"
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
        "positive_transaction_count",
        "negative_transaction_count",
        "zero_transaction_count",
        "gross_positive",
        "gross_negative",
        "net_obligation_change",
        "cumulative_net_obligation"
    ]
]


# --------------------------------------------------
# 14. EXPORT MONTHLY REPORT
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


report.to_csv(OUTPUT_FILE)


# --------------------------------------------------
# 15. DISPLAY RESULTS
# --------------------------------------------------

print("\n" + "=" * 90)

print("LOCKHEED MARTIN - MONTHLY OBLIGATION ANALYSIS")

print("=" * 90)


print("\nMONTHLY RESULTS")

print(report.to_string())


print("\n" + "-" * 90)

print("MONTHS WITHOUT RECORDED TRANSACTIONS")

print("Number of months:", len(missing_months))

print("\nFirst 30 missing months:")

print(missing_months[:30])


print("\n" + "-" * 90)

print("LARGEST MONTHLY POSITIVE NET CHANGE")

print("Month:", largest_positive_month)

print(
    "Amount:",
    f"${format_cents(monthly.loc[largest_positive_month, 'net_obligation_change_cents'])}"
)


print("\nLARGEST MONTHLY NEGATIVE NET CHANGE")

print("Month:", largest_negative_month)

print(
    "Amount:",
    f"${format_cents(monthly.loc[largest_negative_month, 'net_obligation_change_cents'])}"
)


print("\n" + "-" * 90)

print("TRANSACTION TYPE COUNTS")

print("Positive transactions:", int(df["positive_transaction"].sum()))

print("Negative transactions:", int(df["negative_transaction"].sum()))

print("Zero-value transactions:", int(df["zero_transaction"].sum()))


print("\n" + "-" * 90)

print("FINANCIAL RECONCILIATION")

print(
    "Total monthly net changes:",
    f"${format_cents(monthly_total_cents)}"
)

print(
    "Total original transaction obligations:",
    f"${format_cents(raw_total_cents)}"
)

print(
    "\nFinal cumulative net obligation change:",
    f"${format_cents(monthly['cumulative_net_obligation_cents'].iloc[-1])}"
)


print("\nDATA QUALITY CHECKS")

print("Transaction IDs unique: PASS")
print("Award identifier validated: PASS")
print("Transaction dates valid: PASS")
print("Financial amounts valid: PASS")
print("Maximum financial precision: 2 decimal places")
print("Monthly gross-to-net reconciliation: PASS")
print("Monthly totals match raw transactions: PASS")
print("Transaction type counts reconcile: PASS")


print("\nREPORT EXPORTED TO:")

print(OUTPUT_FILE)

print("=" * 90)
