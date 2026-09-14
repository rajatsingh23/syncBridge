from unittest.mock import Mock

from django.test import SimpleTestCase

from integrations.providers.factory import get_provider
from integrations.providers.mock import MockProvider
from integrations.providers.shopify_provider import ShopifyProvider


class ProviderFactoryTests(SimpleTestCase):
    def test_factory_returns_mock_provider(self):
        store = Mock()
        store.integration.provider = "mock"

        provider = get_provider(store)

        self.assertIsInstance(provider, MockProvider)

    def test_factory_returns_shopify_provider(self):
        store = Mock()
        store.integration.provider = "shopify"
        store.credentials = {
            "shop_domain": "example.myshopify.com",
            "access_token": "test_token",
        }

        provider = get_provider(store)

        self.assertIsInstance(provider, ShopifyProvider)

    def test_shopify_provider_get_products_uses_product_adapter(self):
        store = Mock()
        store.integration.provider = "shopify"
        store.credentials = {
            "shop_domain": "example.myshopify.com",
            "access_token": "test-token",
        }

        provider = get_provider(store)

        expected_products = [Mock(), Mock()]
        provider.product_adapter.get_products = Mock(
            return_value=expected_products
        )

        products = provider.get_products()

        self.assertEqual(products, expected_products)
        provider.product_adapter.get_products.assert_called_once_with()

    def test_shopify_provider_get_inventory_uses_inventory_adapter(self):
        store = Mock()
        store.integration.provider = "shopify"
        store.credentials = {
            "shop_domain": "example.myshopify.com",
            "access_token": "test-token",
        }

        provider = get_provider(store)

        expected_inventory = [Mock(), Mock()]
        provider.inventory_adapter = Mock()
        provider.inventory_adapter.get_inventory.return_value = expected_inventory

        inventory = provider.get_inventory()

        self.assertEqual(inventory, expected_inventory)
        provider.inventory_adapter.get_inventory.assert_called_once_with()

    def test_shopify_provider_get_orders_uses_order_adapter(self):
        store = Mock()
        store.integration.provider = "shopify"
        store.credentials = {
            "shop_domain": "example.myshopify.com",
            "access_token": "test-token",
        }

        provider = get_provider(store)

        expected_orders = [Mock(), Mock()]
        provider.order_adapter = Mock()
        provider.order_adapter.get_orders.return_value = expected_orders

        orders = provider.get_orders()

        self.assertEqual(orders, expected_orders)
        provider.order_adapter.get_orders.assert_called_once_with()

    def test_shopify_provider_update_inventory_uses_client(self):
        store = Mock()
        store.integration.provider = "shopify"
        store.credentials = {
            "shop_domain": "example.myshopify.com",
            "access_token": "test-token",
        }

        provider = get_provider(store)

        provider.client.put = Mock()

        provider.update_inventory(
            external_variant_id="5001",
            quantity=50,
        )

        provider.client.put.assert_called_once_with(
            "/admin/api/inventory_levels.json",
            json={
                "inventory_item_id": "5001",
                "available": 50,
            },
        )
    def test_shopify_provider_update_inventory_returns_client_response(self):
        store = Mock()
        store.integration.provider = "shopify"
        store.credentials = {
            "shop_domain": "example.myshopify.com",
            "access_token": "test-token",
        }

        provider = get_provider(store)

        expected_response = Mock()
        provider.client.put = Mock(return_value=expected_response)

        response = provider.update_inventory(
            external_variant_id="5001",
            quantity=50,
        )

        self.assertIs(response, expected_response)