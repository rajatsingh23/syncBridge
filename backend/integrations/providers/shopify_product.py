from decimal import Decimal

from integrations.providers.schemas import (
    NormalizedProduct,
    NormalizedVariant,
)


class ShopifyProductAdapter:
    def __init__(self, client):
        self.client = client

    def get_products(self):
        products = []
        url = "/admin/api/products.json"

        while url:
            response = self.client.get(url)
            data = response.json()

            products.extend(
                NormalizedProduct(
                    external_id=str(product["id"]),
                    title=product["title"],
                    description=product.get("body_html") or "",
                    variants=[
                        NormalizedVariant(
                            external_id=str(variant["id"]),
                            sku=variant.get("sku") or "",
                            price=Decimal(str(variant["price"])),
                            currency="INR",
                        )
                        for variant in product.get("variants", [])
                    ],
                )
                for product in data.get("products", [])
            )

            url = data.get("next")

        return products