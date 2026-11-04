# Transaction-level obligation analysis

This optional module extends award-level reporting with **signed funding changes**.

## Usage

From the project root, with dependencies installed:

```bash
python -m pytest -q tests/test_transaction_obligations.py
python -m src.analytics.transaction_obligations data/raw/sandia_transactions_2017.csv --year 2017
python -m src.analytics.transaction_obligations data/raw/sandia_transactions_2017.csv --year 2017 --output reports/sandia_2017_summary.json
python -m src.analytics.transaction_obligations data/raw/sandia_transactions_2017.csv --year 2017 --basis fiscal
```

The CSV/JSON export must contain `id`, `action_date`, and
`federal_action_obligation`. Optional columns include `modification_number`,
`action_type_description`, and `description`. JSON must be a list of records.

The module provides positive, negative, and net obligation changes; counts
zero-dollar administrative transactions; groups changes by month and action
type; and lists the five largest deobligations.

## Sandia 2017 case study: preliminary result

From a locally supplied extract of **21 calendar-year 2017 transactions**
under the former Sandia management contract DE-AC04-94AL85000:

| Measure | Amount |
| --- | ---: |
| Positive obligation changes | $516,070,700.39 |
| Negative obligation changes | -$1,505,793,091.56 |
| Net obligation changes | **-$989,722,391.17** |

The two largest negative transactions were modification 652 (May 30, 2017)
and modification 653 (May 31, 2017). Further research is needed to establish
why those funds were deobligated; proximity to the laboratory management
transition alone does not establish causation.

**Data provenance:** these figures come from an analyst-provided transaction
extract; they are not calculated from a checked-in complete transaction file.
Run the module against the full export to reproduce and validate the totals.
The provided listing contains amounts in rounded scientific notation, so use
the underlying raw data for exact reconciliation.

**Interpretation cautions:**
- Net obligations are **changes to committed federal funding**, not cash paid,
  losses, outstanding balances, or total lifetime award values.
- Calendar 2017 (Jan–Dec) is not FY2017 (Oct 2016–Sep 2017).
- Transaction count reflects the supplied extract, not necessarily all
  modifications or all federal contracts.
- A zero-dollar modification may document an important administrative change.
- Do not sum award face values and transaction changes as if interchangeable.
- Include transaction ID in uniqueness checks to avoid double-counting.

## Next enhancements

1. Add an API ingestion adapter for paginated individual award transactions.
2. Persist normalized transaction rows in PostgreSQL with unique transaction IDs.
3. Add Streamlit month and modification drill-downs.
4. Compare historical periods and record provenance and query parameters.
