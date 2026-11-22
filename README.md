Federal Program Performance & Spending Analytics Platform

An independent data analytics portfolio project that collects, transforms, validates, stores, and analyzes federal spending data from the USAspending.gov API.

The project demonstrates an end-to-end data analytics workflow using Python, SQL, PostgreSQL, data validation, exploratory analysis, and interactive dashboards. It also includes a historical investigation of federal contract obligations and deobligations associated with a major Department of Energy contract.

⸻

1. Project Overview

Federal spending data provides insight into how government agencies distribute funding, manage contracts, and allocate financial resources.

This project uses publicly available federal award data to examine:

* Federal award distribution across government agencies.
* Total award values and recipient concentration.
* Federal contract obligation trends.
* Positive and negative obligation adjustments.
* Historical changes in contract funding.
* Significant contract modifications and deobligations.

The project combines data engineering and analytical techniques to transform raw government spending records into structured datasets, SQL-based analysis, and visual reporting.

Project Objectives

1. Retrieve federal award information through the USAspending.gov API.
2. Build a repeatable data ingestion and transformation pipeline.
3. Clean and validate raw federal spending records.
4. Store structured award data in PostgreSQL.
5. Perform SQL-based spending analysis.
6. Develop an interactive Streamlit dashboard.
7. Investigate historical contract obligations and deobligations.
8. Communicate findings through visualizations and analytical reports.

⸻

2. Technology Stack

Category	Technologies
Programming	Python
Data Analysis	pandas, NumPy
Data Visualization	Matplotlib, Plotly
Database	PostgreSQL 18
SQL	PostgreSQL SQL
Dashboard	Streamlit
API Integration	USAspending.gov REST API, Requests
Data Validation	Python, pytest
Data Processing	JSON, CSV
Environment Management	Python virtual environment, python-dotenv
Version Control	Git, GitHub

⸻

3. Data Source

USAspending.gov API

The project retrieves publicly available federal award information from:

https://api.usaspending.gov/api/v2/search/spending_by_award/

The API provides information about federal awards, including:

* Award identification numbers.
* Recipient names.
* Award amounts.
* Awarding agencies.
* Award descriptions.
* Award start and end dates.

The initial award dataset uses four award categories:

Award Type Code	Award Category
A	Procurement Contract
B	Procurement Contract
C	Procurement Contract
D	Procurement Contract

The API response is saved as raw JSON before processing.

Data workflow:

USAspending.gov API → Raw JSON → Data Cleaning → Data Validation → Processed CSV → PostgreSQL → SQL Analysis → Dashboard

⸻

4. Data Engineering Pipeline

The project implements an end-to-end data processing workflow.

Step 1: Data Ingestion

Python retrieves federal award records through the USAspending.gov REST API.

The ingestion process:

* Sends API requests.
* Retrieves federal award information.
* Handles request timeouts.
* Saves the original API response as JSON.
* Preserves the raw data for subsequent processing.

Step 2: Data Cleaning

The transformation process uses pandas to prepare the award dataset.

Cleaning operations include:

* Selecting relevant fields.
* Standardizing column names.
* Handling missing values.
* Converting award amounts into numeric values.
* Preparing dates for analysis.
* Removing unnecessary fields.

Step 3: Data Validation

The validation process checks the quality and consistency of the processed dataset.

Validation includes:

* Required field checks.
* Missing value checks.
* Duplicate award identification.
* Unique internal identifier checks.
* Nonnegative award amount checks.
* Data consistency checks.

Step 4: PostgreSQL Database

Validated award records are loaded into PostgreSQL.

Database: federal_spending

Main table: awards

The table stores:

Column	Description
internal_id	Primary key for the award record
award_id	Federal award identification number
recipient_name	Award recipient
award_amount	Total award amount
generated_internal_id	Generated record identifier
awarding_agency	Federal awarding agency
start_date	Award start date
end_date	Award end date
description	Award description

The database uses an upsert process to manage existing records and avoid inserting duplicate internal identifiers.

Step 5: SQL Analytics

SQL queries are used to examine:

* Total award counts.
* Distinct award counts.
* Total award values.
* Average award values.
* Spending distribution by agency.
* Spending distribution by recipient.
* Agency and recipient rankings.

