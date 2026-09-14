from decimal import Decimal

from integrations.providers.schemas import NormalizedOrder


class ShopifyOrderAdapter:
    def __init__(self, client):
        self.client = client

    def get_orders(self):
        orders = []
        url = "/admin/api/orders.json"

        while url:
            response = self.client.get(url)
            data = response.json()

            for order in data.get("orders", []):
                customer = order.get("customer") or {}

                orders.append(
                    NormalizedOrder(
                        external_id=str(order["id"]),
                        customer_name=(
                            f'{customer.get("first_name", "")} '
                            f'{customer.get("last_name", "")}'
                        ).strip(),
                        status=order.get("financial_status", "pending"),
                        total_amount=Decimal(
                            str(order.get("current_total_price") or "0")
                        ),
                        currency=order.get("currency", "INR"),
                    )
                )

            url = data.get("next")

        return orders