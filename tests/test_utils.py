"""Tests for utils.py shared helpers."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock

from utils import fetch_arr_data


class TestFetchArrData:

    def _mock_response(self, json_data, status_code=200):
        mock = MagicMock()
        mock.json.return_value = json_data
        mock.status_code = status_code
        if status_code >= 400:
            mock.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
        else:
            mock.raise_for_status.return_value = None
        return mock

    def test_returns_json_response(self):
        payload = [{"id": 1, "name": "Test CF"}]
        with patch("requests.get", return_value=self._mock_response(payload)) as mock_get:
            result = fetch_arr_data("http://localhost:7878", "mykey", "customformat")
        assert result == payload

    def test_url_constructed_from_base_and_endpoint(self):
        with patch("requests.get", return_value=self._mock_response([])) as mock_get:
            fetch_arr_data("http://localhost:7878", "mykey", "qualityprofile")
        called_url = mock_get.call_args[0][0]
        assert called_url == "http://localhost:7878/api/v3/qualityprofile"

    def test_trailing_slash_in_base_url_stripped(self):
        with patch("requests.get", return_value=self._mock_response([])) as mock_get:
            fetch_arr_data("http://localhost:7878/", "mykey", "customformat")
        called_url = mock_get.call_args[0][0]
        assert called_url == "http://localhost:7878/api/v3/customformat"
        assert "//" not in called_url.split("://", 1)[1]

    def test_api_key_sent_as_header(self):
        with patch("requests.get", return_value=self._mock_response([])) as mock_get:
            fetch_arr_data("http://localhost:7878", "secret-key-123", "customformat")
        headers = mock_get.call_args[1]["headers"]
        assert headers["X-Api-Key"] == "secret-key-123"

    def test_timeout_is_set(self):
        with patch("requests.get", return_value=self._mock_response([])) as mock_get:
            fetch_arr_data("http://localhost:7878", "mykey", "customformat")
        assert mock_get.call_args[1]["timeout"] == 10

    def test_raises_on_http_error(self):
        error_response = self._mock_response([], status_code=401)
        with patch("requests.get", return_value=error_response):
            with pytest.raises(Exception):
                fetch_arr_data("http://localhost:7878", "badkey", "customformat")
