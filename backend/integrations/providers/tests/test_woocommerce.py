from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from requests.exceptions import ConnectionError, Timeout

from integrations.providers.errors import (
    AuthenticationError,
    NotFoundError,
    ProviderRequestError,
    RateLimitError,
    TemporaryProviderError,
)
from integrations.providers.woocommerce import WooCommerceClient
from integrations.providers.woocommerce_credentials import WooCommerceCredentials

class WooCommerceClientTests(SimpleTestCase):

    def setUp(self):
        self.client = WooCommerceClient(
            store_url="https://example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

    @patch("integrations.providers.woocommerce.requests.get")
    def test_get_sends_auth_and_timeout(self, mock_get):
        response = Mock()
        response.status_code = 200
        mock_get.return_value = response

        result = self.client.get("/products")

        self.assertIs(result, response)

        mock_get.assert_called_once_with(
            "https://example.com/wp-json/wc/v3/products",
            auth=("ck_test", "cs_test"),
            timeout=(3, 10),
        )

    @patch("integrations.providers.woocommerce.requests.get")
    def test_custom_timeout_is_used(self, mock_get):
        client = WooCommerceClient(
            store_url="https://example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
            connect_timeout=5,
            read_timeout=20,
        )

        response = Mock()
        response.status_code = 200
        mock_get.return_value = response

        client.get("/products")

        mock_get.assert_called_once_with(
            "https://example.com/wp-json/wc/v3/products",
            auth=("ck_test", "cs_test"),
            timeout=(5, 20),
        )

    @patch("integrations.providers.woocommerce.requests.get")
    def test_401_raises_authentication_error(self, mock_get):
        response = Mock()
        response.status_code = 401
        mock_get.return_value = response

        with self.assertRaises(AuthenticationError):
            self.client.get("/products")

    @patch("integrations.providers.woocommerce.requests.get")
    def test_403_raises_authentication_error(self, mock_get):
        response = Mock()
        response.status_code = 403
        mock_get.return_value = response

        with self.assertRaises(AuthenticationError):
            self.client.get("/products")

    @patch("integrations.providers.woocommerce.requests.get")
    def test_404_raises_not_found_error(self, mock_get):
        response = Mock()
        response.status_code = 404
        mock_get.return_value = response

        with self.assertRaises(NotFoundError):
            self.client.get("/products")

    @patch("integrations.providers.woocommerce.requests.get")
    def test_429_raises_rate_limit_error(self, mock_get):
        response = Mock()
        response.status_code = 429
        response.headers = {"Retry-After": "30"}
        mock_get.return_value = response

        with self.assertRaises(RateLimitError) as context:
            self.client.get("/products")

        self.assertEqual(context.exception.retry_after, "30")

    @patch("integrations.providers.woocommerce.requests.get")
    def test_400_raises_provider_request_error(self, mock_get):
        response = Mock()
        response.status_code = 400
        mock_get.return_value = response

        with self.assertRaises(ProviderRequestError):
            self.client.get("/products")

    @patch("integrations.providers.woocommerce.requests.get")
    def test_500_raises_temporary_provider_error(self, mock_get):
        response = Mock()
        response.status_code = 500
        mock_get.return_value = response

        with self.assertRaises(TemporaryProviderError):
            self.client.get("/products")

    @patch("integrations.providers.woocommerce.requests.get")
    def test_connection_error_raises_temporary_provider_error(self, mock_get):
        mock_get.side_effect = ConnectionError()

        with self.assertRaises(TemporaryProviderError):
            self.client.get("/products")

    @patch("integrations.providers.woocommerce.requests.get")
    def test_timeout_raises_temporary_provider_error(self, mock_get):
        mock_get.side_effect = Timeout()

        with self.assertRaises(TemporaryProviderError):
            self.client.get("/products")

    @patch("integrations.providers.woocommerce.requests.post")
    def test_post_uses_same_auth_and_url(self, mock_post):
        response = Mock()
        response.status_code = 200
        mock_post.return_value = response

        self.client.post(
            "/products",
            json={"name": "Test Product"},
        )

        mock_post.assert_called_once_with(
            "https://example.com/wp-json/wc/v3/products",
            auth=("ck_test", "cs_test"),
            timeout=(3, 10),
            json={"name": "Test Product"},
        )

    @patch("integrations.providers.woocommerce.requests.put")
    def test_put_uses_same_auth_and_url(self, mock_put):
        response = Mock()
        response.status_code = 200
        mock_put.return_value = response

        self.client.put(
            "/products/123",
            json={"name": "Updated Product"},
        )

        mock_put.assert_called_once_with(
            "https://example.com/wp-json/wc/v3/products/123",
            auth=("ck_test", "cs_test"),
            timeout=(3, 10),
            json={"name": "Updated Product"},
        )

class WooCommerceCredentialsTests(SimpleTestCase):
    def test_valid_credentials(self):
        credentials = WooCommerceCredentials(
            store_url="https://example.com/",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        self.assertTrue(credentials.validate())
        self.assertEqual(credentials.store_url, "https://example.com")
        self.assertEqual(credentials.consumer_key, "ck_test")
        self.assertEqual(credentials.consumer_secret, "cs_test")

    def test_empty_store_url_raises_error(self):
        credentials = WooCommerceCredentials(
            store_url="",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        with self.assertRaises(ValueError):
            credentials.validate()

    def test_empty_consumer_key_raises_error(self):
        credentials = WooCommerceCredentials(
            store_url="https://example.com",
            consumer_key="",
            consumer_secret="cs_test",
        )

        with self.assertRaises(ValueError):
            credentials.validate()

    def test_empty_consumer_secret_raises_error(self):
        credentials = WooCommerceCredentials(
            store_url="https://example.com",
            consumer_key="ck_test",
            consumer_secret="",
        )

        with self.assertRaises(ValueError):
            credentials.validate()