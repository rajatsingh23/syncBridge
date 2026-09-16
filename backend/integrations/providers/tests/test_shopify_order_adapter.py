from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from integrations.providers.schemas import NormalizedOrderItem
from integrations.providers.shopify import ShopifyClient
from integrations.providers.shopify_order import ShopifyOrderAdapter


class ShopifyOrderAdapterTests(SimpleTestCase):

    @patch.object(ShopifyClient, "get")
    def test_get_orders_returns_normalized_orders(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "orders": [
                {
                    "id": 9001,
                    "created_at": "2026-09-16T10:30:00Z",
                    "customer": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john@example.com",
                    },
                    "financial_status": "paid",
                    "current_total_price": "1299.00",
                    "currency": "INR",
                    "line_items": [
                        {
                            "variant_id": 201,
                            "product_id": 101,
                            "sku": "TSHIRT-BLK-M",
                            "quantity": 2,
                            "price": "499.00",
                        }
                    ],
                }
            ]
        }

        mock_get.return_value = mock_response

        adapter = ShopifyOrderAdapter(
            client=ShopifyClient(
                shop_domain="example.myshopify.com",
                access_token="test-token",
            )
        )

        orders = adapter.get_orders()

        self.assertEqual(len(orders), 1)

        order = orders[0]

        self.assertEqual(order.external_id, "9001")
        self.assertEqual(order.customer_name, "John Doe")
        self.assertEqual(order.customer_email, "john@example.com")
        self.assertEqual(order.status, "paid")
        self.assertEqual(order.total_amount, Decimal("1299.00"))
        self.assertEqual(order.currency, "INR")

        self.assertEqual(
            order.ordered_at,
            datetime.fromisoformat(
                "2026-09-16T10:30:00+00:00"
            ),
        )

        self.assertEqual(len(order.items), 1)

        self.assertEqual(
            order.items[0],
            NormalizedOrderItem(
                external_variant_id="201",
                sku="TSHIRT-BLK-M",
                quantity=2,
                unit_price=Decimal("499.00"),
            ),
        )

    @patch.object(ShopifyClient, "get")
    def test_get_orders_handles_multiple_orders_and_missing_customer(
        self,
        mock_get,
    ):
        mock_response = Mock()
        mock_response.json.return_value = {
            "orders": [
                {
                    "id": 9001,
                    "created_at": "2026-09-16T10:30:00Z",
                    "customer": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john@example.com",
                    },
                    "financial_status": "paid",
                    "current_total_price": "1299.00",
                    "currency": "INR",
                    "line_items": [],
                },
                {
                    "id": 9002,
                    "created_at": "2026-09-16T11:30:00Z",
                    "customer": None,
                    "financial_status": "pending",
                    "current_total_price": "799.00",
                    "currency": "INR",
                    "line_items": [],
                },
            ]
        }

        mock_get.return_value = mock_response

        adapter = ShopifyOrderAdapter(
            client=ShopifyClient(
                shop_domain="example.myshopify.com",
                access_token="test-token",
            )
        )

        orders = adapter.get_orders()

        self.assertEqual(len(orders), 2)

        self.assertEqual(orders[0].external_id, "9001")
        self.assertEqual(orders[0].customer_name, "John Doe")
        self.assertEqual(
            orders[0].customer_email,
            "john@example.com",
        )

        self.assertEqual(orders[1].external_id, "9002")
        self.assertEqual(orders[1].customer_name, "")
        self.assertEqual(orders[1].customer_email, "")
        self.assertEqual(orders[1].status, "pending")
        self.assertEqual(
            orders[1].total_amount,
            Decimal("799.00"),
        )
        self.assertEqual(orders[1].items, [])

    @patch.object(ShopifyClient, "get")
    def test_get_orders_handles_missing_total_price(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "orders": [
                {
                    "id": 9003,
                    "created_at": "2026-09-16T12:30:00Z",
                    "customer": {
                        "first_name": "Jane",
                        "last_name": "Doe",
                    },
                    "financial_status": "paid",
                    "currency": "INR",
                    "line_items": [],
                }
            ]
        }

        mock_get.return_value = mock_response

        adapter = ShopifyOrderAdapter(
            client=ShopifyClient(
                shop_domain="example.myshopify.com",
                access_token="test-token",
            )
        )

        orders = adapter.get_orders()

        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].external_id, "9003")
        self.assertEqual(
            orders[0].total_amount,
            Decimal("0"),
        )
        self.assertEqual(
            orders[0].customer_email,
            "",
        )
        self.assertEqual(orders[0].items, [])

    @patch.object(ShopifyClient, "get")
    def test_get_orders_follows_pagination(self, mock_get):
        first_response = Mock()
        first_response.json.return_value = {
            "orders": [
                {
                    "id": 9001,
                    "created_at": "2026-09-16T10:30:00Z",
                    "customer": {
                        "first_name": "John",
                        "last_name": "Doe",
                    },
                    "financial_status": "paid",
                    "current_total_price": "1299.00",
                    "currency": "INR",
                    "line_items": [],
                }
            ],
            "next": "/admin/api/orders.json?page=2",
        }

        second_response = Mock()
        second_response.json.return_value = {
            "orders": [
                {
                    "id": 9002,
                    "created_at": "2026-09-16T11:30:00Z",
                    "customer": {
                        "first_name": "Jane",
                        "last_name": "Doe",
                    },
                    "financial_status": "pending",
                    "current_total_price": "799.00",
                    "currency": "INR",
                    "line_items": [],
                }
            ],
            "next": None,
        }

        mock_get.side_effect = [
            first_response,
            second_response,
        ]

        adapter = ShopifyOrderAdapter(
            client=ShopifyClient(
                shop_domain="example.myshopify.com",
                access_token="test-token",
            )
        )

        orders = adapter.get_orders()

        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0].external_id, "9001")
        self.assertEqual(orders[1].external_id, "9002")

        self.assertEqual(mock_get.call_count, 2)

        self.assertEqual(
            mock_get.call_args_list[0].args,
            ("/admin/api/orders.json",),
        )

        self.assertEqual(
            mock_get.call_args_list[1].args,
            ("/admin/api/orders.json?page=2",),
        )