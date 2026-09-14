from unittest.mock import Mock

from django.test import SimpleTestCase

from integrations.providers.woocommerce_product import WooCommerceProductAdapter


class WooCommerceProductAdapterTests(SimpleTestCase):
    def setUp(self):
        self.client = Mock()
        self.adapter = WooCommerceProductAdapter(
            self.client,
            per_page=2,
        )

    def test_get_products_maps_product_and_variation(self):
        product_response = Mock()
        product_response.json.return_value = [
            {
                "id": 101,
                "name": "Test T-Shirt",
                "description": "<p>Black T-Shirt</p>",
            }
        ]

        variation_response = Mock()
        variation_response.json.return_value = [
            {
                "id": 201,
                "sku": "TSHIRT-BLK-M",
                "price": "499.00",
                "currency": "INR",
            }
        ]

        self.client.get.side_effect = [
            product_response,
            variation_response,
        ]

        products = self.adapter.get_products()

        self.assertEqual(len(products), 1)

        product = products[0]

        self.assertEqual(product.external_id, "101")
        self.assertEqual(product.title, "Test T-Shirt")
        self.assertEqual(product.description, "<p>Black T-Shirt</p>")

        self.assertEqual(len(product.variants), 1)

        variant = product.variants[0]

        self.assertEqual(variant.external_id, "201")
        self.assertEqual(variant.sku, "TSHIRT-BLK-M")
        self.assertEqual(variant.price, 499)
        self.assertEqual(variant.currency, "INR")

    def test_empty_product_response_returns_empty_list(self):
        response = Mock()
        response.json.return_value = []

        self.client.get.return_value = response

        products = self.adapter.get_products()

        self.assertEqual(products, [])

        self.client.get.assert_called_once_with(
            "/products",
            params={"page": 1, "per_page": 2},
        )

    def test_product_without_variations_returns_empty_variants(self):
        product_response = Mock()
        product_response.json.return_value = [
            {
                "id": 101,
                "name": "Simple T-Shirt",
                "description": "",
            }
        ]

        variation_response = Mock()
        variation_response.json.return_value = []

        self.client.get.side_effect = [
            product_response,
            variation_response,
        ]

        products = self.adapter.get_products()

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].variants, [])

    def test_product_pagination(self):
        first_page = Mock()
        first_page.json.return_value = [
            {
                "id": 101,
                "name": "Product 1",
                "description": "",
            },
            {
                "id": 102,
                "name": "Product 2",
                "description": "",
            },
        ]

        second_page = Mock()
        second_page.json.return_value = [
            {
                "id": 103,
                "name": "Product 3",
                "description": "",
            }
        ]

        empty_variations = Mock()
        empty_variations.json.return_value = []

        self.client.get.side_effect = [
            first_page,
            empty_variations,
            empty_variations,
            second_page,
            empty_variations,
        ]

        products = self.adapter.get_products()

        self.assertEqual(len(products), 3)

        self.assertEqual(products[0].external_id, "101")
        self.assertEqual(products[1].external_id, "102")
        self.assertEqual(products[2].external_id, "103")

        self.assertEqual(
            self.client.get.call_args_list[0].kwargs["params"],
            {"page": 1, "per_page": 2},
        )

        self.assertEqual(
            self.client.get.call_args_list[3].kwargs["params"],
            {"page": 2, "per_page": 2},
        )

    def test_variation_pagination(self):
        product_response = Mock()
        product_response.json.return_value = [
            {
                "id": 101,
                "name": "Test Product",
                "description": "",
            }
        ]

        first_variation_page = Mock()
        first_variation_page.json.return_value = [
            {
                "id": 201,
                "sku": "SKU-1",
                "price": "100.00",
                "currency": "INR",
            },
            {
                "id": 202,
                "sku": "SKU-2",
                "price": "200.00",
                "currency": "INR",
            },
        ]

        second_variation_page = Mock()
        second_variation_page.json.return_value = [
            {
                "id": 203,
                "sku": "SKU-3",
                "price": "300.00",
                "currency": "INR",
            }
        ]

        self.client.get.side_effect = [
            product_response,
            first_variation_page,
            second_variation_page,
        ]

        products = self.adapter.get_products()

        variants = products[0].variants

        self.assertEqual(len(variants), 3)
        self.assertEqual(variants[0].external_id, "201")
        self.assertEqual(variants[1].external_id, "202")
        self.assertEqual(variants[2].external_id, "203")

        self.assertEqual(
            self.client.get.call_args_list[1].kwargs["params"],
            {"page": 1, "per_page": 2},
        )

        self.assertEqual(
            self.client.get.call_args_list[2].kwargs["params"],
            {"page": 2, "per_page": 2},
        )

    def test_missing_optional_fields_use_defaults(self):
        product_response = Mock()
        product_response.json.return_value = [
            {
                "id": 101,
                "name": "Test Product",
            }
        ]

        variation_response = Mock()
        variation_response.json.return_value = [
            {
                "id": 201,
            }
        ]

        self.client.get.side_effect = [
            product_response,
            variation_response,
        ]

        products = self.adapter.get_products()

        self.assertEqual(products[0].description, "")
        self.assertEqual(products[0].variants[0].sku, "")
        self.assertEqual(products[0].variants[0].price, 0)
        self.assertEqual(products[0].variants[0].currency, "INR")