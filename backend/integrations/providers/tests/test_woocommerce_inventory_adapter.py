from unittest.mock import Mock

from django.test import SimpleTestCase

from integrations.providers.woocommerce_inventory import (
    WooCommerceInventoryAdapter,
)


class WooCommerceInventoryAdapterTests(SimpleTestCase):
    def setUp(self):
        self.client = Mock()
        self.adapter = WooCommerceInventoryAdapter(
            self.client,
            per_page=2,
        )

    def test_get_inventory_maps_variation_stock(self):
        product_response = Mock()
        product_response.json.return_value = [
            {"id": 101, "name": "Test Product"}
        ]

        variation_response = Mock()
        variation_response.json.return_value = [
            {
                "id": 201,
                "sku": "SKU-001",
                "stock_quantity": 25,
            }
        ]

        self.client.get.side_effect = [
            product_response,
            variation_response,
        ]

        inventory = self.adapter.get_inventory()

        self.assertEqual(len(inventory), 1)

        item = inventory[0]

        self.assertEqual(item.external_variant_id, "201")
        self.assertEqual(item.sku, "SKU-001")
        self.assertEqual(item.quantity, 25)
        self.assertEqual(item.reserved_quantity, 0)
        
    def test_empty_product_response_returns_empty_inventory(self):
        response = Mock()
        response.json.return_value = []

        self.client.get.return_value = response

        inventory = self.adapter.get_inventory()

        self.assertEqual(inventory, [])

        self.client.get.assert_called_once_with(
            "/products",
            params={"page": 1, "per_page": 2},
        )

    def test_product_without_variations_returns_no_inventory(self):
        product_response = Mock()
        product_response.json.return_value = [
            {"id": 101, "name": "Simple Product"}
        ]

        variation_response = Mock()
        variation_response.json.return_value = []

        self.client.get.side_effect = [
            product_response,
            variation_response,
        ]

        inventory = self.adapter.get_inventory()

        self.assertEqual(inventory, [])

    def test_variation_pagination(self):
        product_response = Mock()
        product_response.json.return_value = [
            {"id": 101, "name": "Test Product"}
        ]

        first_variation_page = Mock()
        first_variation_page.json.return_value = [
            {
                "id": 201,
                "sku": "SKU-001",
                "stock_quantity": 20,
            },
            {
                "id": 202,
                "sku": "SKU-002",
                "stock_quantity": 30,
            },
        ]

        second_variation_page = Mock()
        second_variation_page.json.return_value = [
            {
                "id": 203,
                "sku": "SKU-003",
                "stock_quantity": 40,
            }
        ]

        self.client.get.side_effect = [
            product_response,
            first_variation_page,
            second_variation_page,
        ]

        inventory = self.adapter.get_inventory()

        self.assertEqual(len(inventory), 3)
        self.assertEqual(
            inventory[2].external_variant_id,
            "203",
        )

        self.assertEqual(
            self.client.get.call_args_list[1].kwargs["params"],
            {"page": 1, "per_page": 2},
        )

        self.assertEqual(
            self.client.get.call_args_list[2].kwargs["params"],
            {"page": 2, "per_page": 2},
        )

    def test_missing_stock_quantity_defaults_to_zero(self):
        product_response = Mock()
        product_response.json.return_value = [
            {"id": 101, "name": "Test Product"}
        ]

        variation_response = Mock()
        variation_response.json.return_value = [
            {
                "id": 201,
                "sku": "SKU-001",
            }
        ]

        self.client.get.side_effect = [
            product_response,
            variation_response,
        ]

        inventory = self.adapter.get_inventory()

        self.assertEqual(len(inventory), 1)
        self.assertEqual(inventory[0].quantity, 0)
        self.assertEqual(inventory[0].sku, "SKU-001")