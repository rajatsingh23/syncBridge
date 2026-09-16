from unittest.mock import patch

from django.test import TestCase

from accounts.models import User
from products.models import ExternalVariant, Inventory, Product, Variant
from stores.models import Integration, Store
from synchronization.models import SyncJob, SyncError
from synchronization.services.inventory_sync_job import (
    sync_inventory_with_job,
)

from integrations.providers.schemas import NormalizedInventory

class InventorySyncJobTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="inventory-job-test@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.MOCK
        )

        cls.store = Store.objects.create(
            user=cls.user,
            integration=integration,
            name="Inventory Job Test Store",
            external_store_id="inventory-job-test-store",
        )

        cls.product = Product.objects.create(
            owner=cls.user,
            title="Inventory Job Product",
        )

        cls.variant = Variant.objects.create(
            product=cls.product,
            sku="JOB-INV-001",
            title="Inventory Job Variant",
            price="499.00",
            currency="INR",
        )

        ExternalVariant.objects.create(
            variant=cls.variant,
            store=cls.store,
            external_id="external-variant-001",
        )

    def test_inventory_sync_creates_and_completes_sync_job(self):
        normalized_inventory = NormalizedInventory(
            external_variant_id="external-variant-001",
            sku="JOB-INV-001",
            quantity=100,
            reserved_quantity=10,
        )

        synced_inventory = Inventory.objects.create(
            variant=self.variant,
            store=self.store,
            quantity=100,
            reserved_quantity=10,
        )

        with patch(
            "synchronization.services.inventory_sync_job.fetch_sync_items"
        ) as mock_fetch:
            with patch(
                "synchronization.services.inventory_sync_job.sync_item"
            ) as mock_sync_item:
                mock_fetch.return_value = [
                    normalized_inventory,
                ]

                mock_sync_item.return_value = synced_inventory

                sync_job = sync_inventory_with_job(self.store)

        mock_fetch.assert_called_once_with(
            store=self.store,
            sync_type=SyncJob.SyncType.INVENTORY,
        )

        mock_sync_item.assert_called_once_with(
            store=self.store,
            sync_type=SyncJob.SyncType.INVENTORY,
            item=normalized_inventory,
        )

        self.assertEqual(
            sync_job.status,
            SyncJob.Status.COMPLETED,
        )

        self.assertEqual(sync_job.total_items, 1)
        self.assertEqual(sync_job.processed_items, 1)
        self.assertEqual(sync_job.successful_items, 1)
        self.assertEqual(sync_job.failed_items, 0)

        self.assertIsNotNone(sync_job.started_at)
        self.assertIsNotNone(sync_job.completed_at)

        inventory = Inventory.objects.get(
            variant=self.variant,
            store=self.store,
        )

        self.assertEqual(inventory.quantity, 100)
        self.assertEqual(inventory.reserved_quantity, 10)

    def test_inventory_sync_records_partial_failure(self):
        inventory_1 = NormalizedInventory(
            external_variant_id="external-variant-001",
            sku="JOB-INV-001",
            quantity=100,
            reserved_quantity=10,
        )

        inventory_2 = NormalizedInventory(
            external_variant_id="external-variant-002",
            sku="JOB-INV-002",
            quantity=50,
            reserved_quantity=5,
        )

        inventory_3 = NormalizedInventory(
            external_variant_id="external-variant-003",
            sku="JOB-INV-003",
            quantity=75,
            reserved_quantity=0,
        )

        successful_inventory_1 = Inventory.objects.create(
            variant=self.variant,
            store=self.store,
            quantity=100,
            reserved_quantity=10,
        )

        with patch(
            "synchronization.services.inventory_sync_job.fetch_sync_items"
        ) as mock_fetch:
            with patch(
                "synchronization.services.inventory_sync_job.sync_item"
            ) as mock_sync_item:

                mock_fetch.return_value = [
                    inventory_1,
                    inventory_2,
                    inventory_3,
                ]

                mock_sync_item.side_effect = [
                    successful_inventory_1,
                    ValueError("External variant mapping not found"),
                    successful_inventory_1,
                ]

                sync_job = sync_inventory_with_job(self.store)

        self.assertEqual(
            sync_job.status,
            SyncJob.Status.PARTIAL,
        )

        self.assertEqual(sync_job.total_items, 3)
        self.assertEqual(sync_job.processed_items, 3)
        self.assertEqual(sync_job.successful_items, 2)
        self.assertEqual(sync_job.failed_items, 1)

        self.assertIsNotNone(sync_job.completed_at)

        self.assertEqual(
            SyncError.objects.filter(sync_job=sync_job).count(),
            1,
        )

        sync_error = SyncError.objects.get(sync_job=sync_job)

        self.assertEqual(sync_error.entity_type, "inventory")
        self.assertEqual(
            sync_error.entity_id,
            "external-variant-002",
        )
        self.assertEqual(
            sync_error.error_type,
            "ValueError",
        )
        self.assertEqual(
            sync_error.message,
            "External variant mapping not found",
        )