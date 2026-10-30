"""
Federal Program Performance & Spending Analytics Platform

Features:
- PostgreSQL data connection
- Agency and recipient filters
- Spending summary metrics
- Award-value visualization
- Award records table
- CSV export
- Nine data quality checks

Important:
This dashboard displays the records currently loaded into the project
database. It does not represent all federal spending nationwide.
Award values are not necessarily amounts actually paid.
"""

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
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
    """
    Create and cache the SQLAlchemy database engine.
    """

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

# Work with a separate copy so the original loaded data remains unchanged.
filtered_df = awards_df.copy()

# Normalize agency labels for filtering.
# The original database values are not changed.
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
    total_awards = int(
        filtered_df["award_id"].nunique()
    )

    total_recorded_value = filtered_df["award_amount"].sum(
        min_count=1
    )

    average_award_value = filtered_df["award_amount"].mean()

    largest_award_value = filtered_df["award_amount"].max()

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "Unique Award IDs",
        f"{total_awards:,}",
    )

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
            number_of_awards=(
                "award_id",
                "nunique",
            ),
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

        st.plotly_chart(
            fig,
            width="stretch",
        )

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
            "Recorded Award Value ($)": (
                st.column_config.NumberColumn(
                    "Recorded Award Value ($)",
                    format="$%.2f",
                )
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

    csv_data = display_df.to_csv(
        index=False
    ).encode("utf-8")

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


# --------------------------------------------------
# Helper function: detect NULL, NaN, or blank strings
# --------------------------------------------------

def missing_or_blank_count(series):
    """
    Count missing values and strings that contain only whitespace.
    """

    missing_mask = series.isna()

    blank_mask = (
        series
        .astype("string")
        .str.strip()
        .eq("")
        .fillna(False)
    )

    return int(
        (missing_mask | blank_mask).sum()
    )


# --------------------------------------------------
# Check 1: Missing or blank award IDs
# --------------------------------------------------

missing_award_ids = missing_or_blank_count(
    awards_df["award_id"]
)


# --------------------------------------------------
# Check 2: Duplicate nonblank award IDs
# --------------------------------------------------

award_ids = (
    awards_df["award_id"]
    .astype("string")
    .str.strip()
)

valid_award_ids = award_ids[
    award_ids.notna() & award_ids.ne("")
]

duplicate_award_ids = int(
    valid_award_ids.duplicated().sum()
)


# --------------------------------------------------
# Check 3: Missing or blank recipient names
# --------------------------------------------------

missing_recipients = missing_or_blank_count(
    awards_df["recipient_name"]
)


# --------------------------------------------------
# Check 4: Missing award amounts
# --------------------------------------------------

missing_award_amounts = int(
    awards_df["award_amount"].isna().sum()
)


# --------------------------------------------------
# Check 5: Negative award amounts
# --------------------------------------------------

negative_award_amounts = int(
    (awards_df["award_amount"] < 0)
    .fillna(False)
    .sum()
)


# --------------------------------------------------
# Check 6: Missing or blank awarding agencies
# --------------------------------------------------

missing_agencies = missing_or_blank_count(
    awards_df["awarding_agency"]
)


# --------------------------------------------------
# Check 7: Duplicate non-null internal IDs
# --------------------------------------------------

duplicate_internal_ids = int(
    awards_df["internal_id"]
    .dropna()
    .duplicated()
    .sum()
)


# --------------------------------------------------
# Check 8: Missing or blank generated identifiers
# --------------------------------------------------

missing_generated_ids = missing_or_blank_count(
    awards_df["generated_internal_id"]
)


# --------------------------------------------------
# Check 9: Invalid date ranges
# --------------------------------------------------

invalid_date_mask = (
    awards_df["start_date"].notna()
    & awards_df["end_date"].notna()
    & (
        awards_df["end_date"]
        < awards_df["start_date"]
    )
)

invalid_date_ranges = int(
    invalid_date_mask.sum()
)


# ==================================================
# 11. DISPLAY DATA QUALITY METRICS
# ==================================================

quality_checks = [
    ("Missing Award IDs", missing_award_ids),
    ("Duplicate Award IDs", duplicate_award_ids),
    ("Missing Recipient Names", missing_recipients),
    ("Missing Award Amounts", missing_award_amounts),
    ("Negative Award Amounts", negative_award_amounts),
    ("Missing Awarding Agencies", missing_agencies),
    ("Duplicate Internal IDs", duplicate_internal_ids),
    ("Missing Generated IDs", missing_generated_ids),
    ("Invalid Date Ranges", invalid_date_ranges),
]

quality_cols = st.columns(4)

for index, (check_name, issue_count) in enumerate(
    quality_checks
):
    with quality_cols[index % 4]:
        st.metric(
            check_name,
            f"{issue_count:,}",
        )


# ==================================================
# 12. MISSING VALUES BY COLUMN
# ==================================================

with st.expander("View missing values by column"):

    missing_report = (
        awards_df.isna()
        .sum()
        .rename("Missing Values")
        .reset_index()
        .rename(
            columns={
                "index": "Column",
                "Missing Values": "Missing Values",
            }
        )
    )

    # Also report blank strings in text columns.
    text_columns = awards_df.select_dtypes(
        include=["object", "string"]
    ).columns

    blank_counts = {}

    for column in text_columns:
        blank_counts[column] = int(
            (
                awards_df[column]
                .notna()
                & awards_df[column]
                .astype("string")
                .str.strip()
                .eq("")
                .fillna(False)
            ).sum()
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


# ==================================================
# 13. INVALID DATE RECORDS
# ==================================================

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
        st.success(
            "No invalid date ranges were detected."
        )

    else:
        st.dataframe(
            invalid_dates_df,
            width="stretch",
            hide_index=True,
        )


# ==================================================
# 14. DATA QUALITY SUMMARY
# ==================================================

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
        f"The nine checks detected "
        f"{total_issue_instances:,} potential issue instances. "
        "One record may contribute to more than one check. "
        "Review the metrics and expanders above."
    )


# ==================================================
# 15. DASHBOARD FOOTER
# ==================================================

st.divider()

st.caption(
    f"Database: {DB_NAME} | "
    f"Records loaded: {len(awards_df):,} | "
    f"Records displayed: {len(filtered_df):,} | "
    "Data source: project PostgreSQL database"
)
