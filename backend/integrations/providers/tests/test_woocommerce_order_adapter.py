from unittest.mock import Mock

from django.test import SimpleTestCase

from integrations.providers.woocommerce_order import WooCommerceOrderAdapter

from decimal import Decimal

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
                "status": "processing",
                "total": "1299.50",
                "currency": "INR",
                "billing": {
                    "first_name": "Rajat",
                    "last_name": "Singh",
                },
            }
        ]

        self.client.get.return_value = response

        orders = self.adapter.get_orders()

        self.assertEqual(len(orders), 1)

        order = orders[0]

        self.assertEqual(order.external_id, "501")
        self.assertEqual(order.customer_name, "Rajat Singh")
        self.assertEqual(order.status, "processing")
        self.assertEqual(order.total_amount, Decimal("1299.50"))
        self.assertEqual(order.currency, "INR")

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
            }
        ]

        self.client.get.return_value = response

        orders = self.adapter.get_orders()

        self.assertEqual(len(orders), 1)

        order = orders[0]

        self.assertEqual(order.external_id, "501")
        self.assertEqual(order.customer_name, "")
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.total_amount, Decimal("0"))
        self.assertEqual(order.currency, "INR")

    def test_order_pagination(self):
        first_page = Mock()
        first_page.json.return_value = [
            {
                "id": 501,
                "status": "processing",
                "total": "100.00",
                "currency": "INR",
                "billing": {},
            },
            {
                "id": 502,
                "status": "completed",
                "total": "200.00",
                "currency": "INR",
                "billing": {},
            },
        ]

        second_page = Mock()
        second_page.json.return_value = [
            {
                "id": 503,
                "status": "pending",
                "total": "300.00",
                "currency": "INR",
                "billing": {},
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