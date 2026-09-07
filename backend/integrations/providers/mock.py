import requests

from .base import BaseProvider
from .schemas import NormalizedProduct, NormalizedVariant


class MockProvider(BaseProvider):
    def __init__(self, store):
        self.store = store
        self.base_url = "http://127.0.0.1:8000/api/mock-store"

    def get_products(self):
        response = requests.get(
            f"{self.base_url}/products/",
            timeout=10,
        )
        response.raise_for_status()
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
        response = requests.get(
            f"{self.base_url}/inventory/",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def get_orders(self):
        response = requests.get(
            f"{self.base_url}/orders/",
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def update_inventory(self, external_variant_id, quantity):
        response = requests.patch(
            f"{self.base_url}/inventory/{external_variant_id}/",
            json={"quantity": quantity},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()