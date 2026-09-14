from decimal import Decimal

from integrations.providers.schemas import (
    NormalizedProduct,
    NormalizedVariant,
)


class WooCommerceProductAdapter:
    def __init__(self, client, per_page=100):
        self.client = client
        self.per_page = per_page

    def get_products(self):
        products = []
        page = 1

        while True:
            response = self.client.get(
                "/products",
                params={
                    "page": page,
                    "per_page": self.per_page,
                },
            )

            data = response.json()

            if not data:
                break

            for product in data:
                variants = self._get_variations(product["id"])

                products.append(
                    NormalizedProduct(
                        external_id=str(product["id"]),
                        title=product["name"],
                        description=product.get("description") or "",
                        variants=variants,
                    )
                )

            if len(data) < self.per_page:
                break

            page += 1

        return products

    def _get_variations(self, product_id):
        variants = []
        page = 1

        while True:
            response = self.client.get(
                f"/products/{product_id}/variations",
                params={
                    "page": page,
                    "per_page": self.per_page,
                },
            )

            data = response.json()

            if not data:
                break

            variants.extend(
                NormalizedVariant(
                    external_id=str(variation["id"]),
                    sku=variation.get("sku") or "",
                    price=Decimal(
                        str(variation.get("price") or "0")
                    ),
                    currency=variation.get("currency") or "INR",
                )
                for variation in data
            )

            if len(data) < self.per_page:
                break

            page += 1

        return variants