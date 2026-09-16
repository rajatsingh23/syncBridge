from datetime import datetime
from decimal import Decimal

from integrations.providers.schemas import (
    NormalizedOrder,
    NormalizedOrderItem,
)


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
                self._normalize_order(order)
                for order in data
            )

            if len(data) < self.per_page:
                break

            page += 1

        return orders

    def _normalize_order(self, order):
        billing = order.get("billing", {})

        items = [
            NormalizedOrderItem(
                external_variant_id=str(
                    item.get("variation_id") or item.get("product_id")
                ),
                sku=item.get("sku") or "",
                quantity=item.get("quantity") or 0,
                unit_price=Decimal(
                    str(item.get("price") or "0")
                ),
            )
            for item in order.get("line_items", [])
        ]

        ordered_at = datetime.fromisoformat(
            order["date_created"].replace("Z", "+00:00")
        )

        return NormalizedOrder(
            external_id=str(order["id"]),
            customer_name=(
                f'{billing.get("first_name", "")} '
                f'{billing.get("last_name", "")}'
            ).strip(),
            customer_email=billing.get("email") or "",
            status=order.get("status", "pending"),
            total_amount=Decimal(
                str(order.get("total") or "0")
            ),
            currency=order.get("currency", "INR"),
            ordered_at=ordered_at,
            items=items,
        )