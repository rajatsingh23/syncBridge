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
        response = self.client.get(
            f"{self.base_url}/products/",
        )
        if not response.ok:
            self._handle_response_error(response)
        products = response.json()

        return [
            NormalizedProduct(
                external_id=product["external_id"],
                title=product["title"],
                description=product["description"],
                variants=[
                    NormalizedVariant(
                        external_id=variant["external_id"],
                        sku=variant["sku"],
                        price=variant["price"],
                        currency=variant["currency"],
                    )
                    for variant in product["variants"]
                ],
            )
            for product in products
        ]

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
            raise RateLimitError("Provider rate limit exceeded")

        if response.status_code >= 500:
            raise TemporaryProviderError(
                f"Provider server error: {response.status_code}"
            )

        if response.status_code >= 400:
            raise ProviderRequestError(
                f"Provider request failed: {response.status_code}"
            )