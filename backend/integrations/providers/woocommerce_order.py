from decimal import Decimal

from integrations.providers.schemas import NormalizedOrder


class WooCommerceOrderAdapter:
    def __init__(self, client, per_page=100):
        self.client = client
        self.per_page = per_page

    def get_orders(self):
        orders = []
        page = 1

        while True:
            response = self.client.get(
                "/orders",
                params={
                    "page": page,
                    "per_page": self.per_page,
                },
            )

            data = response.json()

            if not data:
                break

            orders.extend(
                NormalizedOrder(
                    external_id=str(order["id"]),
                    customer_name=(
                        f'{order.get("billing", {}).get("first_name", "")} '
                        f'{order.get("billing", {}).get("last_name", "")}'
                    ).strip(),
                    status=order.get("status", "pending"),
                    total_amount=Decimal(
                        str(order.get("total") or "0")
                    ),
                    currency=order.get("currency", "INR"),
                )
                for order in data
            )

            if len(data) < self.per_page:
                break

            page += 1

        return orders