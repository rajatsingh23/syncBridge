from integrations.providers.schemas import NormalizedInventory


class WooCommerceInventoryAdapter:
    def __init__(self, client, per_page=100):
        self.client = client
        self.per_page = per_page

    def get_inventory(self):
        inventory = []
        product_page = 1

        while True:
            response = self.client.get(
                "/products",
                params={
                    "page": product_page,
                    "per_page": self.per_page,
                },
            )

            products = response.json()

            if not products:
                break

            for product in products:
                product_id = product["id"]
                variation_page = 1

                while True:
                    response = self.client.get(
                        f"/products/{product_id}/variations",
                        params={
                            "page": variation_page,
                            "per_page": self.per_page,
                        },
                    )

                    variations = response.json()

                    if not variations:
                        break

                    inventory.extend(
                        NormalizedInventory(
                            external_variant_id=str(
                                variation["id"]
                            ),
                            sku=variation.get("sku") or "",
                            quantity=(
                                variation.get("stock_quantity")
                                or 0
                            ),
                            reserved_quantity=0,
                        )
                        for variation in variations
                    )

                    if len(variations) < self.per_page:
                        break

                    variation_page += 1

            if len(products) < self.per_page:
                break

            product_page += 1

        return inventory