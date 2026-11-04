"""Transaction-level federal obligation analysis.

Input is a CSV or a JSON list of USAspending transaction records. Obligation
changes are signed flows, not payments, current balances, or award face values.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ("id", "action_date", "federal_action_obligation")


def prepare_transactions(records: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize transaction records, preserving signed amounts."""
    missing = [name for name in REQUIRED_COLUMNS if name not in records.columns]
    if missing:
        raise ValueError(f"Missing required transaction fields: {missing}")

    df = records.copy()
    if df["id"].isna().any() or df["id"].astype("string").str.strip().eq("").any():
        raise ValueError("Transaction IDs must be present")
    if df["id"].duplicated().any():
        raise ValueError("Duplicate transaction IDs found; deduplicate at source")

    df["action_date"] = pd.to_datetime(df["action_date"], errors="coerce")
    if df["action_date"].isna().any():
        raise ValueError("Invalid or missing action_date values")

    raw_amounts = df["federal_action_obligation"]
    amounts = pd.to_numeric(raw_amounts, errors="coerce")
    if (raw_amounts.notna() & amounts.isna()).any():
        raise ValueError("Non-numeric federal_action_obligation values")
    df["federal_action_obligation"] = amounts.fillna(0.0)
    df["calendar_year"] = df["action_date"].dt.year
    # Federal fiscal years start October 1.
    df["fiscal_year"] = df["calendar_year"] + (
        df["action_date"].dt.month >= 10
    ).astype(int)
    df["month"] = df["action_date"].dt.to_period("M").astype(str)
    return df


def summarize_transactions(
    records: pd.DataFrame, *, year: int | None = None,
    year_basis: str = "calendar"
) -> dict:
    """Summarize signed funding actions for a calendar or federal fiscal year."""
    if year_basis not in {"calendar", "fiscal"}:
        raise ValueError("year_basis must be 'calendar' or 'fiscal'")
    df = prepare_transactions(records)
    if year is not None:
        field = "calendar_year" if year_basis == "calendar" else "fiscal_year"
        df = df.loc[df[field] == year].copy()

    obligations = df["federal_action_obligation"]
    positive = float(obligations.loc[obligations > 0].sum())
    negative = float(obligations.loc[obligations < 0].sum())
    monthly = (
        df.groupby("month", sort=True)["federal_action_obligation"]
        .agg(transaction_count="size", net_obligations="sum")
        .reset_index()
    )
    action_field = (
        "action_type_description" if "action_type_description" in df.columns
        else "action_type" if "action_type" in df.columns else None
    )
    by_action = (
        df.assign(action_category=df[action_field].fillna("Unknown"))
          .groupby("action_category", dropna=False)["federal_action_obligation"]
          .agg(transaction_count="size", net_obligations="sum")
          .reset_index()
        if action_field else pd.DataFrame(
            columns=["action_category", "transaction_count", "net_obligations"]
        )
    )
    detail_columns = [
        col for col in ("id", "action_date", "modification_number",
                        "action_type_description", "federal_action_obligation",
                        "description") if col in df.columns
    ]
    largest_reductions = (
        df.loc[obligations < 0]
          .nsmallest(5, "federal_action_obligation")[detail_columns]
          .copy()
    )
    if "action_date" in largest_reductions:
        largest_reductions["action_date"] = largest_reductions[
            "action_date"
        ].dt.strftime("%Y-%m-%d")

    return {
        "year": year,
        "year_basis": year_basis,
        "transaction_count": int(len(df)),
        "positive_obligations": positive,
        "negative_obligations": negative,
        "net_obligations": positive + negative,
        "zero_dollar_transactions": int((obligations == 0).sum()),
        "monthly": monthly.to_dict(orient="records"),
        "by_action_type": by_action.to_dict(orient="records"),
        "largest_reductions": largest_reductions.to_dict(orient="records"),
    }


def load_transactions(path: str | Path) -> pd.DataFrame:
    """Read a local CSV or list-of-records JSON export."""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() == ".json":
        with path.open(encoding="utf-8") as stream:
            records = json.load(stream)
        if not isinstance(records, list):
            raise ValueError("JSON input must be a list of transaction objects")
        return pd.DataFrame(records)
    raise ValueError("Input must be a .csv or .json file")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze signed USAspending transactions")
    parser.add_argument("input_file", help="CSV or JSON transaction export")
    parser.add_argument("--year", type=int, default=None)
    parser.add_argument("--basis", choices=("calendar", "fiscal"), default="calendar")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    summary = summarize_transactions(
        load_transactions(args.input_file), year=args.year, year_basis=args.basis
    )
    output = json.dumps(summary, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
