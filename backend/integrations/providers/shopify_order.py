from datetime import datetime
from decimal import Decimal

from integrations.providers.schemas import (
    NormalizedOrder,
    NormalizedOrderItem,
)


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
                orders.append(
                    self._normalize_order(order)
                )

            url = data.get("next")

        return orders

    def _normalize_order(self, order):
        customer = order.get("customer") or {}

        items = [
            NormalizedOrderItem(
                external_variant_id=str(
                    item.get("variant_id") or item.get("product_id")
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
            order["created_at"].replace("Z", "+00:00")
        )

        return NormalizedOrder(
            external_id=str(order["id"]),
            customer_name=(
                f'{customer.get("first_name", "")} '
                f'{customer.get("last_name", "")}'
            ).strip(),
            customer_email=customer.get("email") or "",
            status=order.get("financial_status", "pending"),
            total_amount=Decimal(
                str(order.get("current_total_price") or "0")
            ),
            currency=order.get("currency", "INR"),
            ordered_at=ordered_at,
            items=items,
        )