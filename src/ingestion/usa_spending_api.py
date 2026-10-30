import requests


def fetch_awards():
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

    payload = {
        "subawards": False,
        "filters": {
            "award_type_codes": ["A", "B", "C", "D"]
        },
        "fields": [
            "Award ID",
            "Recipient Name",
            "Award Amount",
            "Total Outlays",
            "Awarding Agency",
            "Start Date",
            "End Date",
            "Description",
        ],
        "limit": 10,
        "page": 1,
        "sort": "Award Amount",
        "order": "desc",
    }

    response = requests.post(
        url,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()
    return data["results"]
