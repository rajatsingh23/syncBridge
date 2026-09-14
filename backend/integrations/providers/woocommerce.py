import requests
from requests.exceptions import ConnectionError, Timeout

from integrations.providers.errors import (
    AuthenticationError,
    NotFoundError,
    ProviderRequestError,
    RateLimitError,
    TemporaryProviderError,
)


class WooCommerceClient:
    def __init__(
        self,
        store_url,
        consumer_key,
        consumer_secret,
        connect_timeout=3,
        read_timeout=10,
    ):
        self.store_url = store_url.rstrip("/")
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.timeout = (connect_timeout, read_timeout)

    def _build_url(self, path):
        return f"{self.store_url}/wp-json/wc/v3{path}"

    def _handle_response(self, response):
        if response.status_code in (401, 403):
            raise AuthenticationError(
                "WooCommerce authentication failed.",
                provider="woocommerce",
                status_code=response.status_code,
            )

        if response.status_code == 404:
            raise NotFoundError(
                "WooCommerce resource was not found.",
                provider="woocommerce",
                status_code=404,
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")

            raise RateLimitError(
                "WooCommerce rate limit exceeded.",
                retry_after=retry_after,
                provider="woocommerce",
                status_code=429,
            )

        if 400 <= response.status_code < 500:
            raise ProviderRequestError(
                f"WooCommerce request failed: {response.status_code}",
                provider="woocommerce",
                status_code=response.status_code,
            )

        if 500 <= response.status_code < 600:
            raise TemporaryProviderError(
                f"WooCommerce server error: {response.status_code}",
                provider="woocommerce",
                status_code=response.status_code,
            )

        return response

    def get(self, path, **kwargs):
        try:
            response = requests.get(
                self._build_url(path),
                auth=(self.consumer_key, self.consumer_secret),
                timeout=self.timeout,
                **kwargs,
            )
        except (ConnectionError, Timeout) as error:
            raise TemporaryProviderError(
                "WooCommerce request failed due to a network error.",
                provider="woocommerce",
            ) from error

        return self._handle_response(response)

    def post(self, path, **kwargs):
        try:
            response = requests.post(
                self._build_url(path),
                auth=(self.consumer_key, self.consumer_secret),
                timeout=self.timeout,
                **kwargs,
            )
        except (ConnectionError, Timeout) as error:
            raise TemporaryProviderError(
                "WooCommerce request failed due to a network error.",
                provider="woocommerce",
            ) from error

        return self._handle_response(response)

    def put(self, path, **kwargs):
        try:
            response = requests.put(
                self._build_url(path),
                auth=(self.consumer_key, self.consumer_secret),
                timeout=self.timeout,
                **kwargs,
            )
        except (ConnectionError, Timeout) as error:
            raise TemporaryProviderError(
                "WooCommerce request failed due to a network error.",
                provider="woocommerce",
            ) from error

        return self._handle_response(response)