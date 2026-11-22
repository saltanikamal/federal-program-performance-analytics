import requests
from urllib.parse import quote

from src.ingestion.usa_spending_api import fetch_awards


# 1. Retrieve the award from the search API.
rows = fetch_awards()

target = next(
    row for row in rows
    if row.get("Award ID") == "N0002417C2100"
)

# 2. Extract the generated identifier.
generated_id = target["generated_internal_id"]

print("Award ID:", target["Award ID"])
print("Generated identifier:", generated_id)

# 3. Request the detailed award record.
encoded_id = quote(generated_id, safe="")

url = f"https://api.usaspending.gov/api/v2/awards/{encoded_id}/"

response = requests.get(url, timeout=30)

print("\nHTTP status:", response.status_code)

if response.ok:
    data = response.json()

    print("\nDetailed award response:")
    for key, value in data.items():
        print(f"{key}: {value}")
else:
    print("\nThe detail request did not succeed.")
    print("Response:", response.text[:1000])
