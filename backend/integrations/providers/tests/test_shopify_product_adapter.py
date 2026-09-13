from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from integrations.providers.shopify import ShopifyClient
from integrations.providers.shopify_product import ShopifyProductAdapter


class ShopifyProductAdapterTests(SimpleTestCase):
    @patch.object(ShopifyClient, "get")
    def test_get_products_returns_normalized_products(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "products": [
                {
                    "id": 101,
                    "title": "Classic T-Shirt",
                    "body_html": "<p>Black cotton t-shirt</p>",
                    "variants": [
                        {
                            "id": 1001,
                            "sku": "TSHIRT-BLK-M",
                            "price": "499.00",
                        }
                    ],
                }
            ]
        }
        mock_get.return_value = mock_response

        adapter = ShopifyProductAdapter(
            client=ShopifyClient(
                shop_domain="example.myshopify.com",
                access_token="test-token",
            )
        )

        products = adapter.get_products()

        self.assertEqual(len(products), 1)

        product = products[0]

        self.assertEqual(product.external_id, "101")
        self.assertEqual(product.title, "Classic T-Shirt")
        self.assertEqual(product.description, "<p>Black cotton t-shirt</p>")

        self.assertEqual(len(product.variants), 1)

        variant = product.variants[0]

        self.assertEqual(variant.external_id, "1001")
        self.assertEqual(variant.sku, "TSHIRT-BLK-M")
        self.assertEqual(variant.price, Decimal("499.00"))
        self.assertEqual(variant.currency, "INR")

    @patch.object(ShopifyClient, "get")
    def test_get_products_handles_multiple_variants_and_missing_fields(
        self,
        mock_get,
    ):
        mock_response = Mock()
        mock_response.json.return_value = {
            "products": [
                {
                    "id": 102,
                    "title": "Hoodie",
                    "variants": [
                        {
                            "id": 2001,
                            "sku": "HOODIE-BLK-M",
                            "price": "899.00",
                        },
                        {
                            "id": 2002,
                            "sku": None,
                            "price": "999.00",
                        },
                    ],
                }
            ]
        }
        mock_get.return_value = mock_response

        adapter = ShopifyProductAdapter(
            client=ShopifyClient(
                shop_domain="example.myshopify.com",
                access_token="test-token",
            )
        )

        products = adapter.get_products()

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].description, "")

        self.assertEqual(len(products[0].variants), 2)

        self.assertEqual(
            products[0].variants[0].sku,
            "HOODIE-BLK-M",
        )
        self.assertEqual(
            products[0].variants[1].sku,
            "",
        )

    @patch.object(ShopifyClient, "get")
    def test_get_products_follows_pagination(self, mock_get):
        first_response = Mock()
        first_response.json.return_value = {
            "products": [
                {
                    "id": 101,
                    "title": "Product 1",
                    "variants": [],
                }
            ],
            "next": "/admin/api/products.json?page=2,"
        }

        second_response = Mock()
        second_response.json.return_value = {
            "products": [
                {
                    "id": 102,
                    "title": "Product 2",
                    "variants": [],
                }
            ],
            "next": None,
        }

        mock_get.side_effect = [first_response, second_response]

        adapter = ShopifyProductAdapter(
            client=ShopifyClient(
                shop_domain="example.myshopify.com",
                access_token="test-token",
            )
        )

        products = adapter.get_products()

        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].external_id, "101")
        self.assertEqual(products[1].external_id, "102")

        self.assertEqual(mock_get.call_count, 2)