Step 6: Dashboard Development

An interactive Streamlit dashboard provides an accessible interface for exploring federal award information.

Dashboard functionality includes:

* Summary metrics.
* Award-level information.
* Agency-level analysis.
* Recipient-level analysis.
* Interactive filtering.
* Data export to CSV.
* Data quality information.
* Spending visualizations.

⸻

5. Award Dataset Results

The initial processed dataset contains 10 federal award records.

Dataset Summary

Metric	Result
Total award records	10
Distinct award IDs	10
Total award value	$404,739,667,534.78
Average award value	$40,473,966,753.48
Largest individual award	$51,269,205,263.03

Data Quality Observations

The processed dataset contains 10 distinct award records.

The pipeline validates award identifiers, required fields, numeric award amounts, and record consistency before loading the data into PostgreSQL.

Important limitation: This is a small analytical sample, not a comprehensive representation of all federal spending. The results describe the selected award records rather than total federal government expenditures.

⸻

6. Federal Award Spending Analysis

The award analysis examines the distribution of federal contract values across agencies and recipients.

The analytical objectives include:

* Identifying agencies with the largest award values.
* Comparing award counts across agencies.
* Ranking recipients by award value.
* Examining the concentration of federal contract awards.

Agency-Level Analysis

The project produces agency-level summaries containing:

* Number of awards.
* Total award value.
* Average award value.
* Percentage of total award value.

Recipient-Level Analysis

Recipient-level analysis examines:

* Total awards received.
* Aggregate award values.
* Recipient rankings.
* Concentration of award values among recipients.

The results are stored in processed CSV files and used by the dashboard.

⸻

7. Lockheed Martin Contract Analysis

Historical Contract Investigation

A second analytical component investigates the historical obligation activity associated with a Department of Energy contract awarded to Lockheed Martin Corporation.

Contract Award ID: DEAC0494AL85000

The analysis examines 594 historical contract transactions spanning:

October 15, 1993 – July 7, 2026

The transaction dataset includes:

* Transaction identifiers.
* Action dates.
* Action type descriptions.
* Modification numbers.
* Federal action obligations.
* Transaction descriptions.

The objective is to understand how the contract’s financial obligations changed over time.

Understanding Federal Obligations

Federal contract obligations represent the government’s legally binding financial commitments.

A positive obligation generally increases the amount committed to a contract.

A negative obligation generally represents a reduction or deobligation of previously recorded commitments.

These adjustments can result from contract modifications, funding changes, administrative actions, or other contractual events.

Importantly, obligations are not the same as actual payments or outlays.

Historical Transaction Results

Metric	Result
Total transactions	594
Gross positive obligations	$49.599 billion
Gross negative obligations	-$1.535 billion
Net obligation change	$48.064 billion
Historical period	1993–2026

The analysis separates positive and negative transactions to distinguish new funding commitments from reductions in previously recorded obligations.

This distinction provides a more complete understanding of historical contract funding activity than examining net changes alone.

⸻

8. Annual Obligation Analysis

Annual analysis aggregates contract transactions by calendar year.

The analysis calculates:

* Gross positive obligations.
* Gross negative obligations.
* Annual net obligation changes.
* Cumulative obligations.
* Year-over-year changes.

The purpose is to identify years with significant funding increases or reductions.

Key Historical Finding

2017 was an exceptional year in the contract’s obligation history.

The investigation identified approximately $1.506 billion in negative obligation adjustments during 2017.

This represented approximately 98.07% of the historical gross negative obligations identified in the 594-transaction dataset.

The finding led to a more detailed investigation of monthly activity and individual contract modifications.

⸻

9. Detailed 2017 Obligation Analysis

Annual Results

The 2017 analysis identified a significant net reduction in contract obligations.

Metric	Result
Opening cumulative obligations	$49,079,828,101.11
Ending cumulative obligations	$48,090,105,709.94
Gross positive obligations	$516,070,700.39
Gross negative obligations	-$1,505,793,091.56
Net annual obligation change	-$989,722,391.17
Percentage change	-2.02%

The contract experienced a net obligation reduction of approximately $989.7 million during 2017.

Monthly Analysis

