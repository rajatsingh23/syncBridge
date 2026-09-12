
from django.test import SimpleTestCase
from unittest.mock import patch
from requests.exceptions import ConnectionError
from integrations.providers.shopify_oauth import ShopifyOAuth
from integrations.providers.errors import AuthenticationError, ProviderRequestError, TemporaryProviderError

class ShopifyOAuthTests(SimpleTestCase):
    def test_build_authorization_url(self):
        oauth = ShopifyOAuth(
            client_id="test-client-id",
            redirect_uri="http://localhost:8000/api/shopify/callback/",
            scopes=["read_products", "read_inventory"],
        )

        url = oauth.build_authorization_url(
            shop_domain="example.myshopify.com",
            state="test-state",
        )

        self.assertEqual(
            url,
            "https://example.myshopify.com/admin/oauth/authorize"
            "?client_id=test-client-id"
            "&scope=read_products%2Cread_inventory"
            "&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fshopify%2Fcallback%2F"
            "&state=test-state"
        )

    def test_build_authorization_url_with_multiple_scopes(self):
        oauth = ShopifyOAuth(
            client_id="test-client-id",
            redirect_uri="http://localhost:8000/api/shopify/callback/",
            scopes=[
                "read_products",
                "write_products",
                "read_inventory",
                "write_inventory",
            ],
        )

        url = oauth.build_authorization_url(
            shop_domain="example.myshopify.com",
            state="test-state",
        )

        self.assertIn(
            "scope=read_products%2Cwrite_products%2Cread_inventory%2Cwrite_inventory",
            url,
        )

    def test_generate_state(self):
        oauth = ShopifyOAuth(
            client_id="test-client-id",
            redirect_uri="http://localhost:8000/api/shopify/callback/",
            scopes=["read_products"],
        )

        state = oauth.generate_state()

        self.assertIsInstance(state, str)
        self.assertGreaterEqual(len(state), 32)

    def test_generate_state_returns_unique_values(self):
        oauth = ShopifyOAuth(
            client_id="test-client-id",
            redirect_uri="http://localhost:8000/api/shopify/callback/",
            scopes=["read_products"],
        )

        state_one = oauth.generate_state()
        state_two = oauth.generate_state()

        self.assertNotEqual(state_one, state_two)

    def test_validate_state_accepts_matching_state(self):
        oauth = ShopifyOAuth(
            client_id="test-client-id",
            redirect_uri="http://localhost:8000/api/shopify/callback/",
            scopes=["read_products"],
        )

        self.assertTrue(
            oauth.validate_state("expected-state", "expected-state")
        )


    def test_validate_state_rejects_mismatched_state(self):
        oauth = ShopifyOAuth(
            client_id="test-client-id",
            redirect_uri="http://localhost:8000/api/shopify/callback/",
            scopes=["read_products"],
        )

        self.assertFalse(
            oauth.validate_state("expected-state", "attacker-state")
        )

    @patch("integrations.providers.shopify_oauth.requests.post")
    def test_exchange_code_for_token(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "test-access-token",
            "scope": "read_products,read_inventory",
        }

        oauth = ShopifyOAuth(
            client_id="test-client-id",
            redirect_uri="http://localhost:8000/api/integrations/shopify/callback/",
            scopes=["read_products", "read_inventory"],
            client_secret="test-client-secret",
        )

        result = oauth.exchange_code(
            shop_domain="example.myshopify.com",
            code="test-code",
        )

        self.assertEqual(
            result["access_token"],
            "test-access-token",
        )

        mock_post.assert_called_once_with(
            "https://example.myshopify.com/admin/oauth/access_token",
            json={
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
                "code": "test-code",
            },
        )

    @patch("integrations.providers.shopify_oauth.requests.post")
    def test_exchange_code_raises_authentication_error_on_401(self, mock_post):
        mock_post.return_value.status_code = 401
        mock_post.return_value.json.return_value = {
            "errors": "Invalid client credentials"
        }

        oauth = ShopifyOAuth(
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:8000/api/integrations/shopify/callback/",
            scopes=["read_products"],
        )

        with self.assertRaises(AuthenticationError):
            oauth.exchange_code(
                shop_domain="example.myshopify.com",
                code="test-code",
            )

    @patch("integrations.providers.shopify_oauth.requests.post")
    def test_exchange_code_raises_provider_request_error_on_400(
        self,
        mock_post,
    ):
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {
            "errors": "Invalid authorization code"
        }

        oauth = ShopifyOAuth(
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:8000/api/integrations/shopify/callback/",
            scopes=["read_products"],
        )

        with self.assertRaises(ProviderRequestError):
            oauth.exchange_code(
                shop_domain="example.myshopify.com",
                code="invalid-code",
            )

    @patch("integrations.providers.shopify_oauth.requests.post")
    def test_exchange_code_raises_temporary_error_on_500(self, mock_post):
        mock_post.return_value.status_code = 500
        mock_post.return_value.json.return_value = {
            "errors": "Internal server error"
        }

        oauth = ShopifyOAuth(
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:8000/api/integrations/shopify/callback/",
            scopes=["read_products"],
        )

        with self.assertRaises(TemporaryProviderError):
            oauth.exchange_code(
                shop_domain="example.myshopify.com",
                code="test-code",
            )

    @patch("integrations.providers.shopify_oauth.requests.post")
    def test_exchange_code_raises_temporary_error_on_connection_error(
        self,
        mock_post,
    ):
        mock_post.side_effect = ConnectionError("Connection failed")

        oauth = ShopifyOAuth(
            client_id="test-client-id",
            client_secret="test-client-secret",
            redirect_uri="http://localhost:8000/api/integrations/shopify/callback/",
            scopes=["read_products"],
        )

        with self.assertRaises(TemporaryProviderError):
            oauth.exchange_code(
                shop_domain="example.myshopify.com",
                code="test-code",
            )