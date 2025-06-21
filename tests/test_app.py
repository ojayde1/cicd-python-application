# tests/test_app.py
import pytest
from unittest.mock import patch, MagicMock
from app import app, get_exchange_rate

# --- Fixture for Flask Test Client ---
@pytest.fixture
def client():
    """Configures the Flask app for testing and provides a test client."""
    app.config['TESTING'] = True # Enable Flask's testing mode
    with app.test_client() as client:
        yield client # Provide the client to the test functions

# --- Test Cases for Web Routes ---

def test_index_route_success(client):
    """
    Tests the '/' route to ensure it displays exchange rates correctly
    when the API call is successful.
    """
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "success",
            "rates": {"NGN": 1500.0}, # Example NGN rate
            "time_last_update_utc": "Thu, 01 Jan 2025 00:00:00 +0000"
        }
        mock_get.return_value = mock_response

        response = client.get('/')

        assert response.status_code == 200
        assert b"Current Exchange Rates" in response.data
        assert b"1 NGN = 0.000667 USD" in response.data # 1/1500 = 0.0006666...
        assert b"1 USD = 1500.00 NGN" in response.data
        assert b"Last Updated:" in response.data
        assert b"Current Time:" in response.data
        mock_get.assert_called_once_with('https://open.er-api.com/v6/latest/USD') # Verify API was called

def test_index_route_api_error(client):
    """
    Tests the '/' route to ensure it displays an error message correctly
    when the API call fails or returns an error status.
    """
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 500 # Simulate an API server error
        mock_response.json.return_value = {"result": "error", "error-type": "internal-error"}
        mock_get.return_value = mock_response

        response = client.get('/')

        assert response.status_code == 200
        # --- CORRECTED ASSERTION HERE ---
        assert b"API Error: internal-error" in response.data # Removed "Error: " prefix
        mock_get.assert_called_once_with('https://open.er-api.com/v6/latest/USD')

def test_index_route_request_exception(client):
    """
    Tests the '/' route to ensure it displays an error message correctly
    when the network request fails (e.g., no internet connection).
    """
    from requests.exceptions import RequestException
    with patch('requests.get', side_effect=RequestException("Network unreachable")) as mock_get:
        response = client.get('/')

        assert response.status_code == 200
        # --- CORRECTED ASSERTION HERE ---
        assert b"Request failed: Network unreachable" in response.data # Removed "Error: " prefix
        mock_get.assert_called_once_with('https://open.er-api.com/v6/latest/USD')

def test_health_check_route(client):
    """
    Tests the new '/health' endpoint.
    """
    response = client.get('/health')
    assert response.status_code == 200
    assert response.data == b"OK"


# --- Test Cases for get_exchange_rate function ---

def test_get_exchange_rate_success():
    """
    Tests the get_exchange_rate function directly for a successful API response.
    """
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "success",
            "rates": {"NGN": 1000.0}, # Example NGN rate
            "time_last_update_utc": "Fri, 02 Jan 2026 12:30:00 +0000"
        }
        mock_get.return_value = mock_response

        result = get_exchange_rate()

        assert 'error' not in result
        assert result['ngn_to_usd'] == 0.001 # 1/1000
        assert result['usd_to_ngn'] == 1000.0
        assert result['last_updated'] == "Fri, 02 Jan 2026 12:30:00 +0000"
        # We can't perfectly predict current_time, so we'll just check its presence
        assert 'current_time' in result
        mock_get.assert_called_once_with('https://open.er-api.com/v6/latest/USD')

def test_get_exchange_rate_ngn_not_found():
    """
    Tests get_exchange_rate when NGN rate is missing from API response.
    """
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "success",
            "rates": {"EUR": 0.9}, # NGN is missing
            "time_last_update_utc": "..."
        }
        mock_get.return_value = mock_response

        result = get_exchange_rate()
        assert 'error' in result
        assert result['error'] == 'NGN rate not found in the response'

def test_get_exchange_rate_api_fail_status_code():
    """
    Tests get_exchange_rate when API returns a non-200 status code.
    """
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 403 # Forbidden
        mock_response.json.return_value = {"result": "error", "error-type": "forbidden"}
        mock_get.return_value = mock_response

        result = get_exchange_rate()
        assert 'error' in result
        assert result['error'] == 'API Error: forbidden'

def test_get_exchange_rate_network_failure():
    """
    Tests get_exchange_rate when a network exception occurs.
    """
    from requests.exceptions import RequestException
    with patch('requests.get', side_effect=RequestException("Connection refused")) as mock_get:
        result = get_exchange_rate()
        assert 'error' in result
        assert result['error'] == 'Request failed: Connection refused' 
