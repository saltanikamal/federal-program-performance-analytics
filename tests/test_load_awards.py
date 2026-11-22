import numpy as np
import pandas as pd
import pytest

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    MetaData,
    Numeric,
    Table,
    Text,
)

import src.database.load_awards as loader


# --------------------------------------------------
# 1. SAMPLE AWARD DATA
# --------------------------------------------------

def create_sample_awards():

    return pd.DataFrame({
        "internal_id": [1001, 1002, 1003],

        "award_id": [
            "DEAC0494AL85000",
            "DEAC0494AL85001",
            "DEAC0494AL85002",
        ],

        "recipient_name": [
            "Lockheed Martin Corp",
            "Boeing Company",
            "General Dynamics",
        ],

        "award_amount": [
            1000000.00,
            2000000.00,
            3000000.00,
        ],

        "generated_internal_id": [
            "ID001",
            "ID002",
            "ID003",
        ],

        "total_outlays": [
            -1000.00,
            5000.00,
            10000.00,
        ],

        "awarding_agency": [
            "Department of Energy",
            "Department of Defense",
            "Department of Defense",
        ],

        "start_date": [
            "2020-01-01",
            "2021-01-01",
            "2022-01-01",
        ],

        "end_date": [
            "2025-01-01",
            "2026-01-01",
            "2027-01-01",
        ],

        "description": [
            "Research contract",
            "Defense contract",
            "Technology contract",
        ],
    })


# --------------------------------------------------
# 2. REQUIRED VALUE VALIDATION
# --------------------------------------------------

def test_required_values_pass():

    df = create_sample_awards()

    loader.validate_required_values(df)


@pytest.mark.parametrize(
    "column,value",
    [
        ("award_id", None),
        ("recipient_name", None),
        ("generated_internal_id", None),
        ("award_id", ""),
        ("recipient_name", "   "),
    ],
)
def test_missing_required_values_fail(column, value):

    df = create_sample_awards()

    df.loc[0, column] = value

    with pytest.raises(ValueError, match="missing or blank"):

        loader.validate_required_values(df)


# --------------------------------------------------
# 3. INTERNAL ID VALIDATION
# --------------------------------------------------

def test_valid_internal_ids_pass():

    df = create_sample_awards()

    loader.validate_internal_ids(df)

    assert df["internal_id"].dtype == "int64"


@pytest.mark.parametrize(
    "invalid_id",
    [
        "invalid",
        1001.5,
        np.inf,
        float(2**63),
    ],
)
def test_invalid_internal_ids_fail(invalid_id):

    df = create_sample_awards()

    df["internal_id"] = df["internal_id"].astype(object)

    df.loc[0, "internal_id"] = invalid_id

    with pytest.raises(ValueError):

        loader.validate_internal_ids(df)


def test_missing_internal_id_fails():

    df = create_sample_awards()

    df.loc[0, "internal_id"] = np.nan

    with pytest.raises(ValueError, match="missing or invalid"):

        loader.validate_internal_ids(df)


def test_duplicate_internal_ids_fail():

    df = create_sample_awards()

    df.loc[1, "internal_id"] = 1001

    with pytest.raises(ValueError, match="duplicate"):

        loader.validate_internal_ids(df)


# --------------------------------------------------
# 4. AWARD AMOUNT VALIDATION
# --------------------------------------------------

def test_valid_award_amounts_pass():

    df = create_sample_awards()

    loader.validate_award_amounts(df)


@pytest.mark.parametrize(
    "invalid_amount",
    [
        -1000,
        "invalid",
        np.inf,
        -np.inf,
        10**13,
    ],
)
def test_invalid_award_amounts_fail(invalid_amount):

    df = create_sample_awards()

    df["award_amount"] = df["award_amount"].astype(object)

    df.loc[0, "award_amount"] = invalid_amount

    with pytest.raises(ValueError):

        loader.validate_award_amounts(df)


def test_missing_award_amount_fails():

    df = create_sample_awards()

    df.loc[0, "award_amount"] = np.nan

    with pytest.raises(ValueError, match="missing or invalid"):

        loader.validate_award_amounts(df)


def test_zero_award_amount_passes():

    df = create_sample_awards()

    df.loc[0, "award_amount"] = 0

    loader.validate_award_amounts(df)

    assert df.loc[0, "award_amount"] == 0


# --------------------------------------------------
# 5. TOTAL OUTLAYS VALIDATION
# --------------------------------------------------

def test_valid_total_outlays_pass():

    df = create_sample_awards()

    loader.validate_total_outlays(df)


def test_negative_total_outlays_are_retained():

    df = create_sample_awards()

    loader.validate_total_outlays(df)

    assert df.loc[0, "total_outlays"] == -1000.00


@pytest.mark.parametrize(
    "invalid_outlay",
    [
        "invalid",
        np.inf,
        -np.inf,
        10**16,
    ],
)
def test_invalid_total_outlays_fail(invalid_outlay):

    df = create_sample_awards()

    df["total_outlays"] = df["total_outlays"].astype(object)

    df.loc[0, "total_outlays"] = invalid_outlay

    with pytest.raises(ValueError):

        loader.validate_total_outlays(df)