Monthly transaction aggregation identified May 2017 as the primary driver of the annual reduction.

Metric	Amount
May 2017 net obligation change	-$1,347,149,687.35
All other months combined	$357,427,296.18
Full-year net obligation change	-$989,722,391.17

Reconciliation:

May 2017 + All Other Months = Full-Year Net Change

-$1,347,149,687.35 + $357,427,296.18 = -$989,722,391.17

The monthly results reconcile exactly with the annual analysis.

Monthly Transaction Distribution

Transaction Category	Count
Months with positive net changes	7
Months with negative net changes	8

May was the dominant negative month, while the remaining months collectively offset part of the reduction.

⸻

10. Investigation of Major May 2017 Transactions

The next stage examined the individual transactions responsible for the unusually large May reduction.

Three important modifications were identified.

Action Date	Modification	Action Type	Federal Action Obligation
2017-05-05	651	Novation Agreement	$0.00
2017-05-30	652	Funding Only Action	-$792,802,785.58
2017-05-31	653	Funding Only Action	-$554,346,901.77

The two largest negative transactions occurred immediately after the May 5 novation agreement.

Both major transactions included descriptions identifying Lockheed Martin Corporation as the new contracting party.

Major Transaction Findings

Metric	Result
First major reduction	-$792,802,785.58
Second major reduction	-$554,346,901.77
Combined reduction	-$1,347,149,687.35
Share of 2017 gross negative obligations	89.46%
Share of historical gross negative obligations	87.74%

These two transactions account for approximately 89.46% of all negative obligations recorded during 2017.

They also represent approximately 87.74% of all historical negative obligations in the transaction dataset.

After-Novation Transaction Analysis

The five transactions following the novation-related activity showed:

Metric	Result
Transactions examined	5
Positive transactions	0
Net obligation change	-$1,364,409,755.27

The transaction descriptions and timing suggest a significant relationship between the contractor transition and the subsequent funding adjustments.

However, transaction descriptions alone do not establish the complete legal or financial reason for the reductions. The analysis identifies the timing and magnitude of the changes without claiming an independently verified contractual explanation.

⸻

11. Key Analytical Findings

The historical investigation produced several important findings.

Finding 1: Historical negative obligations were highly concentrated.

Approximately 98.07% of the historical gross negative obligations occurred in 2017.

Finding 2: May 2017 drove the annual reduction.

May recorded a net obligation reduction of approximately $1.347 billion.

Finding 3: Two transactions accounted for most historical reductions.

The May 30 and May 31 modifications represented approximately 87.74% of historical gross negative obligations.

Finding 4: Positive obligations partially offset the reductions.

The remaining months of 2017 generated approximately $357.4 million in net positive obligation changes.

Finding 5: Annual and monthly results reconciled.

The monthly transaction analysis matched the annual net obligation change exactly, confirming consistency between the two analytical approaches.

Business Significance

This investigation demonstrates how transaction-level federal spending data can reveal financial changes that are not immediately apparent from aggregate award amounts.

By combining annual trends, monthly aggregation, transaction descriptions, and individual modification analysis, the project identifies the specific events responsible for major changes in contract obligations.

⸻

12. Visualizations and Reports

The project includes visual reports designed to communicate spending patterns and historical contract changes.

Federal Award Analysis

* Number of awards by agency.
* Total award value by agency.
* Agency-level spending summaries.
* Recipient-level spending summaries.

Lockheed Martin Contract Analysis

* Annual obligation trends.
* Annual positive and negative obligations.
* Historical obligation changes.
* Monthly obligation changes.
* 2017 cumulative obligation analysis.
* Major historical deobligation transactions.

The visualizations help communicate financial trends, identify unusual changes, and support further investigation.

⸻

13. Project Structure

