from integrations.providers.schemas import NormalizedInventory


class ShopifyInventoryAdapter:
    def __init__(self, client):
        self.client = client

    def get_inventory(self):
        inventory = []
        url = "/admin/api/inventory_levels.json"

        while url:
            response = self.client.get(url)
            data = response.json()

            inventory.extend(
                NormalizedInventory(
                    external_variant_id=str(item["inventory_item_id"]),
                    sku="",
                    quantity=item.get("available") or 0,
                    reserved_quantity=0,
                )
                for item in data.get("inventory_levels", [])
            )

            url = data.get("next")

        return inventory