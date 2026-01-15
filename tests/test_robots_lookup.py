import pytest
from unittest.mock import MagicMock, patch
from src.scanner.robots_lookup import RobotsLookup

def test_get_robots_txt_success():
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *"
        mock_get.return_value = mock_response

        content = RobotsLookup.get_robots_txt("example.com")
        assert content == "User-agent: *"
        mock_get.assert_called_with("http://example.com/robots.txt", timeout=5)

def test_get_robots_txt_error():
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        content = RobotsLookup.get_robots_txt("example.com")
        assert "Error: Received status code 404" in content

def test_get_robots_txt_exception():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection failed")

        content = RobotsLookup.get_robots_txt("example.com")
        assert "Error fetching robots.txt: Connection failed" in content
