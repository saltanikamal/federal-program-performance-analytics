import pytest
from unittest.mock import Mock

from src.ingestion.usa_spending_api import fetch_awards


def test_fetch_awards_returns_results(monkeypatch):
    """Test that fetch_awards returns award records."""

    mock_results = [
        {
            "Award ID": "DEAC0494AL85000",
            "Recipient Name": "Lockheed Martin Corporation",
            "Award Amount": 1000000,
            "Total Outlays": 500000,
        }
    ]

    mock_response = Mock()
    mock_response.json.return_value = {
        "results": mock_results
    }

    mock_post = Mock(return_value=mock_response)

    monkeypatch.setattr(
        "src.ingestion.usa_spending_api.requests.post",
        mock_post
    )

    results = fetch_awards()

    assert results == mock_results
    mock_response.raise_for_status.assert_called_once()


def test_fetch_awards_uses_correct_api_request(monkeypatch):
    """Test that the correct API endpoint and payload are used."""

    mock_response = Mock()
    mock_response.json.return_value = {"results": []}

    mock_post = Mock(return_value=mock_response)

    monkeypatch.setattr(
        "src.ingestion.usa_spending_api.requests.post",
        mock_post
    )

    fetch_awards()

    mock_post.assert_called_once()

    args, kwargs = mock_post.call_args

    assert args[0] == (
        "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    )

    assert kwargs["timeout"] == 30

    payload = kwargs["json"]

    assert payload["limit"] == 10
    assert payload["page"] == 1
    assert payload["sort"] == "Award Amount"
    assert payload["order"] == "desc"

    assert payload["filters"]["award_type_codes"] == [
        "A", "B", "C", "D"
    ]


def test_fetch_awards_handles_http_error(monkeypatch):
    """Test that HTTP errors are properly propagated."""

    mock_response = Mock()

    mock_response.raise_for_status.side_effect = (
        __import__("requests").exceptions.HTTPError(
            "API request failed"
        )
    )

    mock_post = Mock(return_value=mock_response)

    monkeypatch.setattr(
        "src.ingestion.usa_spending_api.requests.post",
        mock_post
    )

    with pytest.raises(
        __import__("requests").exceptions.HTTPError
    ):
        fetch_awards()
