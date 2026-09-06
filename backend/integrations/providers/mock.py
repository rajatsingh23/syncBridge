from .base import BaseProvider

class MockProvider(BaseProvider):
    def __init__(self, store):
        self.store = store
    def get_products(self):
        return []

    def get_inventory(self):
        return []

    def get_orders(self):
        return []

    def update_inventory(self, external_variant_id, quantity):
        return {
            "external_variant_id": external_variant_id,
            "quantity": quantity
        }