def test_missing_total_outlays_are_allowed():

    df = create_sample_awards()

    df.loc[0, "total_outlays"] = np.nan

    loader.validate_total_outlays(df)

    assert pd.isna(df.loc[0, "total_outlays"])


# --------------------------------------------------
# 6. DATE VALIDATION
# --------------------------------------------------

def test_valid_dates_pass():

    df = create_sample_awards()

    loader.validate_dates(df)

    assert str(df.loc[0, "start_date"]) == "2020-01-01"


def test_missing_dates_are_allowed():

    df = create_sample_awards()

    df.loc[0, "start_date"] = None

    loader.validate_dates(df)

    assert pd.isna(df.loc[0, "start_date"])


def test_invalid_dates_fail():

    df = create_sample_awards()

    df.loc[0, "start_date"] = "not-a-date"

    with pytest.raises(ValueError, match="invalid dates"):

        loader.validate_dates(df)


# --------------------------------------------------
# 7. DATABASE RECORD PREPARATION
# --------------------------------------------------

def test_prepare_database_records():

    df = create_sample_awards()

    df.loc[0, "description"] = None

    records = loader.prepare_database_records(df)

    assert len(records) == 3

    assert isinstance(records, list)

    assert records[0]["description"] is None

    assert records[0]["internal_id"] == 1001


# --------------------------------------------------
# 8. EMPTY CSV TEST
# --------------------------------------------------

def test_empty_csv_does_not_connect_to_database(
    tmp_path,
    monkeypatch,
):

    csv_path = tmp_path / "empty.csv"

    create_sample_awards().iloc[0:0].to_csv(
        csv_path,
        index=False,
    )

    monkeypatch.setattr(
        loader,
        "CSV_PATH",
        csv_path,
    )

    def unexpected_connection(*args, **kwargs):

        pytest.fail(
            "Database connection should not occur."
        )

    monkeypatch.setattr(
        loader,
        "create_engine",
        unexpected_connection,
    )

    loader.load_awards()


# --------------------------------------------------
# 9. MISSING CSV TEST
# --------------------------------------------------

def test_missing_csv_file_fails(
    tmp_path,
    monkeypatch,
):

    csv_path = tmp_path / "missing.csv"

    monkeypatch.setattr(
        loader,
        "CSV_PATH",
        csv_path,
    )

    with pytest.raises(FileNotFoundError):

        loader.load_awards()


# --------------------------------------------------
# 10. MISSING REQUIRED COLUMN TEST
# --------------------------------------------------

def test_missing_required_column_fails(
    tmp_path,
    monkeypatch,
):

    df = create_sample_awards()

    df = df.drop(
        columns=["recipient_name"]
    )

    csv_path = tmp_path / "awards.csv"

    df.to_csv(
        csv_path,
        index=False,
    )

    monkeypatch.setattr(
        loader,
        "CSV_PATH",
        csv_path,
    )

    with pytest.raises(
        ValueError,
        match="Missing required columns",
    ):

        loader.load_awards()


# --------------------------------------------------
# 11. DATABASE UPSERT WORKFLOW TEST
# --------------------------------------------------

def test_successful_database_loading(
    tmp_path,
    monkeypatch,
):

    df = create_sample_awards()

    csv_path = tmp_path / "awards.csv"

    df.to_csv(
        csv_path,
        index=False,
    )

    monkeypatch.setattr(
        loader,
        "CSV_PATH",
        csv_path,
    )

    # Create a simulated PostgreSQL awards table.

    metadata = MetaData()

    awards_table = Table(
        "awards",
        metadata,

        Column(
            "internal_id",
            BigInteger,
            primary_key=True,
        ),

        Column("award_id", Text),
        Column("recipient_name", Text),
        Column("award_amount", Numeric(15, 2)),
        Column("generated_internal_id", Text),
        Column("total_outlays", Numeric(18, 2)),
        Column("awarding_agency", Text),
        Column("start_date", Date),
        Column("end_date", Date),
        Column("description", Text),
    )

    # Simulate database execution.

    class FakeResult:

        rowcount = 3

    class FakeConnection:

        def execute(self, statement):

            self.statement = statement

            return FakeResult()

    class FakeTransaction:

        def __init__(self, connection):

            self.connection = connection

        def __enter__(self):

            return self.connection

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):

            return False

    class FakeEngine:

        def __init__(self):

            self.connection = FakeConnection()

            self.disposed = False

        def begin(self):

            return FakeTransaction(
                self.connection
            )

        def dispose(self):

            self.disposed = True

    fake_engine = FakeEngine()

    monkeypatch.setattr(
        loader,
        "create_engine",
        lambda *args, **kwargs: fake_engine,
    )

    monkeypatch.setattr(
        loader,
        "Table",
        lambda *args, **kwargs: awards_table,
    )

    # Execute the loading process.

    loader.load_awards()

    # Confirm database execution.

    assert fake_engine.connection.statement is not None

    assert fake_engine.disposed is True
