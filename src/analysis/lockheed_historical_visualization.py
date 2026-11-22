import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

INPUT_FILE = Path(
    "reports/lockheed_annual_obligation_analysis.csv"
)

OUTPUT_DIR = Path("reports")

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# --------------------------------------------------
# 2. LOAD ANNUAL ANALYSIS DATA
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

df = df.set_index("year")

# Ensure chronological order
df = df.sort_index()

# Convert dollars to billions
df["gross_positive"] /= 1_000_000_000

df["gross_negative"] /= 1_000_000_000

df["net_obligation_change"] /= 1_000_000_000


# --------------------------------------------------
# 3. PREPARE HISTORICAL COLORS
# --------------------------------------------------

# Highlight 2017 to emphasize the unusual
# historical deobligation activity.

colors = [
    "red" if year == 2017 else "steelblue"
    for year in df.index
]


# --------------------------------------------------
# 4. CHART: GROSS POSITIVE OBLIGATIONS
# --------------------------------------------------

plt.figure(figsize=(14, 6))

plt.bar(
    df.index,
    df["gross_positive"]
)

plt.title(
    "Lockheed Martin Annual Gross Positive Obligations"
)

plt.xlabel("Year")

plt.ylabel("Obligations ($ Billions)")

plt.xticks(
    df.index,
    rotation=45
)

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "lockheed_gross_positive_obligations.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# --------------------------------------------------
# 5. CHART: GROSS NEGATIVE OBLIGATIONS
# --------------------------------------------------

plt.figure(figsize=(14, 6))

plt.bar(
    df.index,
    df["gross_negative"]
)

plt.axhline(
    0,
    linewidth=0.8
)

plt.title(
    "Lockheed Martin Annual Gross Deobligations"
)

plt.xlabel("Year")

plt.ylabel("Deobligations ($ Billions)")

plt.xticks(
    df.index,
    rotation=45
)

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "lockheed_gross_negative_obligations.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# --------------------------------------------------
# 6. CHART: NET OBLIGATION CHANGES
# --------------------------------------------------

plt.figure(figsize=(14, 6))

plt.bar(
    df.index,
    df["net_obligation_change"]
)

plt.axhline(
    0,
    linewidth=0.8
)

plt.title(
    "Lockheed Martin Annual Net Obligation Changes"
)

plt.xlabel("Year")

plt.ylabel("Net Change ($ Billions)")

plt.xticks(
    df.index,
    rotation=45
)

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "lockheed_net_obligation_changes.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# --------------------------------------------------
# 7. CONSOLIDATED HISTORICAL FINANCIAL OVERVIEW
# --------------------------------------------------

fig, axes = plt.subplots(
    3,
    1,
    figsize=(16, 13),
    sharex=True
)


# CHART 1: GROSS POSITIVE OBLIGATIONS

axes[0].bar(
    df.index,
    df["gross_positive"],
    color=colors
)

axes[0].set_title(
    "Annual Gross Positive Obligations"
)

axes[0].set_ylabel(
    "$ Billions"
)

axes[0].grid(
    axis="y",
    alpha=0.3
)


# CHART 2: GROSS DEOBLIGATIONS

axes[1].bar(
    df.index,
    df["gross_negative"],
    color=colors
)

axes[1].axhline(
    0,
    linewidth=0.8
)

axes[1].set_title(
    "Annual Gross Deobligations"
)

axes[1].set_ylabel(
    "$ Billions"
)

axes[1].grid(
    axis="y",
    alpha=0.3
)


# CHART 3: NET OBLIGATION CHANGES

axes[2].bar(
    df.index,
    df["net_obligation_change"],
    color=colors
)

axes[2].axhline(
    0,
    linewidth=0.8
)

axes[2].set_title(
    "Annual Net Obligation Changes"
)

axes[2].set_ylabel(
    "$ Billions"
)

axes[2].set_xlabel(
    "Year"
)

axes[2].grid(
    axis="y",
    alpha=0.3
)


# FORMAT YEAR AXIS

axes[2].set_xticks(
    df.index
)

