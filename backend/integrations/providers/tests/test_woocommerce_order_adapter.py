from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock

from django.test import SimpleTestCase

from integrations.providers.schemas import NormalizedOrderItem
from integrations.providers.woocommerce_order import WooCommerceOrderAdapter


class WooCommerceOrderAdapterTests(SimpleTestCase):

    def setUp(self):
        self.client = Mock()

        self.adapter = WooCommerceOrderAdapter(
            self.client,
            per_page=2,
        )

    def test_get_orders_maps_order(self):
        response = Mock()
        response.json.return_value = [
            {
                "id": 501,
                "date_created": "2026-09-16T10:30:00Z",
                "status": "processing",
                "total": "1299.50",
                "currency": "INR",
                "billing": {
                    "first_name": "Rajat",
                    "last_name": "Singh",
                    "email": "rajat@example.com",
                },
                "line_items": [
                    {
                        "product_id": 101,
                        "variation_id": 201,
                        "sku": "TSHIRT-BLK-M",
                        "quantity": 2,
                        "price": "499.00",
                    }
                ],
            }
        ]

        self.client.get.return_value = response

        orders = self.adapter.get_orders()

        self.assertEqual(len(orders), 1)

        order = orders[0]

        self.assertEqual(order.external_id, "501")
        self.assertEqual(order.customer_name, "Rajat Singh")
        self.assertEqual(order.customer_email, "rajat@example.com")
        self.assertEqual(order.status, "processing")
        self.assertEqual(order.total_amount, Decimal("1299.50"))
        self.assertEqual(order.currency, "INR")

        self.assertEqual(
            order.ordered_at,
            datetime.fromisoformat("2026-09-16T10:30:00+00:00"),
        )

        self.assertEqual(len(order.items), 1)

        item = order.items[0]

        self.assertEqual(
            item,
            NormalizedOrderItem(
                external_variant_id="201",
                sku="TSHIRT-BLK-M",
                quantity=2,
                unit_price=Decimal("499.00"),
            ),
        )

    def test_empty_response_returns_empty_list(self):
        response = Mock()
        response.json.return_value = []

        self.client.get.return_value = response

        orders = self.adapter.get_orders()

        self.assertEqual(orders, [])

        self.client.get.assert_called_once_with(
            "/orders",
            params={"page": 1, "per_page": 2},
        )

    def test_missing_optional_fields_use_defaults(self):
        response = Mock()
        response.json.return_value = [
            {
                "id": 501,
                "date_created": "2026-09-16T10:30:00Z",
            }
        ]

        self.client.get.return_value = response

        orders = self.adapter.get_orders()

        self.assertEqual(len(orders), 1)

        order = orders[0]

        self.assertEqual(order.external_id, "501")
        self.assertEqual(order.customer_name, "")
        self.assertEqual(order.customer_email, "")
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.total_amount, Decimal("0"))
        self.assertEqual(order.currency, "INR")
        self.assertEqual(
            order.ordered_at,
            datetime.fromisoformat("2026-09-16T10:30:00+00:00"),
        )
        self.assertEqual(order.items, [])

    def test_order_pagination(self):
        first_page = Mock()
        first_page.json.return_value = [
            {
                "id": 501,
                "date_created": "2026-09-16T10:30:00Z",
                "status": "processing",
                "total": "100.00",
                "currency": "INR",
                "billing": {},
                "line_items": [],
            },
            {
                "id": 502,
                "date_created": "2026-09-16T11:30:00Z",
                "status": "completed",
                "total": "200.00",
                "currency": "INR",
                "billing": {},
                "line_items": [],
            },
        ]

        second_page = Mock()
        second_page.json.return_value = [
            {
                "id": 503,
                "date_created": "2026-09-16T12:30:00Z",
                "status": "pending",
                "total": "300.00",
                "currency": "INR",
                "billing": {},
                "line_items": [],
            }
        ]

        self.client.get.side_effect = [
            first_page,
            second_page,
        ]

        orders = self.adapter.get_orders()

        self.assertEqual(len(orders), 3)

        self.assertEqual(orders[0].external_id, "501")
        self.assertEqual(orders[1].external_id, "502")
        self.assertEqual(orders[2].external_id, "503")

        self.assertEqual(
            self.client.get.call_args_list[0].kwargs["params"],
            {"page": 1, "per_page": 2},
        )

        self.assertEqual(
            self.client.get.call_args_list[1].kwargs["params"],
            {"page": 2, "per_page": 2},
        )
