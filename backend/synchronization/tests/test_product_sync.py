from decimal import Decimal

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
from synchronization.services.product_sync import sync_product


class ProductSyncTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="sync-product@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.MOCK
        )

        cls.store = Store.objects.create(
            user=cls.user,
            integration=integration,
            name="Test Store",
            external_store_id="test-store",
        )

    def create_normalized_product(self):
        return NormalizedProduct(
            external_id="external-product-001",
            title="Black T-Shirt",
            description="A black cotton t-shirt",
            variants=[
                NormalizedVariant(
                    external_id="external-variant-001",
                    sku="TSHIRT-BLK-M",
                    price=Decimal("499.00"),
                    currency="INR",
                ),
                NormalizedVariant(
                    external_id="external-variant-002",
                    sku="TSHIRT-BLK-L",
                    price=Decimal("499.00"),
                    currency="INR",
                ),
            ],
        )

    def test_first_sync_creates_product_and_mappings(self):
        normalized_product = self.create_normalized_product()

        product = sync_product(
            self.store,
            normalized_product,
        )

        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Variant.objects.count(), 2)
        self.assertEqual(ExternalProduct.objects.count(), 1)
        self.assertEqual(ExternalVariant.objects.count(), 2)

        self.assertEqual(
            product.title,
            "Black T-Shirt",
        )

        external_product = ExternalProduct.objects.get(
            store=self.store,
            external_id="external-product-001",
        )

        self.assertEqual(
            external_product.product,
            product,
        )

    def test_second_sync_does_not_create_duplicates(self):
        normalized_product = self.create_normalized_product()

        sync_product(
            self.store,
            normalized_product,
        )

        sync_product(
            self.store,
            normalized_product,
        )

        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Variant.objects.count(), 2)
        self.assertEqual(ExternalProduct.objects.count(), 1)
        self.assertEqual(ExternalVariant.objects.count(), 2)

    def test_second_sync_updates_existing_product(self):
        normalized_product = self.create_normalized_product()

        product = sync_product(
            self.store,
            normalized_product,
        )

        original_product_id = product.id

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
                ),
                NormalizedVariant(
                    external_id="external-variant-002",
                    sku="TSHIRT-BLK-L",
                    price=Decimal("649.00"),
                    currency="INR",
                ),
            ],
        )

        sync_product(
            self.store,
            updated_product,
        )

        product.refresh_from_db()

        self.assertEqual(
            product.id,
            original_product_id,
        )

        self.assertEqual(
            product.title,
            "Premium Black T-Shirt",
        )

        self.assertEqual(
            product.description,
            "Updated description",
        )

        variant_m = Variant.objects.get(
            sku="TSHIRT-BLK-M"
        )

        variant_l = Variant.objects.get(
            sku="TSHIRT-BLK-L"
        )

        self.assertEqual(
            variant_m.price,
            Decimal("599.00"),
        )

        self.assertEqual(
            variant_l.price,
            Decimal("649.00"),
        )

    def test_new_variant_is_created_on_next_sync(self):
        normalized_product = self.create_normalized_product()

        sync_product(
            self.store,
            normalized_product,
        )

        normalized_product.variants.append(
            NormalizedVariant(
                external_id="external-variant-003",
                sku="TSHIRT-BLK-XL",
                price=Decimal("699.00"),
                currency="INR",
            )
        )

        sync_product(
            self.store,
            normalized_product,
        )

        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Variant.objects.count(), 3)
        self.assertEqual(ExternalProduct.objects.count(), 1)
        self.assertEqual(ExternalVariant.objects.count(), 3)

        self.assertTrue(
            ExternalVariant.objects.filter(
                store=self.store,
                external_id="external-variant-003",
            ).exists()
        )