Federal Program Performance & Spending Analytics Platform

An independent data analytics portfolio project that collects, transforms, validates, stores, and analyzes federal award data from the U.S. government’s USAspending.gov API.

The project demonstrates an end-to-end data workflow using Python, SQL, PostgreSQL, and Streamlit.

Project Overview

Federal agencies manage large amounts of award data across government programs. This project uses publicly available federal award records to demonstrate how raw data can be transformed into structured, validated information and presented through an interactive analytics dashboard.

The platform focuses on data quality, database management, SQL analysis, and performance reporting.

Key Features

* API Data Ingestion: Retrieves federal award records from USAspending.gov.
* Data Cleaning: Standardizes column names, handles missing values, and converts numeric fields.
* Data Validation: Checks required fields, duplicate identifiers, negative award amounts, and date consistency.
* Automated ETL Pipeline: Coordinates data extraction, transformation, validation, and database loading.
* PostgreSQL Database: Stores structured award records and supports analytical queries.
* SQL Analytics: Summarizes award counts and award values by federal agency and recipient.
* Interactive Dashboard: Uses Streamlit and Plotly to present key metrics and visualizations.

Technology Stack

Category	Technologies
Programming	Python
Data Analysis	pandas, NumPy
Data Ingestion	USAspending.gov API, requests
Data Validation	Python, pandas
Database	PostgreSQL
Database Integration	SQLAlchemy, psycopg2
Analytics	SQL
Dashboard	Streamlit, Plotly
Visualization	Matplotlib, Plotly
Environment Management	Python virtual environment, python-dotenv

Data Pipeline Architecture

USAspending.gov API
        |
        v
Data Extraction
        |
        v
Raw JSON Records
        |
        v
Data Cleaning and Transformation
        |
        v
Data Quality Validation
        |
        v
Processed CSV Data
        |
        v
PostgreSQL Database
        |
        v
SQL Analytics
        |
        v
Interactive Streamlit Dashboard

Current Project Results

The current sample database contains 10 unique federal award records.

Metric	Result
Total award records	10
Unique award IDs	10
Total recorded award value	$403,313,775,104.97
Department of Energy awards	7
Department of Defense awards	3

Award Value by Agency

Federal Agency	Number of Awards	Total Award Value
Department of Energy	7	$281,171,305,002.74
Department of Defense	3	$122,142,470,102.23
Total	10	$403,313,775,104.97

These figures describe the current sample dataset, not all federal spending nationwide.

Important: Award amounts represent recorded award values and should not be interpreted as amounts already paid to recipients. Payment activity requires separate analysis of outlay data.

Dashboard

The interactive dashboard provides:

* Total number of awards
* Total recorded award value
* Average and largest award values
* Agency-level award comparisons
* Recipient-level analysis
* Agency and recipient filters
* Data quality reporting

Project Structure

federal_spending_analytics/
|
├── dashboards/
│   └── spending_dashboard.py
|
├── data/
│   ├── raw/
│   │   └── awards_sample.json
│   └── processed/
│       ├── awards_sample.csv
│       ├── agency_spending_summary.csv
│       └── recipient_spending_summary.csv
|
├── reports/
│   ├── number_of_awards_by_agency.png
│   └── total_award_value_by_agency.png
|
├── src/
│   ├── analytics/
│   ├── database/
│   ├── ingestion/
│   ├── run/
│   └── transformation/
|
├── tests/
├── requirements.txt
├── .gitignore
└── README.md

Installation and Setup

1. Clone the repository

git clone https://github.com/saltanikamal/federal-program-performance-analytics.git
cd federal_spending_analytics

2. Create and activate a virtual environment

python3 -m venv venv
source venv/bin/activate

3. Install dependencies

pip install -r requirements.txt

4. Configure PostgreSQL

Create a PostgreSQL database named:

CREATE DATABASE federal_spending;

Configure your local database connection using environment variables in a .env file.

Do not commit .env or database credentials to GitHub.

5. Run the data pipeline

python -m src.run.pipeline

6. Launch the dashboard

streamlit run dashboards/spending_dashboard.py

Open the local Streamlit address displayed in your terminal.

Data Source

Data is retrieved from the publicly available USAspending.gov API, which provides federal award information.

Official source: https://www.usaspending.gov/

Limitations

* The current implementation uses a small sample of 10 award records.
* Results should not be interpreted as a complete representation of federal spending.
* Award values are not necessarily equivalent to actual payments or outlays.
* The project is an independent portfolio demonstration and is not affiliated with a federal agency.

Project Purpose

This project demonstrates practical skills in:

* Python-based data engineering
* API integration and ETL development
* Data cleaning and validation
* Relational database design
* PostgreSQL and SQL analytics
* Data visualization and dashboard development
* Communicating analytical findings

Project Type: Independent Data Science and Analytics Portfolio Project
