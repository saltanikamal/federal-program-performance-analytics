"""
Federal Program Performance & Spending Analytics Platform

Features:
- PostgreSQL data connection
- Agency and recipient filters
- Spending summary metrics
- Agency award-value visualization
- Award records table and CSV export
- Nine data quality checks
- Lockheed Martin transaction analysis
- Annual positive and negative obligations
- Annual net and cumulative obligation trends

Important:
This dashboard displays the records currently loaded into the project
database. It does not represent all federal spending nationwide.
Award values are not necessarily amounts actually paid.

The Lockheed Martin transaction analysis uses a separate JSON transaction
history file and is not affected by the agency or recipient filters.
"""

import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


# ==================================================
# 1. CONFIGURATION
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")

TRANSACTION_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lockheed_award_transactions.json"
)

st.set_page_config(
    page_title="Federal Spending Analytics",
    page_icon="📊",
    layout="wide",
)


# ==================================================
# 2. PAGE HEADER
# ==================================================

st.title("Federal Program Performance & Spending Analytics")

st.markdown(
    """
    This dashboard analyzes federal award records stored in PostgreSQL.
    Use the filters to explore records by awarding agency and recipient.
    """
)

st.warning(
    """
    **Data limitation:** This project uses a sample of federal award
    records and does not represent all federal spending nationwide.
    Award values are not necessarily amounts actually paid.
    """
)


# ==================================================
# 3. DATABASE CONNECTION
# ==================================================

