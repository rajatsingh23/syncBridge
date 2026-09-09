from decimal import Decimal
from unittest.mock import Mock

from django.test import SimpleTestCase

from integrations.providers.errors import (
    AuthenticationError,
    RateLimitError,
    TemporaryProviderError,
    NotFoundError,
    ProviderRequestError
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
        self.provider.client = Mock()

    def test_get_products_returns_normalized_products(self):
        self.provider.client.get.return_value.ok = True
        self.provider.client.get.return_value.json.return_value = [
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

        products = self.provider.get_products()

        self.assertEqual(len(products), 1)
        self.assertIsInstance(products[0], NormalizedProduct)
        self.assertEqual(products[0].external_id, "prod-001")
        self.assertEqual(products[0].title, "Test Product")
        self.assertEqual(products[0].variants[0].sku, "TEST-SKU")

        self.provider.client.get.assert_called_once_with(
            f"{self.provider.base_url}/products/",
        )

    def test_get_inventory_returns_normalized_inventory(self):
        self.provider.client.get.return_value.ok = True
        self.provider.client.get.return_value.json.return_value = [
            {
                "external_variant_id": "var-001",
                "sku": "TEST-SKU",
                "quantity": 100,
                "reserved_quantity": 5,
            }
        ]

        inventory = self.provider.get_inventory()

        self.assertEqual(len(inventory), 1)
        self.assertIsInstance(inventory[0], NormalizedInventory)
        self.assertEqual(inventory[0].external_variant_id, "var-001")
        self.assertEqual(inventory[0].quantity, 100)

        self.provider.client.get.assert_called_once_with(
            f"{self.provider.base_url}/inventory/",
        )

    def test_get_orders_returns_normalized_orders(self):
        self.provider.client.get.return_value.ok = True
        self.provider.client.get.return_value.json.return_value = [
            {
                "external_id": "order-001",
                "customer_name": "Test Customer",
                "status": "paid",
                "total_amount": "1998.00",
                "currency": "INR",
            }
        ]

        orders = self.provider.get_orders()

        self.assertEqual(len(orders), 1)
        self.assertIsInstance(orders[0], NormalizedOrder)
        self.assertEqual(orders[0].external_id, "order-001")
        self.assertEqual(orders[0].customer_name, "Test Customer")
        self.assertEqual(orders[0].total_amount, Decimal("1998.00"))

        self.provider.client.get.assert_called_once_with(
            f"{self.provider.base_url}/orders/",
        )

    def test_429_raises_rate_limit_error(self):
        self.provider.client.get.return_value.ok = False
        self.provider.client.get.return_value.status_code = 429

        with self.assertRaises(RateLimitError):
            self.provider.get_products()

        self.provider.client.get.assert_called_once_with(
            f"{self.provider.base_url}/products/",
        )

    def test_401_raises_authentication_error(self):
        self.provider.client.get.return_value.ok = False
        self.provider.client.get.return_value.status_code = 401

        with self.assertRaises(AuthenticationError):
            self.provider.get_products()

        self.provider.client.get.assert_called_once_with(
            f"{self.provider.base_url}/products/",
        )

    def test_500_raises_temporary_provider_error(self):
        self.provider.client.get.return_value.ok = False
        self.provider.client.get.return_value.status_code = 500

        with self.assertRaises(TemporaryProviderError):
            self.provider.get_products()

        self.provider.client.get.assert_called_once_with(
            f"{self.provider.base_url}/products/",
        )

    def test_404_raises_not_found_error(self):
        self.provider.client.get.return_value.ok = False
        self.provider.client.get.return_value.status_code = 404
        with self.assertRaises(NotFoundError) as context:
            self.provider.get_products()

        self.assertFalse(context.exception.retryable)

    def test_400_raises_provider_request_error(self):
        self.provider.client.get.return_value.ok = False
        self.provider.client.get.return_value.status_code = 400

        with self.assertRaises(ProviderRequestError) as context:
            self.provider.get_products()

        self.assertFalse(context.exception.retryable)

    def test_429_stores_retry_after(self):
        response = Mock()
        response.status_code = 429
        response.headers = {"Retry-After": "5"}

        self.provider.client.get.return_value = response

        with self.assertRaises(RateLimitError) as context:
            self.provider._handle_response_error(response)

        self.assertEqual(context.exception.retry_after, 5)

    def test_429_without_retry_after(self):
        response = Mock()
        response.status_code = 429
        response.header = {}

        with self.assertRaises(RateLimitError) as context:
            self.provider._handle_response_error(response)

        self.assertIsNone(context.exception.retry_after)

    def test_429_with_invalid_retry_after(self):
        response = Mock()
        response.status_code = 429
        response.headers = {"Retry-After": "abc"}

        with self.assertRaises(RateLimitError) as context:
            self.provider._handle_response_error(response)

        self.assertIsNone(context.exception.retry_after)