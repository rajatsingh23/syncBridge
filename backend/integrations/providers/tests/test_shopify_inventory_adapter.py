from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from integrations.providers.shopify import ShopifyClient
from integrations.providers.shopify_inventory import ShopifyInventoryAdapter


class ShopifyInventoryAdapterTests(SimpleTestCase):
    @patch.object(ShopifyClient, "get")
    def test_get_inventory_returns_normalized_inventory(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "inventory_levels": [
                {
                    "inventory_item_id": 5001,
                    "available": 25,
                }
            ]
        }
        mock_get.return_value = mock_response

        adapter = ShopifyInventoryAdapter(
            client=ShopifyClient(
                shop_domain="example.myshopify.com",
                access_token="test-token",
            )
        )

        inventory = adapter.get_inventory()

        self.assertEqual(len(inventory), 1)

        item = inventory[0]

        self.assertEqual(item.external_variant_id, "5001")
        self.assertEqual(item.quantity, 25)

    @patch.object(ShopifyClient, "get")
    def test_get_inventory_handles_multiple_items(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "inventory_levels": [
                {
                    "inventory_item_id": 5001,
                    "available": 25,
                },
                {
                    "inventory_item_id": 5002,
                    "available": 80,
                },
            ]
        }
        mock_get.return_value = mock_response

        adapter = ShopifyInventoryAdapter(
            client=ShopifyClient(
                shop_domain="example.myshopify.com",
                access_token="test-token",
            )
        )

        inventory = adapter.get_inventory()

        self.assertEqual(len(inventory), 2)
        self.assertEqual(inventory[0].external_variant_id, "5001")
        self.assertEqual(inventory[0].quantity, 25)
        self.assertEqual(inventory[1].external_variant_id, "5002")
        self.assertEqual(inventory[1].quantity, 80)

    @patch.object(ShopifyClient, "get")
    def test_get_inventory_handles_missing_available_quantity(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "inventory_levels": [
                {
                    "inventory_item_id": 5003,
                }
            ]
        }
        mock_get.return_value = mock_response

        adapter = ShopifyInventoryAdapter(
            client=ShopifyClient(
                shop_domain="example.myshopify.com",
                access_token="test-token",
            )
        )

        inventory = adapter.get_inventory()

        self.assertEqual(len(inventory), 1)
        self.assertEqual(inventory[0].external_variant_id, "5003")
        self.assertEqual(inventory[0].quantity, 0)

    @patch.object(ShopifyClient, "get")
    def test_get_inventory_follows_pagination(self, mock_get):
        first_response = Mock()
        first_response.json.return_value = {
            "inventory_levels": [
                {
                    "inventory_item_id": 5001,
                    "available": 25,
                }
            ],
            "next": "/admin/api/inventory_levels.json?page=2",
        }

        second_response = Mock()
        second_response.json.return_value = {
            "inventory_levels": [
                {
                    "inventory_item_id": 5002,
                    "available": 80,
                }
            ],
            "next": None,
        }

        mock_get.side_effect = [first_response, second_response]

        adapter = ShopifyInventoryAdapter(
            client=ShopifyClient(
                shop_domain="example.myshopify.com",
                access_token="test-token",
            )
        )

        inventory = adapter.get_inventory()

        self.assertEqual(len(inventory), 2)
        self.assertEqual(inventory[0].external_variant_id, "5001")
        self.assertEqual(inventory[1].external_variant_id, "5002")

        self.assertEqual(mock_get.call_count, 2)