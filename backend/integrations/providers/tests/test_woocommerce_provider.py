from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from integrations.providers.woocommerce_provider import WooCommerceProvider


class WooCommerceProviderTests(SimpleTestCase):
    def setUp(self):
        self.store = Mock()
        self.store.credentials = {
            "store_url": "https://example.com/",
            "consumer_key": "ck_test",
            "consumer_secret": "cs_test",
        }

    @patch("integrations.providers.woocommerce_provider.WooCommerceClient")
    def test_provider_initializes_with_credentials(self, mock_client):
        provider = WooCommerceProvider(self.store)

        mock_client.assert_called_once_with(
            store_url="https://example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        self.assertIsNotNone(provider.product_adapter)
        self.assertIsNotNone(provider.inventory_adapter)
        self.assertIsNotNone(provider.order_adapter)

    @patch("integrations.providers.woocommerce_provider.WooCommerceClient")
    def test_get_products_delegates_to_product_adapter(self, mock_client):
        provider = WooCommerceProvider(self.store)

        expected = ["product-1"]
        provider.product_adapter.get_products = Mock(
            return_value=expected
        )

        result = provider.get_products()

        self.assertEqual(result, expected)
        provider.product_adapter.get_products.assert_called_once_with()

    @patch("integrations.providers.woocommerce_provider.WooCommerceClient")
    def test_get_inventory_delegates_to_inventory_adapter(self, mock_client):
        provider = WooCommerceProvider(self.store)

        expected = ["inventory-1"]
        provider.inventory_adapter.get_inventory = Mock(
            return_value=expected
        )

        result = provider.get_inventory()

        self.assertEqual(result, expected)
        provider.inventory_adapter.get_inventory.assert_called_once_with()

    @patch("integrations.providers.woocommerce_provider.WooCommerceClient")
    def test_get_orders_delegates_to_order_adapter(self, mock_client):
        provider = WooCommerceProvider(self.store)

        expected = ["order-1"]
        provider.order_adapter.get_orders = Mock(
            return_value=expected
        )

        result = provider.get_orders()

        self.assertEqual(result, expected)
        provider.order_adapter.get_orders.assert_called_once_with()

    @patch("integrations.providers.woocommerce_provider.WooCommerceClient")
    def test_update_inventory_delegates_to_client(self, mock_client):
        provider = WooCommerceProvider(self.store)

        expected = Mock()
        provider.client.put.return_value = expected

        result = provider.update_inventory(
            external_variant_id="201",
            quantity=50,
        )

        self.assertIs(result, expected)

        provider.client.put.assert_called_once_with(
            "/products/variations/201",
            json={
                "stock_quantity": 50,
                "manage_stock": True,
            },
        )

    def test_missing_credentials_raise_error(self):
        self.store.credentials = {
            "store_url": "https://example.com",
            "consumer_key": "ck_test",
        }

        with self.assertRaises(KeyError):
            WooCommerceProvider(self.store)