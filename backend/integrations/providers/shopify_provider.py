from integrations.providers.shopify import ShopifyClient
from integrations.providers.shopify_product import ShopifyProductAdapter
from integrations.providers.shopify_inventory import ShopifyInventoryAdapter
from integrations.providers.shopify_order import ShopifyOrderAdapter

class ShopifyProvider:
    def __init__(self, store):
        self.store = store

        credentials = store.credentials

        self.client = ShopifyClient(
            shop_domain=credentials["shop_domain"],
            access_token=credentials["access_token"],
        )

        self.product_adapter = ShopifyProductAdapter(self.client)
        self.inventory_adapter =  ShopifyInventoryAdapter(self.client)
        self.order_adapter = ShopifyOrderAdapter(self.client)

    def get_products(self):
        return self.product_adapter.get_products()
    
    def get_inventory(self):
        return self.inventory_adapter.get_inventory()
    
    def get_orders(self):
        return self.order_adapter.get_orders()

    def update_inventory(self, external_variant_id, quantity):
        return self.client.put(
            "/admin/api/inventory_levels.json",
            json={
                "inventory_item_id": external_variant_id,
                "available": quantity,
            },
        )