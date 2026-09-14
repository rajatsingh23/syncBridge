from integrations.providers.woocommerce import WooCommerceClient
from integrations.providers.woocommerce_credentials import (
    WooCommerceCredentials,
)
from integrations.providers.woocommerce_product import (
    WooCommerceProductAdapter,
)
from integrations.providers.woocommerce_inventory import (
    WooCommerceInventoryAdapter,
)
from integrations.providers.woocommerce_order import (
    WooCommerceOrderAdapter,
)


class WooCommerceProvider:
    def __init__(self, store):
        self.store = store

        credentials = WooCommerceCredentials(
            store_url=store.credentials["store_url"],
            consumer_key=store.credentials["consumer_key"],
            consumer_secret=store.credentials["consumer_secret"],
        )

        credentials.validate()

        self.client = WooCommerceClient(
            store_url=credentials.store_url,
            consumer_key=credentials.consumer_key,
            consumer_secret=credentials.consumer_secret,
        )

        self.product_adapter = WooCommerceProductAdapter(
            self.client
        )
        self.inventory_adapter = WooCommerceInventoryAdapter(
            self.client
        )
        self.order_adapter = WooCommerceOrderAdapter(
            self.client
        )

    def get_products(self):
        return self.product_adapter.get_products()

    def get_inventory(self):
        return self.inventory_adapter.get_inventory()

    def get_orders(self):
        return self.order_adapter.get_orders()

    def update_inventory(self, external_variant_id, quantity):
        return self.client.put(
            f"/products/variations/{external_variant_id}",
            json={
                "stock_quantity": quantity,
                "manage_stock": True,
            },
        )