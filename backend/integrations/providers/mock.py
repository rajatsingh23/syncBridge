import requests

from .base import BaseProvider


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
        return response.json()

    def get_inventory(self):
        response = requests.get(
            f"{self.base_url}/inventory/",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def get_orders(self):
        return []

    def update_inventory(self, external_variant_id, quantity):
        return {
            "external_variant_id": external_variant_id,
            "quantity": quantity,
        }