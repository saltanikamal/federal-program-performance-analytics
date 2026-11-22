from src.ingestion.usa_spending_api import fetch_awards

# Retrieve awards from the USAspending API.
rows = fetch_awards()

print(f"Records returned: {len(rows)}")
print("-" * 100)

# Display the award amount and outlays for every record.
for row in rows:
    award_id = row.get("Award ID")
    recipient = row.get("Recipient Name")
    award_amount = row.get("Award Amount")
    total_outlays = row.get("Total Outlays")

    print(f"Award ID: {award_id}")
    print(f"Recipient: {recipient}")
    print(f"Award Amount: ${award_amount:,.2f}")
    print(f"Total Outlays: ${total_outlays:,.2f}")
    print("-" * 100)
