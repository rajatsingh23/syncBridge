from unittest.mock import patch

from django.test import SimpleTestCase

from integrations.http_client import HTTPClient


class HTTPClientTests(SimpleTestCase):

    @patch("integrations.http_client.requests.get")
    def test_get_uses_default_timeout(self, mock_get):
        HTTPClient().get("https://example.com")

        mock_get.assert_called_once_with(
            "https://example.com",
            timeout=10,
        )

    @patch("integrations.http_client.requests.get")
    def test_get_uses_custom_timeout(self, mock_get):
        client = HTTPClient(timeout=5)

        client.get("https://example.com")

        mock_get.assert_called_once_with(
            "https://example.com",
            timeout=5,
        )

    @patch("integrations.http_client.requests.patch")
    def test_patch_uses_timeout(self, mock_patch):
        client = HTTPClient(timeout=7)

        client.patch(
            "https://example.com",
            json={"quantity": 100},
        )

        mock_patch.assert_called_once_with(
            "https://example.com",
            timeout=7,
            json={"quantity": 100},
        )