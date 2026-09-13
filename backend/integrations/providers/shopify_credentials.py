import requests
from datetime import timedelta

from django.utils import timezone
from requests.exceptions import ConnectionError, Timeout

from integrations.providers.errors import AuthenticationError, TemporaryProviderError, ProviderRequestError

class ShopifyCredentials:
    def __init__(
        self,
        shop_domain,
        access_token,
        refresh_token=None,
        access_token_expires_at=None,
        refresh_token_expires_at=None,
    ):
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.access_token_expires_at = access_token_expires_at
        self.refresh_token_expires_at = refresh_token_expires_at

    def is_access_token_expired(self):
        if self.access_token_expires_at is None:
            return False

        return timezone.now() >= self.access_token_expires_at

    def refresh_access_token(self, client_id, client_secret):
        try:
            response = requests.post(
                f"https://{self.shop_domain}/admin/oauth/access_token",
                json={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                },
            )
        except (ConnectionError, Timeout) as error:
            raise TemporaryProviderError(
                "Shopify token refresh failed."
            ) from error

        if response.status_code == 401:
            raise AuthenticationError("Shopify token refresh authentication failed.")

        if 400 <= response.status_code < 500:
            raise ProviderRequestError(
                f"Shopify token refresh failed: {response.status_code}"
            )

        if 500 <= response.status_code < 600:
            raise TemporaryProviderError(
                f"Shopify token refresh failed: {response.status_code}"
            )
        response.raise_for_status()

        data = response.json()

        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

        now = timezone.now()

        self.access_token_expires_at = (
            now + timedelta(seconds=data["expires_in"])
        )

        self.refresh_token_expires_at = (
            now + timedelta(seconds=data["refresh_token_expires_in"])
        )

