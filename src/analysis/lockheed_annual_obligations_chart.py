import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


# --------------------------------------------------
# 1. FILE PATHS
# --------------------------------------------------

INPUT_FILE = Path(
    "reports/lockheed_annual_obligation_analysis.csv"
)

OUTPUT_DIR = Path("reports")


# --------------------------------------------------
# 2. LOAD ANNUAL OBLIGATION DATA
# --------------------------------------------------

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

# Sort by fiscal/calendar year
df = df.sort_values("year").reset_index(drop=True)

print("\nAnnual obligation data loaded successfully.")

print(df.head())


# --------------------------------------------------
# 3. VALIDATE REQUIRED COLUMNS
# --------------------------------------------------

required_columns = [
    "year",
    "gross_positive",
    "gross_negative",
    "net_obligation_change",
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
# 4. PREPARE DATA FOR VISUALIZATION
# --------------------------------------------------

# Convert dollar amounts into billions of dollars.

df["gross_positive_billions"] = (
    df["gross_positive"] / 1_000_000_000
)

df["gross_negative_billions"] = (
    df["gross_negative"] / 1_000_000_000
)

df["net_change_billions"] = (
    df["net_obligation_change"] / 1_000_000_000
)


# --------------------------------------------------
# 5. CREATE OUTPUT DIRECTORY
# --------------------------------------------------

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# --------------------------------------------------
# 6. CHART 1: GROSS POSITIVE OBLIGATIONS
# --------------------------------------------------

fig_positive = go.Figure()

fig_positive.add_trace(
    go.Bar(
        x=df["year"],
        y=df["gross_positive_billions"],
        name="Gross Positive Obligations",
        text=df["gross_positive_billions"].round(3),
        texttemplate="$%{text:.3f}B",
        textposition="outside",
        hovertemplate=(
            "Year: %{x}<br>"
            "Gross Positive Obligations: "
            "$%{y:.3f}B"
            "<extra></extra>"
        ),
    )
)

fig_positive.update_layout(
    title="Lockheed Martin: Annual Gross Positive Obligations",
    xaxis_title="Year",
    yaxis_title="Obligations (Billions of Dollars)",
    template="plotly_white",
    showlegend=False,
    height=600,
)

fig_positive.update_xaxes(
    type="category"
)

fig_positive.write_html(
    OUTPUT_DIR / "lockheed_gross_positive_obligations.html"
)


# --------------------------------------------------
# 7. CHART 2: GROSS NEGATIVE OBLIGATIONS
# --------------------------------------------------

fig_negative = go.Figure()

fig_negative.add_trace(
    go.Bar(
        x=df["year"],
        y=df["gross_negative_billions"],
        name="Gross Negative Obligations",
        text=df["gross_negative_billions"].round(3),
        texttemplate="$%{text:.3f}B",
        textposition="outside",
        hovertemplate=(
            "Year: %{x}<br>"
            "Gross Negative Obligations: "
            "$%{y:.3f}B"
            "<extra></extra>"
        ),
    )
)

fig_negative.update_layout(
    title="Lockheed Martin: Annual Gross Negative Obligations",
    xaxis_title="Year",
    yaxis_title="Deobligations (Billions of Dollars)",
    template="plotly_white",
    showlegend=False,
    height=600,
)

fig_negative.update_xaxes(
    type="category"
)

fig_negative.write_html(
    OUTPUT_DIR / "lockheed_gross_negative_obligations.html"
)


# --------------------------------------------------
# 8. CHART 3: NET ANNUAL OBLIGATION CHANGES
# --------------------------------------------------

fig_net = go.Figure()

fig_net.add_trace(
    go.Bar(
        x=df["year"],
        y=df["net_change_billions"],
        name="Net Obligation Change",
        text=df["net_change_billions"].round(3),
        texttemplate="$%{text:.3f}B",
        textposition="outside",
        hovertemplate=(
            "Year: %{x}<br>"
            "Net Obligation Change: "
            "$%{y:.3f}B"
            "<extra></extra>"
        ),
    )
)

# Add a zero reference line.
# Positive values indicate net increases.
# Negative values indicate net reductions.

fig_net.add_hline(
    y=0,
    line_dash="dash",
    line_width=2,
    annotation_text="Zero Net Change",
    annotation_position="top left",
)

fig_net.update_layout(
    title="Lockheed Martin: Annual Net Obligation Changes",
    xaxis_title="Year",
    yaxis_title="Net Change (Billions of Dollars)",
    template="plotly_white",
    showlegend=False,
    height=600,
)

fig_net.update_xaxes(
    type="category"
)

fig_net.write_html(
    OUTPUT_DIR / "lockheed_net_obligation_changes.html"
)


# --------------------------------------------------
# 9. DISPLAY RESULTS
# --------------------------------------------------

print("\nAnnual obligation charts generated successfully.")

print("\nGenerated files:")

print(
    OUTPUT_DIR / "lockheed_gross_positive_obligations.html"
)

print(
    OUTPUT_DIR / "lockheed_gross_negative_obligations.html"
)

print(
    OUTPUT_DIR / "lockheed_net_obligation_changes.html"
)

print("\nAll charts are saved in the reports directory.")
