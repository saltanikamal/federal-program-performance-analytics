import pandas as pd


def awards_to_dataframe(records):
    """
    Convert USAspending API records into a clean DataFrame.
    """

    df = pd.DataFrame(records)

    # Rename API fields to consistent column names.
    df = df.rename(
        columns={
            "Award ID": "award_id",
            "Recipient Name": "recipient_name",
            "Award Amount": "award_amount",
            "Awarding Agency": "awarding_agency",
            "Start Date": "start_date",
            "End Date": "end_date",
            "Description": "description",
        }
    )

    # Check that essential fields exist.
    required_columns = [
        "internal_id",
        "award_id",
        "recipient_name",
        "award_amount",
        "generated_internal_id",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required API fields: {missing_columns}"
        )

    # Clean text fields.
    text_columns = [
        "award_id",
        "recipient_name",
        "generated_internal_id",
        "awarding_agency",
        "description",
    ]

    for column in text_columns:
        if column not in df.columns:
            df[column] = pd.NA

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    # Convert internal IDs to numeric values.
    df["internal_id"] = pd.to_numeric(
        df["internal_id"],
        errors="coerce",
    )

    # Convert award amounts to numeric values.
    df["award_amount"] = pd.to_numeric(
        df["award_amount"],
        errors="coerce",
    )

    # Convert award dates to datetime values.
    for column in ["start_date", "end_date"]:
        if column not in df.columns:
            df[column] = pd.NA

        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
        )

    # Return columns in a consistent order.
    output_columns = [
        "internal_id",
        "award_id",
        "recipient_name",
        "award_amount",
        "generated_internal_id",
        "awarding_agency",
        "start_date",
        "end_date",
        "description",
    ]

    return df[output_columns]