@st.cache_resource
def get_engine():
    """Create and cache the SQLAlchemy database engine."""

    required_settings = {
        "DB_NAME": DB_NAME,
        "DB_USER": DB_USER,
        "DB_HOST": DB_HOST,
        "DB_PORT": DB_PORT,
    }

    missing_settings = [
        name
        for name, value in required_settings.items()
        if not value
    ]

    if missing_settings:
        raise ValueError(
            "Missing database settings in .env: "
            + ", ".join(missing_settings)
        )

    database_url = (
        f"postgresql+psycopg2://{DB_USER}@/{DB_NAME}"
        f"?host={DB_HOST}&port={DB_PORT}"
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


# ==================================================
# 4. LOAD DATA FROM POSTGRESQL
# ==================================================

@st.cache_data(ttl=60)
def load_awards():
    """
    Load award records from PostgreSQL.

    Results are cached for 60 seconds to reduce repeated queries.
    """

    engine = get_engine()

    query = text(
        """
        SELECT
            internal_id,
            award_id,
            recipient_name,
            award_amount,
            generated_internal_id,
            awarding_agency,
            start_date,
            end_date,
            description
        FROM awards
        ORDER BY award_amount DESC NULLS LAST
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(query, connection)

    if "award_amount" in df.columns:
        df["award_amount"] = pd.to_numeric(
            df["award_amount"],
            errors="coerce",
        )

    for column in ["start_date", "end_date"]:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
            )

    return df


try:
    awards_df = load_awards()

except (SQLAlchemyError, ValueError, OSError) as error:
    st.error(
        "The dashboard could not connect to PostgreSQL or load "
        "the award records."
    )

    st.caption(
        "Check that PostgreSQL is running, the database exists, "
        "and your .env settings are correct."
    )

    with st.expander("Technical details"):
        st.code(str(error))

    st.stop()


if awards_df.empty:
    st.warning(
        "The awards table is empty. Run the data pipeline to load records."
    )
    st.stop()


# ==================================================
# 5. DATA PREPARATION
# ==================================================

filtered_df = awards_df.copy()

agency_values = (
    awards_df["awarding_agency"]
    .dropna()
    .astype(str)
    .str.strip()
)

agency_options = sorted(
    value
    for value in agency_values.unique()
    if value
)


# ==================================================
# 6. SIDEBAR FILTERS
# ==================================================

st.sidebar.header("Dashboard Filters")

selected_agencies = st.sidebar.multiselect(
    "Select awarding agencies",
    options=agency_options,
    default=agency_options,
)

recipient_search = st.sidebar.text_input(
    "Search recipient name",
    placeholder="Enter recipient name...",
)

if selected_agencies:
    filtered_df = filtered_df[
        filtered_df["awarding_agency"]
        .astype("string")
        .str.strip()
        .isin(selected_agencies)
    ]
else:
    filtered_df = filtered_df.iloc[0:0]

if recipient_search.strip():
    recipient_mask = (
        filtered_df["recipient_name"]
        .astype("string")
        .str.contains(
            recipient_search.strip(),
            case=False,
            regex=False,
            na=False,
        )
    )

    filtered_df = filtered_df[recipient_mask]


# ==================================================
# 7. SUMMARY METRICS
# ==================================================

st.divider()
st.subheader("Spending Summary")

if filtered_df.empty:
    st.info(
        "No records match the selected filters. "
        "Change the agency or recipient filters."
    )

else:
    total_awards = int(filtered_df["award_id"].nunique())

    total_recorded_value = filtered_df["award_amount"].sum(
        min_count=1
    )

    average_award_value = filtered_df["award_amount"].mean()
    largest_award_value = filtered_df["award_amount"].max()

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric("Unique Award IDs", f"{total_awards:,}")

    metric2.metric(
        "Total Recorded Award Value",
        (
            f"${total_recorded_value:,.2f}"
            if pd.notna(total_recorded_value)
            else "N/A"
        ),
    )

    metric3.metric(
        "Average Award Value",
        (
            f"${average_award_value:,.2f}"
            if pd.notna(average_award_value)
            else "N/A"
        ),
    )

    metric4.metric(
        "Largest Award Value",
        (
            f"${largest_award_value:,.2f}"
            if pd.notna(largest_award_value)
            else "N/A"
        ),
    )


# ==================================================
# 8. AGENCY AWARD-VALUE CHART
# ==================================================

st.divider()
st.subheader("Award Values by Agency")

if not filtered_df.empty:

    agency_summary = (
        filtered_df
        .dropna(subset=["awarding_agency"])
        .groupby("awarding_agency", as_index=False)
        .agg(
            total_award_value=(
                "award_amount",
                lambda values: values.sum(min_count=1),
            ),
            number_of_awards=("award_id", "nunique"),
        )
        .sort_values(
            "total_award_value",
            ascending=False,
            na_position="last",
        )
    )

    agency_summary = agency_summary.dropna(
        subset=["total_award_value"]
    )

    if not agency_summary.empty:

        fig = px.bar(
            agency_summary,
            x="awarding_agency",
            y="total_award_value",
            color="awarding_agency",
            hover_data={
                "total_award_value": ":$,.2f",
                "number_of_awards": True,
            },
            labels={
                "awarding_agency": "Awarding Agency",
                "total_award_value": "Recorded Award Value ($)",
                "number_of_awards": "Unique Award IDs",
            },
            title="Award Values in the Selected Records",
        )

        fig.update_layout(
            xaxis_title="Awarding Agency",
            yaxis_title="Recorded Award Value ($)",
            yaxis_tickprefix="$",
            yaxis_tickformat="~s",
            showlegend=False,
        )

        st.plotly_chart(fig, width="stretch")

    else:
        st.info(
            "No valid agency award-value data is available "
            "for this selection."
        )


# ==================================================
# 9. AWARD RECORDS TABLE AND CSV EXPORT
# ==================================================

st.divider()
st.subheader("Award Records")

if not filtered_df.empty:

    display_columns = [
        "award_id",
        "recipient_name",
        "award_amount",
        "awarding_agency",
        "start_date",
        "end_date",
        "description",
    ]

    display_df = (
        filtered_df[display_columns]
        .sort_values(
            "award_amount",
            ascending=False,
            na_position="last",
        )
        .copy()
    )

    display_df = display_df.rename(
        columns={
            "award_id": "Award ID",
            "recipient_name": "Recipient",
            "award_amount": "Recorded Award Value ($)",
            "awarding_agency": "Awarding Agency",
            "start_date": "Start Date",
            "end_date": "End Date",
            "description": "Description",
        }
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Recorded Award Value ($)": st.column_config.NumberColumn(
                "Recorded Award Value ($)",
                format="$%.2f",
            ),
            "Start Date": st.column_config.DateColumn(
                "Start Date",
                format="YYYY-MM-DD",
            ),
            "End Date": st.column_config.DateColumn(
                "End Date",
                format="YYYY-MM-DD",
            ),
        },
    )

    csv_data = display_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download filtered awards as CSV",
        data=csv_data,
        file_name="filtered_federal_awards.csv",
        mime="text/csv",
    )

else:
    st.info(
        "No award records are available for the selected filters."
    )


# ==================================================
# 10. DATA QUALITY REPORT
# ==================================================

st.divider()
st.subheader("Data Quality Report")

st.markdown(
    """
    These checks identify potential data problems in the records
    loaded from PostgreSQL.

    A result of zero means that the specific issue was not detected
    in the current database sample. These checks do not guarantee
    that every record is correct.
    """
)


def missing_or_blank_count(series):
    """Count missing values and strings that contain only whitespace."""

    missing_mask = series.isna()

    blank_mask = (
        series.astype("string")
        .str.strip()
        .eq("")
        .fillna(False)
    )

    return int((missing_mask | blank_mask).sum())


# --------------------------------------------------
# Checks 1-9
# --------------------------------------------------

missing_award_ids = missing_or_blank_count(awards_df["award_id"])

negative_award_amounts = int(
    (awards_df["award_amount"] < 0).fillna(False).sum()
)

invalid_date_mask = (
    awards_df["start_date"].notna()
    & awards_df["end_date"].notna()
    & (awards_df["end_date"] < awards_df["start_date"])
)

duplicate_award_ids = int(
    awards_df["award_id"].duplicated(keep=False).sum()
)

missing_agencies = missing_or_blank_count(
    awards_df["awarding_agency"]
)

missing_recipients = missing_or_blank_count(
    awards_df["recipient_name"]
)

duplicate_internal_ids = int(
    awards_df["internal_id"].duplicated(keep=False).sum()
)

missing_award_amounts = int(
    awards_df["award_amount"].isna().sum()
)

missing_generated_ids = missing_or_blank_count(
    awards_df["generated_internal_id"]
)

quality_checks = [
    ("Missing Award IDs", missing_award_ids),
    ("Negative Award Amounts", negative_award_amounts),
    ("Invalid Date Ranges", int(invalid_date_mask.sum())),
    ("Duplicate Award IDs", duplicate_award_ids),
    ("Missing Awarding Agencies", missing_agencies),
    ("Missing Recipient Names", missing_recipients),
    ("Duplicate Internal IDs", duplicate_internal_ids),
    ("Missing Award Amounts", missing_award_amounts),
    ("Missing Generated IDs", missing_generated_ids),
]

quality_df = pd.DataFrame(
    quality_checks,
    columns=["Data Quality Check", "Issue Count"],
)

st.dataframe(
    quality_df,
    width="stretch",
    hide_index=True,
)

# Missing values by column
with st.expander("View missing values by column"):

    missing_counts = {
        column: int(awards_df[column].isna().sum())
        for column in awards_df.columns
    }

    blank_counts = {
        column: int(
            (
                awards_df[column]
                .astype("string")
                .str.strip()
                .eq("")
                .fillna(False)
            ).sum()
        )
        for column in awards_df.columns
    }

    missing_report = pd.DataFrame(
        {"Column": list(awards_df.columns)}
    )

    missing_report["Missing Values"] = (
        missing_report["Column"]
        .map(missing_counts)
        .fillna(0)
        .astype(int)
    )

    missing_report["Blank Strings"] = (
        missing_report["Column"]
        .map(blank_counts)
        .fillna(0)
        .astype(int)
    )

    st.dataframe(
        missing_report,
        width="stretch",
        hide_index=True,
    )


# Invalid date records
with st.expander("View records with invalid date ranges"):

    invalid_dates_df = awards_df.loc[
        invalid_date_mask,
        [
            "award_id",
            "recipient_name",
            "start_date",
            "end_date",
        ],
    ]

    if invalid_dates_df.empty:
        st.success("No invalid date ranges were detected.")

    else:
        st.dataframe(
            invalid_dates_df,
            width="stretch",
            hide_index=True,
        )


# Data quality summary
total_issue_instances = sum(
    issue_count
    for _, issue_count in quality_checks
)

if total_issue_instances == 0:
    st.success(
        "All nine data quality checks passed for the current sample."
    )
else:
    st.warning(
        f"The nine checks detected {total_issue_instances:,} "
        "potential issue instances. One record may contribute to "
        "more than one check. Review the metrics and expanders above."
    )


# ==================================================
# 11. DASHBOARD FOOTER
# ==================================================

st.divider()

st.caption(
    f"Database: {DB_NAME} | "
    f"Records loaded: {len(awards_df):,} | "
    f"Records displayed: {len(filtered_df):,} | "
    "Data source: project PostgreSQL database"
)


# ==================================================
# 12. LOCKHEED MARTIN TRANSACTION ANALYSIS
# ==================================================

st.divider()

st.header("Contract Transaction Analysis")

st.markdown(
    """
    Annual analysis of positive and negative federal obligations
    associated with the Lockheed Martin award transaction history.

    This transaction dataset is analyzed separately from the award
    records stored in PostgreSQL.
    """
)


@st.cache_data(ttl=300)
def load_lockheed_transactions(file_path, modified_time):
    """
    Load and prepare Lockheed Martin transaction history.

    The modification time is included in the cache key so that
    changes to the source file trigger a reload.
    """

    with open(file_path, encoding="utf-8") as file:
        transaction_data = json.load(file)

    if "results" not in transaction_data:
        raise ValueError(
            "The transaction JSON file does not contain a 'results' field."
        )

    transactions = pd.DataFrame(transaction_data["results"])

    required_columns = [
        "federal_action_obligation",
        "action_date",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in transactions.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required transaction fields: "
            + ", ".join(missing_columns)
        )

    transactions["federal_action_obligation"] = pd.to_numeric(
        transactions["federal_action_obligation"],
        errors="coerce",
    )

    transactions["action_date"] = pd.to_datetime(
        transactions["action_date"],
        errors="coerce",
    )

    transactions = transactions.dropna(
        subset=[
            "federal_action_obligation",
            "action_date",
        ]
    ).copy()

    transactions["year"] = transactions["action_date"].dt.year

    transactions["positive_obligations"] = (
        transactions["federal_action_obligation"].clip(lower=0)
    )

    transactions["negative_obligations"] = (
        transactions["federal_action_obligation"].clip(upper=0)
    )

    return transactions


if TRANSACTION_FILE.exists():

    try:
        transactions_df = load_lockheed_transactions(
            str(TRANSACTION_FILE),
            TRANSACTION_FILE.stat().st_mtime,
        )

    except (OSError, json.JSONDecodeError, ValueError, KeyError) as error:
        st.error(
            "The Lockheed Martin transaction history could not be loaded."
        )

        with st.expander("Transaction data technical details"):
            st.code(str(error))

        transactions_df = pd.DataFrame()

    if not transactions_df.empty:

        # --------------------------------------------------
        # Annual aggregation
        # --------------------------------------------------

        annual_summary = (
            transactions_df
            .groupby("year")
            .agg(
                total_transactions=(
                    "federal_action_obligation",
                    "count",
                ),
                positive_transactions=(
                    "positive_obligations",
                    lambda values: int((values > 0).sum()),
                ),
                negative_transactions=(
                    "negative_obligations",
                    lambda values: int((values < 0).sum()),
                ),
                gross_positive_obligations=(
                    "positive_obligations",
                    "sum",
                ),
                gross_negative_obligations=(
                    "negative_obligations",
                    "sum",
                ),
                net_obligation_change=(
                    "federal_action_obligation",
                    "sum",
                ),
            )
            .reset_index()
            .sort_values("year")
            .reset_index(drop=True)
        )

        # Cumulative sum of annual net changes.
        # This is not an independently verified outstanding award balance.
        annual_summary["cumulative_net_obligations"] = (
            annual_summary["net_obligation_change"].cumsum()
        )

        # --------------------------------------------------
        # Transaction summary metrics
        # --------------------------------------------------

        total_transactions = len(transactions_df)

        total_positive = transactions_df[
            "positive_obligations"
        ].sum()

        total_negative = transactions_df[
            "negative_obligations"
        ].sum()

        total_net = transactions_df[
            "federal_action_obligation"
        ].sum()

        st.subheader("Transaction Summary")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Transactions",
            f"{total_transactions:,}",
        )

        col2.metric(
            "Gross Positive Obligations",
            f"${total_positive / 1e9:,.3f}B",
        )

        col3.metric(
            "Gross Negative Obligations",
            f"-${abs(total_negative) / 1e9:,.3f}B",
        )

        col4.metric(
            "Net Obligation Change",
            f"${total_net / 1e9:,.3f}B",
        )

        # --------------------------------------------------
        # Annual positive and negative obligations
        # --------------------------------------------------

        st.subheader("Annual Positive vs. Negative Obligations")

        fig_obligations = go.Figure()

        fig_obligations.add_trace(
            go.Bar(
                x=annual_summary["year"],
                y=annual_summary["gross_positive_obligations"],
                name="Gross Positive Obligations",
            )
        )

        fig_obligations.add_trace(
            go.Bar(
                x=annual_summary["year"],
                y=annual_summary["gross_negative_obligations"],
                name="Gross Negative Obligations",
            )
        )

        fig_obligations.update_layout(
            title="Annual Obligation Increases and Reductions",
            xaxis_title="Transaction Year",
            yaxis_title="Obligation Amount ($)",
            yaxis_tickprefix="$",
            yaxis_tickformat="~s",
            barmode="relative",
            hovermode="x unified",
            legend_title="Transaction Type",
        )

        st.plotly_chart(
            fig_obligations,
            width="stretch",
        )

        # --------------------------------------------------
        # Annual net obligation change
        # --------------------------------------------------

        st.subheader("Annual Net Obligation Change")

        fig_net = go.Figure()

        fig_net.add_trace(
            go.Scatter(
                x=annual_summary["year"],
                y=annual_summary["net_obligation_change"],
                mode="lines+markers",
                name="Annual Net Obligation Change",
            )
        )

        fig_net.add_hline(
            y=0,
            line_dash="dash",
            line_color="gray",
        )

        fig_net.update_layout(
            title="Yearly Net Increase or Reduction in Obligations",
            xaxis_title="Transaction Year",
            yaxis_title="Annual Net Change ($)",
            yaxis_tickprefix="$",
            yaxis_tickformat="~s",
            hovermode="x unified",
        )

        st.plotly_chart(
            fig_net,
            width="stretch",
        )

        # --------------------------------------------------
        # Cumulative net obligation change
        # --------------------------------------------------

        st.subheader("Cumulative Net Obligation Change")

        fig_cumulative = go.Figure()

        fig_cumulative.add_trace(
            go.Scatter(
                x=annual_summary["year"],
                y=annual_summary["cumulative_net_obligations"],
                mode="lines+markers",
                name="Cumulative Net Change",
                fill="tozeroy",
            )
        )

        fig_cumulative.update_layout(
            title="Cumulative Net Obligation Change Over Time",
            xaxis_title="Transaction Year",
            yaxis_title="Cumulative Net Change ($)",
            yaxis_tickprefix="$",
            yaxis_tickformat="~s",
            hovermode="x unified",
        )

        st.plotly_chart(
            fig_cumulative,
            width="stretch",
        )

        st.caption(
            "Cumulative net change is the running sum of the annual "
            "net obligation changes in this transaction dataset. "
            "It should not be interpreted as cash paid or as an "
            "independently verified outstanding contract balance."
        )

        # --------------------------------------------------
        # Annual transaction results table
        # --------------------------------------------------

        st.subheader("Annual Transaction Results")

        display_annual = annual_summary.copy()

        st.dataframe(
            display_annual,
            width="stretch",
            hide_index=True,
            column_config={
                "year": st.column_config.NumberColumn("Year", format="%d"),
                "total_transactions": "Total Transactions",
                "positive_transactions": "Positive Transactions",
                "negative_transactions": "Negative Transactions",
                "gross_positive_obligations": (
                    st.column_config.NumberColumn(
                        "Gross Positive Obligations",
                        format="$%.2f",
                    )
                ),
                "gross_negative_obligations": (
                    st.column_config.NumberColumn(
                        "Gross Negative Obligations",
                        format="$%.2f",
                    )
                ),
                "net_obligation_change": (
                    st.column_config.NumberColumn(
                        "Annual Net Obligation Change",
                        format="$%.2f",
                    )
                ),
                "cumulative_net_obligations": (
                    st.column_config.NumberColumn(
                        "Cumulative Net Change",
                        format="$%.2f",
                    )
                ),
            },
        )

        # --------------------------------------------------
        # Annual transaction CSV export
        # --------------------------------------------------

        csv_transactions = annual_summary.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download Annual Transaction Analysis",
            data=csv_transactions,
            file_name="lockheed_annual_obligation_analysis.csv",
            mime="text/csv",
        )

    else:
        st.warning(
            "No valid transaction records were found in the source file."
        )

else:
    st.warning(
        "Lockheed Martin transaction history file was not found. "
        "Expected location: data/raw/lockheed_award_transactions.json"
    )
