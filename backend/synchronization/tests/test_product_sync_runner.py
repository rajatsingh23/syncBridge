from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from accounts.models import User
from integrations.providers.schemas import (
    NormalizedProduct,
    NormalizedVariant,
)
from products.models import (
    ExternalProduct,
    ExternalVariant,
    Product,
    Variant,
)
from stores.models import Integration, Store
from synchronization.services.product_sync_runner import sync_products


class ProductSyncRunnerTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="runner-test@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.MOCK
        )

        cls.store = Store.objects.create(
            user=cls.user,
            integration=integration,
            name="Runner Test Store",
            external_store_id="runner-test-store",
        )

    def test_sync_products_fetches_and_upserts_products(self):
        normalized_products = [
            NormalizedProduct(
                external_id="external-product-001",
                title="Black T-Shirt",
                description="Black cotton t-shirt",
                variants=[
                    NormalizedVariant(
                        external_id="external-variant-001",
                        sku="TSHIRT-BLK-M",
                        price=Decimal("499.00"),
                        currency="INR",
                    )
                ],
            ),
            NormalizedProduct(
                external_id="external-product-002",
                title="White T-Shirt",
                description="White cotton t-shirt",
                variants=[
                    NormalizedVariant(
                        external_id="external-variant-002",
                        sku="TSHIRT-WHT-M",
                        price=Decimal("499.00"),
                        currency="INR",
                    )
                ],
            ),
        ]

        with patch(
            "synchronization.services.product_sync_runner.get_provider"
        ) as mock_get_provider:
            mock_provider = mock_get_provider.return_value
            mock_provider.get_products.return_value = normalized_products

            synced_products = sync_products(self.store)

        mock_get_provider.assert_called_once_with(self.store)
        mock_provider.get_products.assert_called_once_with()

        self.assertEqual(len(synced_products), 2)

        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(Variant.objects.count(), 2)
        self.assertEqual(ExternalProduct.objects.count(), 2)
        self.assertEqual(ExternalVariant.objects.count(), 2)

    def test_second_sync_does_not_create_duplicates(self):
        normalized_products = [
            NormalizedProduct(
                external_id="external-product-001",
                title="Black T-Shirt",
                description="Black cotton t-shirt",
                variants=[
                    NormalizedVariant(
                        external_id="external-variant-001",
                        sku="TSHIRT-BLK-M",
                        price=Decimal("499.00"),
                        currency="INR",
                    )
                ],
            )
        ]

        with patch(
            "synchronization.services.product_sync_runner.get_provider"
        ) as mock_get_provider:
            mock_provider = mock_get_provider.return_value
            mock_provider.get_products.return_value = normalized_products

            # First sync
            sync_products(self.store)

            self.assertEqual(Product.objects.count(), 1)
            self.assertEqual(Variant.objects.count(), 1)
            self.assertEqual(ExternalProduct.objects.count(), 1)
            self.assertEqual(ExternalVariant.objects.count(), 1)

            # Second sync
            sync_products(self.store)

        # Nothing new should have been created.
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Variant.objects.count(), 1)
        self.assertEqual(ExternalProduct.objects.count(), 1)
        self.assertEqual(ExternalVariant.objects.count(), 1)

    def test_second_sync_updates_existing_product(self):
        first_product = NormalizedProduct(
            external_id="external-product-001",
            title="Black T-Shirt",
            description="Original description",
            variants=[
                NormalizedVariant(
                    external_id="external-variant-001",
                    sku="TSHIRT-BLK-M",
                    price=Decimal("499.00"),
                    currency="INR",
                )
            ],
        )

        updated_product = NormalizedProduct(
            external_id="external-product-001",
            title="Premium Black T-Shirt",
            description="Updated description",
            variants=[
                NormalizedVariant(
                    external_id="external-variant-001",
                    sku="TSHIRT-BLK-M",
                    price=Decimal("599.00"),
                    currency="INR",
                )
            ],
        )

        with patch(
            "synchronization.services.product_sync_runner.get_provider"
        ) as mock_get_provider:
            mock_provider = mock_get_provider.return_value

            # First sync
            mock_provider.get_products.return_value = [first_product]
            sync_products(self.store)

            # Second sync with changed data
            mock_provider.get_products.return_value = [updated_product]
            sync_products(self.store)

        product = Product.objects.get(
            owner=self.user,
        )

        variant = Variant.objects.get(
            product=product,
        )

        self.assertEqual(product.title, "Premium Black T-Shirt")
        self.assertEqual(product.description, "Updated description")
        self.assertEqual(variant.price, Decimal("599.00"))

        # Still only one record.
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Variant.objects.count(), 1)
        self.assertEqual(ExternalProduct.objects.count(), 1)
        self.assertEqual(ExternalVariant.objects.count(), 1)