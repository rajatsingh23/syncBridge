from unittest.mock import patch

from django.test import SimpleTestCase

from integrations.providers.shopify import ShopifyClient

from integrations.providers.errors import AuthenticationError, NotFoundError, RateLimitError, TemporaryProviderError, ProviderRequestError
from integrations.retry import retry_call
from requests.exceptions import ConnectionError, Timeout

class ShopifyClientTests(SimpleTestCase):
    @patch("integrations.providers.shopify.requests.get")
    def test_get_sends_shopify_access_token(self, mock_get):
        mock_get.return_value.status_code = 200

        client = ShopifyClient(
            shop_domain="example.myshopify.com",
            access_token="test-token",
        )

        client.get("/admin/api/2026-07/products.json")

        mock_get.assert_called_once_with(
            "https://example.myshopify.com/admin/api/2026-07/products.json",
            headers={
                "X-Shopify-Access-Token": "test-token",
            },
            timeout=(3, 10),
        )
    @patch("integrations.providers.shopify.requests.get")
    def test_get_raises_authentication_error_on_401(self, mock_get):
        mock_get.return_value.status_code = 401

        client = ShopifyClient(
            shop_domain="example.myshopify.com",
            access_token="test-token",
        )

        with self.assertRaises(AuthenticationError):
            client.get("/admin/api/2026-07/products.json")

    @patch("integrations.providers.shopify.requests.get")
    def test_get_raises_not_found_error_on_404(self, mock_get):
        mock_get.return_value.status_code = 404

        client = ShopifyClient(
            shop_domain="example.myshopify.com",
            access_token="test-token",
        )

        with self.assertRaises(NotFoundError):
            client.get("/admin/api/2026-07/products.json")

    @patch("integrations.providers.shopify.requests.get")
    def test_get_raises_rate_limit_error_on_429(self, mock_get):
        mock_get.return_value.status_code = 429
        mock_get.return_value.headers = {
            "Retry-After": "5",
        }

        client = ShopifyClient(
            shop_domain="example.myshopify.com",
            access_token="test-token",
        )

        with self.assertRaises(RateLimitError) as context:
            client.get("/admin/api/2026-07/products.json")

        self.assertEqual(context.exception.retry_after, 5)

    @patch("integrations.providers.shopify.requests.get")
    def test_get_handles_invalid_retry_after_header(self, mock_get):
        mock_get.return_value.status_code = 429
        mock_get.return_value.headers = {
            "Retry-After": "abc",
        }

        client = ShopifyClient(
            shop_domain="example.myshopify.com",
            access_token="test-token",
        )

        with self.assertRaises(RateLimitError) as context:
            client.get("/admin/api/2026-07/products.json")

        self.assertIsNone(context.exception.retry_after)

    @patch("integrations.providers.shopify.requests.get")
    def test_get_raises_temporary_provider_error_on_500(self, mock_get):
        mock_get.return_value.status_code = 500

        client = ShopifyClient(
            shop_domain="example.myshopify.com",
            access_token="test-token",
        )

        with self.assertRaises(TemporaryProviderError):
            client.get("/admin/api/2026-07/products.json")

    @patch("integrations.providers.shopify.requests.get")
    def test_get_raises_provider_request_error_on_400(self, mock_get):
        mock_get.return_value.status_code = 400

        client = ShopifyClient(
            shop_domain="example.myshopify.com",
            access_token="test-token",
        )

        with self.assertRaises(ProviderRequestError):
            client.get("/admin/api/2026-07/products.json")

    @patch("integrations.providers.shopify.requests.get")
    def test_get_raises_provider_request_error_on_other_4xx(
        self,
        mock_get,
    ):
        mock_get.return_value.status_code = 418

        client = ShopifyClient(
            shop_domain="example.myshopify.com",
            access_token="test-token",
        )

        with self.assertRaises(ProviderRequestError):
            client.get("/admin/api/2026-07/products.json")

    @patch("integrations.providers.shopify.requests.get")
    def test_get_raises_temporary_provider_error_on_connection_error(
        self,
        mock_get,
    ):
        mock_get.side_effect = ConnectionError("Connection failed")

        client = ShopifyClient(
            shop_domain="example.myshopify.com",
            access_token="test-token",
        )

        with self.assertRaises(TemporaryProviderError):
            client.get("/admin/api/2026-07/products.json")

    @patch("integrations.providers.shopify.requests.get")
    def test_get_raises_temporary_provider_error_on_timeout(
        self,
        mock_get,
    ):
        mock_get.side_effect = Timeout("Request timed out")

        client = ShopifyClient(
            shop_domain="example.myshopify.com",
            access_token="test-token",
        )

        with self.assertRaises(TemporaryProviderError):
            client.get("/admin/api/2026-07/products.json")

    @patch("integrations.providers.shopify.requests.get")
    def test_get_can_be_retried_after_temporary_failure(self, mock_get):
        mock_get.side_effect = [
            Timeout("Request timed out"),
            Timeout("Request timed out"),
            type("Response", (), {"status_code": 200})(),
        ]

        client = ShopifyClient(
            shop_domain="example.myshopify.com",
            access_token="test-token",
        )

        response = retry_call(
            lambda: client.get("/admin/api/2026-07/products.json"),
            max_retries=2,
            base_delay=0,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_get.call_count, 3)

    @patch("integrations.providers.shopify.requests.get")
    @patch("integrations.retry.time.sleep")
    def test_get_can_be_retried_after_rate_limit(
        self,
        mock_sleep,
        mock_get,
    ):
        first_response = type(
            "Response",
            (),
            {
                "status_code": 429,
                "headers": {"Retry-After": "5"},
            },
        )()

        second_response = type(
            "Response",
            (),
            {
                "status_code": 200,
                "headers": {},
            },
        )()

        mock_get.side_effect = [first_response, second_response]

        client = ShopifyClient(
            shop_domain="example.myshopify.com",
            access_token="test-token",
        )

        response = retry_call(
            lambda: client.get("/admin/api/2026-07/products.json"),
            max_retries=1,
        )

        self.assertEqual(response.status_code, 200)
        mock_sleep.assert_called_once_with(5)
        self.assertEqual(mock_get.call_count, 2)
            