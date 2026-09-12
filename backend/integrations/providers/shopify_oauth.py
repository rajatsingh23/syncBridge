import requests
from urllib.parse import urlencode
from secrets import token_urlsafe, compare_digest
from integrations.providers.errors import AuthenticationError, ProviderRequestError, TemporaryProviderError
from requests.exceptions import ConnectionError, Timeout

class ShopifyOAuth:
    def __init__(self, client_id, redirect_uri, scopes, client_secret=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes

    def generate_state(self):
        return token_urlsafe(32)

    def validate_state(self, expected_state, received_state):
        return compare_digest(expected_state, received_state)
    
    def build_authorization_url(self, shop_domain, state):
        params = {
            "client_id": self.client_id,
            "scope": ",".join(self.scopes),
            "redirect_uri": self.redirect_uri,
            "state": state,
        }

        return (
            f"https://{shop_domain}/admin/oauth/authorize"
            f"?{urlencode(params)}"
        )

    def exchange_code(self, shop_domain, code):
        try:
            response = requests.post(
                f"https://{shop_domain}/admin/oauth/access_token",
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                },
            )
        except (ConnectionError, Timeout) as error:
            raise TemporaryProviderError(
                "Shopify token exchange failed."
            ) from error

        if response.status_code == 401:
            raise AuthenticationError("Shopify authentication failed.")

        if 400 <= response.status_code < 500:
            raise ProviderRequestError(
                f"Shopify token exchange failed: {response.status_code}"
            )

        if 500 <= response.status_code < 600:
            raise TemporaryProviderError(
                f"Shopify server error: {response.status_code}"
            )

        return response.json()