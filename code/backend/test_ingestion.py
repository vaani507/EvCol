from unittest.mock import Mock, patch

from ingestion import fetch_holidays_for_country


@patch("ingestion.httpx.Client")
def test_fetch_holidays_returns_empty_for_no_content(mock_client):
    response = Mock(status_code=204)
    mock_client.return_value.__enter__.return_value.get.return_value = response

    assert fetch_holidays_for_country("IN", 2026) == []

    response.json.assert_not_called()
