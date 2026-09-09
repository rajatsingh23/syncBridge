from integrations.http_client import HTTPClient
from decimal import Decimal
from .base import BaseProvider
from .schemas import NormalizedProduct, NormalizedVariant, NormalizedInventory, NormalizedOrder
from .errors import (
    AuthenticationError,
    NotFoundError,
    ProviderRequestError,
    RateLimitError,
    TemporaryProviderError,
)


class MockProvider(BaseProvider):
    def __init__(self, store):
        self.store = store
        self.base_url = "http://127.0.0.1:8000/api/mock-store"
        self.client = HTTPClient()

    def get_products(self):
        products = []
        url = f"{self.base_url}/products/"
        while url:
            response = self.client.get(url)
            self._handle_response_error(response)

            data = response.json()

            # Paginated response
            if isinstance(data, dict):
                page_products = data.get("results", [])
                url = data.get("next")
            else:
                # Backward compatibility with non-paginated response
                page_products = data
                url = None

            products.extend(
                NormalizedProduct(
                    external_id=product["external_id"],
                    title=product["title"],
                    description=product.get("description", ""),
                    variants=[
                        NormalizedVariant(
                            external_id=variant["external_id"],
                            sku=variant["sku"],
                            price=Decimal(str(variant["price"])),
                            currency=variant.get("variants", [])
                        )
                        for variant in product.get("variants", [])
                    ],
                )
                for product in page_products
            )
        return products

    def get_inventory(self):
        response = self.client.get(
            f"{self.base_url}/inventory/",
        )
        if not response.ok:
            self._handle_response_error(response)

        inventory_items = response.json()

        return [
            NormalizedInventory(
                external_variant_id=item["external_variant_id"],
                sku=item["sku"],
                quantity=item["quantity"],
                reserved_quantity=item["reserved_quantity"],
            )
            for item in inventory_items
        ]

    def get_orders(self):
        response = self.client.get(
            f"{self.base_url}/orders/",
        )
        if not response.ok:
            self._handle_response_error(response)

        orders = response.json()

        return [
            NormalizedOrder(
                external_id=order["external_id"],
                customer_name=order["customer_name"],
                status=order["status"],
                total_amount=Decimal(order["total_amount"]),
                currency=order["currency"],
            )
            for order in orders
        ]

    def update_inventory(self, external_variant_id, quantity):
        response = self.client.patch(
            f"{self.base_url}/inventory/{external_variant_id}/",
            json={"quantity": quantity},
            timeout=10,
        )
        if not response.ok:
            self._handle_response_error(response)
        return response.json()

    def _handle_response_error(self, response):
        if response.status_code == 401:
            raise AuthenticationError("Provider authentication failed.")

        if response.status_code == 404:
            raise NotFoundError("Provider resource was not found.")

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")

            if retry_after is not None:
                try:
                    retry_after = int(retry_after)
                except(TypeError, ValueError):
                    retry_after = None
                    
            raise RateLimitError(
                "Provider rate limit exceeded",
                retry_after=retry_after,
                )

        if response.status_code >= 500:
            raise TemporaryProviderError(
                f"Provider server error: {response.status_code}"
            )

        if response.status_code >= 400:
            raise ProviderRequestError(
                f"Provider request failed: {response.status_code}"
            )