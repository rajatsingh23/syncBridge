from django.test import TestCase

from accounts.models import User
from integrations.providers.schemas import NormalizedInventory
from products.models import ExternalVariant, Inventory, Product, Variant
from stores.models import Integration, Store
from synchronization.services.inventory_sync import sync_inventory


class InventorySyncTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="inventory-sync-test@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.MOCK
        )

        cls.store = Store.objects.create(
            user=cls.user,
            integration=integration,
            name="Inventory Sync Test Store",
            external_store_id="inventory-sync-test-store",
        )

        cls.product = Product.objects.create(
            owner=cls.user,
            title="Test Product",
        )

        cls.variant = Variant.objects.create(
            product=cls.product,
            sku="INV-TEST-001",
            title="Test Variant",
            price="499.00",
            currency="INR",
        )

        cls.external_variant = ExternalVariant.objects.create(
            variant=cls.variant,
            store=cls.store,
            external_id="external-variant-001",
        )

    def test_first_sync_creates_inventory(self):
        normalized_inventory = NormalizedInventory(
            external_variant_id="external-variant-001",
            sku="INV-TEST-001",
            quantity=100,
            reserved_quantity=10,
        )

        inventory = sync_inventory(
            store=self.store,
            normalized_inventory=normalized_inventory,
        )

        self.assertEqual(inventory.variant, self.variant)
        self.assertEqual(inventory.store, self.store)
        self.assertEqual(inventory.quantity, 100)
        self.assertEqual(inventory.reserved_quantity, 10)

        self.assertEqual(Inventory.objects.count(), 1)

    def test_second_sync_updates_existing_inventory(self):
        first_inventory = NormalizedInventory(
            external_variant_id="external-variant-001",
            sku="INV-TEST-001",
            quantity=100,
            reserved_quantity=10,
        )

        second_inventory = NormalizedInventory(
            external_variant_id="external-variant-001",
            sku="INV-TEST-001",
            quantity=75,
            reserved_quantity=20,
        )

        sync_inventory(
            store=self.store,
            normalized_inventory=first_inventory,
        )

        sync_inventory(
            store=self.store,
            normalized_inventory=second_inventory,
        )

        inventory = Inventory.objects.get(
            variant=self.variant,
            store=self.store,
        )

        self.assertEqual(inventory.quantity, 75)
        self.assertEqual(inventory.reserved_quantity, 20)

        # Still only one inventory record.
        self.assertEqual(Inventory.objects.count(), 1)

    def test_missing_external_variant_mapping_raises_error(self):
        normalized_inventory = NormalizedInventory(
            external_variant_id="does-not-exist",
            sku="UNKNOWN",
            quantity=50,
            reserved_quantity=0,
        )

        with self.assertRaises(ValueError) as context:
            sync_inventory(
                store=self.store,
                normalized_inventory=normalized_inventory,
            )

        self.assertIn(
            "External variant mapping not found",
            str(context.exception),
        )

        self.assertEqual(Inventory.objects.count(), 0)