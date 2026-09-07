from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from integrations.providers.errors import (
    AuthenticationError,
    RateLimitError,
    TemporaryProviderError,
)
from integrations.providers.mock import MockProvider
from integrations.providers.schemas import (
    NormalizedInventory,
    NormalizedOrder,
    NormalizedProduct,
)


class MockProviderTests(SimpleTestCase):

    def setUp(self):
        self.provider = MockProvider(store=None)

    @patch("integrations.providers.mock.requests.get")
    def test_get_products_returns_normalized_products(self, mock_get):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = [
            {
                "external_id": "prod-001",
                "title": "Test Product",
                "description": "Test description",
                "variants": [
                    {
                        "external_id": "var-001",
                        "sku": "TEST-SKU",
                        "price": "999.00",
                        "currency": "INR",
                    }
                ],
            }
        ]

        mock_get.return_value = mock_response

        products = self.provider.get_products()

        self.assertEqual(len(products), 1)
        self.assertIsInstance(products[0], NormalizedProduct)
        self.assertEqual(products[0].external_id, "prod-001")
        self.assertEqual(products[0].title, "Test Product")
        self.assertEqual(products[0].variants[0].sku, "TEST-SKU")

    @patch("integrations.providers.mock.requests.get")
    def test_get_inventory_returns_normalized_inventory(self, mock_get):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = [
            {
                "external_variant_id": "var-001",
                "sku": "TEST-SKU",
                "quantity": 100,
                "reserved_quantity": 5,
            }
        ]

        mock_get.return_value = mock_response

        inventory = self.provider.get_inventory()

        self.assertEqual(len(inventory), 1)
        self.assertIsInstance(inventory[0], NormalizedInventory)
        self.assertEqual(inventory[0].external_variant_id, "var-001")
        self.assertEqual(inventory[0].quantity, 100)

    @patch("integrations.providers.mock.requests.get")
    def test_get_orders_returns_normalized_orders(self, mock_get):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = [
            {
                "external_id": "order-001",
                "customer_name": "Test Customer",
                "status": "paid",
                "total_amount": "1998.00",
                "currency": "INR",
            }
        ]

        mock_get.return_value = mock_response

        orders = self.provider.get_orders()

        self.assertEqual(len(orders), 1)
        self.assertIsInstance(orders[0], NormalizedOrder)
        self.assertEqual(orders[0].external_id, "order-001")
        self.assertEqual(orders[0].customer_name, "Test Customer")
        self.assertEqual(orders[0].total_amount, Decimal("1998.00"))

    @patch("integrations.providers.mock.requests.get")
    def test_429_raises_rate_limit_error(self, mock_get):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 429

        mock_get.return_value = mock_response

        with self.assertRaises(RateLimitError):
            self.provider.get_products()

    @patch("integrations.providers.mock.requests.get")
    def test_401_raises_authentication_error(self, mock_get):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401

        mock_get.return_value = mock_response

        with self.assertRaises(AuthenticationError):
            self.provider.get_products()

    @patch("integrations.providers.mock.requests.get")
    def test_500_raises_temporary_provider_error(self, mock_get):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500

        mock_get.return_value = mock_response

        with self.assertRaises(TemporaryProviderError):
            self.provider.get_products()