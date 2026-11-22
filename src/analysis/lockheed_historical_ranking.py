import pandas as pd
from pathlib import Path


# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

INPUT_FILE = Path(
    "reports/lockheed_annual_obligation_analysis.csv"
)

OUTPUT_FILE = Path(
    "reports/lockheed_historical_rankings.csv"
)


# --------------------------------------------------
# 2. LOAD ANNUAL ANALYSIS
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

df = df.set_index("year")

df = df.sort_index()


# --------------------------------------------------
# 3. REMOVE YEARS WITHOUT TRANSACTIONS
# --------------------------------------------------

active_years = df[
    df["transaction_count"] > 0
].copy()


# --------------------------------------------------
# 4. HISTORICAL RANKINGS
# --------------------------------------------------

# TOP 5 GROSS POSITIVE OBLIGATION YEARS

top_positive = active_years[
    active_years["gross_positive"] > 0
].sort_values(
    "gross_positive",
    ascending=False
).head(5)


# TOP 5 GROSS NEGATIVE OBLIGATION YEARS

top_negative = active_years[
    active_years["gross_negative"] < 0
].sort_values(
    "gross_negative",
    ascending=True
).head(5)


# TOP 5 NET OBLIGATION INCREASE YEARS

top_increases = active_years[
    active_years["net_obligation_change"] > 0
].sort_values(
    "net_obligation_change",
    ascending=False
).head(5)


# TOP 5 NET OBLIGATION REDUCTION YEARS

top_reductions = active_years[
    active_years["net_obligation_change"] < 0
].sort_values(
    "net_obligation_change",
    ascending=True
).head(5)


# --------------------------------------------------
# 5. 2017 HISTORICAL DEOBLIGATION ANALYSIS
# --------------------------------------------------

total_negative = active_years[
    "gross_negative"
].sum()

negative_2017 = df.loc[
    2017,
    "gross_negative"
]

share_2017 = (
    abs(negative_2017) /
    abs(total_negative)
) * 100


# --------------------------------------------------
# 6. PREPARE RANKING DATA FOR EXPORT
# --------------------------------------------------

ranking_results = []

ranking_groups = {

    "Gross Positive Obligations": top_positive,

    "Gross Negative Obligations": top_negative,

    "Net Obligation Increases": top_increases,

    "Net Obligation Reductions": top_reductions

}


for ranking_name, ranking_df in ranking_groups.items():

    for rank, (year, row) in enumerate(
        ranking_df.iterrows(),
        start=1
    ):

        ranking_results.append({

            "ranking_category": ranking_name,

            "rank": rank,

            "year": year,

            "gross_positive": row["gross_positive"],

            "gross_negative": row["gross_negative"],

            "net_obligation_change": row["net_obligation_change"],

            "transaction_count": row["transaction_count"]

        })


# --------------------------------------------------
# 7. CREATE RANKING DATAFRAME
# --------------------------------------------------

rankings_df = pd.DataFrame(
    ranking_results
)


# --------------------------------------------------
# 8. CLEAN DATA TYPES AND PRECISION
# --------------------------------------------------

rankings_df["transaction_count"] = (
    rankings_df["transaction_count"].astype(int)
)


# --------------------------------------------------
# 9. EXPORT HISTORICAL RANKINGS
# --------------------------------------------------

rankings_df.to_csv(
    OUTPUT_FILE,
    index=False,
    float_format="%.2f"
)


# --------------------------------------------------
# 10. DISPLAY FORMATTED RESULTS
# --------------------------------------------------

print("\n" + "=" * 85)

print("LOCKHEED MARTIN HISTORICAL FINANCIAL RANKINGS")

print("=" * 85)


def display_ranking(title, ranking_df, column):

    print(f"\n{title}")

    print("-" * 85)

    for year, row in ranking_df.iterrows():

        amount = row[column]

        transactions = int(
            row["transaction_count"]
        )

        print(
            f"{year}: ${amount:,.2f} | "
            f"Transactions: {transactions}"
        )


# DISPLAY FOUR HISTORICAL RANKINGS

display_ranking(
    "TOP 5 YEARS: GROSS POSITIVE OBLIGATIONS",
    top_positive,
    "gross_positive"
)


display_ranking(
    "TOP 5 YEARS: GROSS NEGATIVE OBLIGATIONS",
    top_negative,
    "gross_negative"
)


display_ranking(
    "TOP 5 YEARS: NET OBLIGATION INCREASES",
    top_increases,
    "net_obligation_change"
)


display_ranking(
    "TOP 5 YEARS: NET OBLIGATION REDUCTIONS",
    top_reductions,
    "net_obligation_change"
)


# --------------------------------------------------
# 11. DISPLAY 2017 HISTORICAL FINDING
# --------------------------------------------------

print("\n2017 HISTORICAL DEOBLIGATION ANALYSIS")

print("-" * 85)

print(
    f"Total historical negative obligations: "
    f"${total_negative:,.2f}"
)

print(
    f"2017 negative obligations: "
    f"${negative_2017:,.2f}"
)

print(
    f"2017 share of historical reductions: "
    f"{share_2017:.2f}%"
)


# --------------------------------------------------
# 12. CONFIRM EXPORT
# --------------------------------------------------

print("\n" + "=" * 85)

print("HISTORICAL RANKINGS EXPORT COMPLETED")

print("=" * 85)

print(
    f"\nCSV report saved to: {OUTPUT_FILE}"
)

print(
    f"Total ranking records exported: {len(rankings_df)}"
)

print("\n" + "=" * 85)