axes[2].tick_params(
    axis="x",
    rotation=45
)


# OVERALL TITLE

fig.suptitle(
    "Lockheed Martin Historical Financial Analysis",
    fontsize=17,
    fontweight="bold"
)

plt.tight_layout(
    rect=[0, 0, 1, 0.97]
)


# SAVE CONSOLIDATED CHART

plt.savefig(
    OUTPUT_DIR / "lockheed_historical_financial_overview.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# --------------------------------------------------
# 8. DETAILED FINANCIAL OVERVIEW: 2018-2026
# --------------------------------------------------

# Examine the years following the major 2017
# deobligation activity separately.
#
# This provides a more readable scale for the
# relatively small financial adjustments.
#
# Original historical data remain unchanged.


recent_df = df.loc[2018:2026].copy()


# Convert billions to millions

recent_df["gross_positive"] *= 1000

recent_df["gross_negative"] *= 1000

recent_df["net_obligation_change"] *= 1000


# CREATE THREE-PANEL FIGURE

fig, axes = plt.subplots(
    3,
    1,
    figsize=(15, 12),
    sharex=True
)


# CHART 1: GROSS POSITIVE OBLIGATIONS

axes[0].bar(
    recent_df.index,
    recent_df["gross_positive"],
    color="steelblue"
)

axes[0].set_title(
    "Annual Gross Positive Obligations"
)

axes[0].set_ylabel(
    "$ Millions"
)

axes[0].grid(
    axis="y",
    alpha=0.3
)


# CHART 2: GROSS DEOBLIGATIONS

axes[1].bar(
    recent_df.index,
    recent_df["gross_negative"],
    color="indianred"
)

axes[1].axhline(
    0,
    linewidth=0.8
)

axes[1].set_title(
    "Annual Gross Deobligations"
)

axes[1].set_ylabel(
    "$ Millions"
)

axes[1].grid(
    axis="y",
    alpha=0.3
)


# CHART 3: NET OBLIGATION CHANGES

axes[2].bar(
    recent_df.index,
    recent_df["net_obligation_change"],
    color="steelblue"
)

axes[2].axhline(
    0,
    linewidth=0.8
)

axes[2].set_title(
    "Annual Net Obligation Changes"
)

axes[2].set_ylabel(
    "$ Millions"
)

axes[2].set_xlabel(
    "Year"
)

axes[2].grid(
    axis="y",
    alpha=0.3
)


# FORMAT YEAR AXIS

axes[2].set_xticks(
    recent_df.index
)

axes[2].tick_params(
    axis="x",
    rotation=45
)


# OVERALL TITLE

fig.suptitle(
    "Lockheed Martin Financial Activity: 2018-2026",
    fontsize=17,
    fontweight="bold"
)

plt.tight_layout(
    rect=[0, 0, 1, 0.97]
)


# SAVE DETAILED CHART

plt.savefig(
    OUTPUT_DIR / "lockheed_recent_financial_overview.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# --------------------------------------------------
# 9. CONFIRM CHART GENERATION
# --------------------------------------------------

print("\n" + "=" * 70)

print("LOCKHEED MARTIN HISTORICAL VISUALIZATION COMPLETE")

print("=" * 70)

print("\nGENERATED CHARTS:")


print("\n1. Gross positive obligations")

print(
    "   reports/lockheed_gross_positive_obligations.png"
)


print("\n2. Gross deobligations")

print(
    "   reports/lockheed_gross_negative_obligations.png"
)


print("\n3. Net obligation changes")

print(
    "   reports/lockheed_net_obligation_changes.png"
)


print("\n4. Consolidated historical financial overview")

print(
    "   reports/lockheed_historical_financial_overview.png"
)


print("\n5. Detailed financial overview (2018-2026)")

print(
    "   reports/lockheed_recent_financial_overview.png"
)


print("\nIMPORTANT DATA NOTE:")

print(
    "2026 data are partial and extend through July 7, 2026."
)


print("\n2017 is highlighted in red in the consolidated overview.")

print("\n" + "=" * 70)