federal_spending_analytics/
│
├── data/
│   ├── raw/
│   │   ├── awards_sample.json
│   │   └── lockheed_award_transactions.json
│   │
│   └── processed/
│       ├── awards_sample.csv
│       ├── agency_spending_summary.csv
│       └── recipient_spending_summary.csv
│
├── dashboards/
│   └── spending_dashboard.py
│
├── reports/
│   ├── number_of_awards_by_agency.png
│   ├── total_award_value_by_agency.png
│   ├── 2017_monthly_obligations.png
│   └── annual_positive_negative_obligations.html
│
├── src/
│   ├── ingestion/
│   │   └── usa_spending_api.py
│   │
│   └── analysis/
│       ├── lockheed_annual_analysis.py
│       ├── lockheed_monthly_analysis.py
│       ├── lockheed_historical_ranking.py
│       └── lockheed_historical_visualization.py
│
├── tests/
│
├── requirements.txt
├── .gitignore
└── README.md

⸻

14. Installation and Setup

Prerequisites

* Python 3.12 or later.
* PostgreSQL 18.
* Git.
* Access to the USAspending.gov API.

Clone the Repository

git clone https://github.com/saltanikamal/federal-program-performance-analytics.git
cd federal_spending_analytics

Create a Virtual Environment

python3 -m venv venv

Activate the Environment

macOS/Linux:

source venv/bin/activate

Install Dependencies

pip install -r requirements.txt

Configure PostgreSQL

Create the project database:

CREATE DATABASE federal_spending;

Configure the database connection using environment variables in a local .env file.

Do not commit database credentials or other secrets to GitHub.

Run the Dashboard

streamlit run dashboards/spending_dashboard.py

⸻

15. Skills Demonstrated

This project demonstrates practical experience with:

Data Engineering

* REST API integration.
* Data ingestion.
* ETL pipeline development.
* JSON and CSV processing.
* Data transformation.
* Database loading.

Data Analytics

* Exploratory data analysis.
* Financial data analysis.
* Aggregation and grouping.
* Trend analysis.
* Transaction-level investigation.
* Financial reconciliation.

Database Management

* PostgreSQL.
* Relational database design.
* SQL queries.
* Data integrity.
* Primary keys.
* Upsert operations.
* Analytical database views.

Data Quality

* Required field validation.
* Duplicate detection.
* Missing value checks.
* Numeric validation.
* Data consistency checks.

Visualization and Reporting

* Streamlit.
* Plotly.
* Matplotlib.
* Interactive dashboards.
* Analytical reporting.

Software Development

* Python scripting.
* Modular project structure.
* Git and GitHub.
* Virtual environments.
* Automated testing.

⸻

16. Project Limitations

Several limitations should be considered when interpreting the results.

1. The initial federal award dataset contains only 10 records and should not be interpreted as a comprehensive picture of federal spending.
2. The Lockheed Martin investigation focuses on one specific contract award.
3. Negative obligations represent reductions in recorded obligations, not necessarily cash refunds or actual payments.
4. Contract obligations and federal outlays measure different aspects of government spending.
5. Transaction descriptions provide context but do not independently establish the complete contractual or legal explanation for every financial adjustment.
6. Historical results depend on the underlying USAspending.gov data available when the API records were retrieved.

These limitations provide opportunities for future expansion, including larger award datasets, additional agencies, multiple contractors, and more extensive transaction-level comparisons.

⸻

17. Future Enhancements

Potential improvements include:

* Expanding the federal award dataset.
* Analyzing additional federal agencies.
* Comparing multiple major contractors.
* Developing additional SQL analytical views.
* Adding more comprehensive automated data quality tests.
* Investigating relationships between obligations and outlays.
* Expanding interactive dashboard functionality.
* Developing predictive models for federal spending trends.

⸻

18. Conclusion

The Federal Program Performance & Spending Analytics Platform demonstrates an end-to-end approach to working with publicly available federal financial data.

The project combines API integration, Python-based ETL development, data validation, PostgreSQL database management, SQL analytics, and interactive visualization.

The Lockheed Martin contract investigation extends the project beyond basic spending summaries by examining 594 historical transactions, identifying significant deobligations, investigating contractor transition activity, and reconciling annual and monthly financial changes.

Together, these components demonstrate the ability to transform raw government data into structured analytical information, investigate financial trends, validate findings, and communicate results through meaningful visualizations and reporting.

Repository:
https://github.com/saltanikamal/federal-program-performance-analytics

Project Type: Independent Data Analytics Portfolio Project

Focus Areas: Federal Spending Analytics | Data Engineering | Financial Analysis | SQL | Python | PostgreSQL | Data Visualization
