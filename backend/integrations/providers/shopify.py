import requests
from integrations.providers.errors import AuthenticationError, NotFoundError, RateLimitError, TemporaryProviderError, ProviderRequestError
from requests.exceptions import ConnectionError, Timeout

class ShopifyClient:
    def __init__(self, shop_domain, access_token):
        self.base_url = f"https://{shop_domain}"
        self.access_token = access_token

    def get(self, path):
        try:
            response = requests.get(
                f"{self.base_url}{path}",
                headers={
                    "X-Shopify-Access-Token": self.access_token,
                },
                timeout=(3, 10),
            )
        except (ConnectionError, Timeout) as error:
            raise TemporaryProviderError(
                "Shopify connection failed."
            ) from error
        match response.status_code:
            case 401:
                raise AuthenticationError("Shopify authentication failed.")
            case 404:
                raise NotFoundError("Shopify resource was not found")
            case 429:
                retry_after = response.headers.get("Retry-After")

                if retry_after is not None:
                    try:
                        retry_after = int(retry_after)
                    except (TypeError, ValueError):
                        retry_after = None

                raise RateLimitError(
                    "Shopify rate limit exceeded.",
                    retry_after=retry_after,
                )
            case 500 | 501 | 502 | 503 | 504:
                raise TemporaryProviderError(
                    f"Shopify server error: {response.status_code}"
                )
            case status if 400 <= status < 500:
                raise ProviderRequestError(
                    f"Shopify request failed: {status}"
                )
        return response