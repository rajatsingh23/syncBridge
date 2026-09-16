from unittest.mock import patch

from django.test import TestCase

from accounts.models import User
from stores.models import Integration, Store
from synchronization.models import SyncError, SyncJob
from synchronization.services.order_sync_job import sync_orders_with_job


class OrderSyncJobTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="order-job@example.com",
            password="TestPass123",
        )

        self.integration = Integration.objects.get_or_create(
            provider="mock",
            defaults={
                "name": "Mock Store",
            },
        )[0]

        self.store = Store.objects.create(
            user=self.user,
            integration=self.integration,
            name="Test Store",
            external_store_id="store-001",
            credentials={},
        )

    @patch(
        "synchronization.services.order_sync_job.sync_item"
    )
    @patch(
        "synchronization.services.order_sync_job.fetch_sync_items"
    )
    def test_successful_order_sync_job(
        self,
        mock_fetch_sync_items,
        mock_sync_item,
    ):
        items = [
            type("Order", (), {"external_id": "order-001"})(),
            type("Order", (), {"external_id": "order-002"})(),
        ]

        mock_fetch_sync_items.return_value = items

        sync_job = sync_orders_with_job(
            store=self.store,
        )

        self.assertEqual(
            sync_job.status,
            SyncJob.Status.COMPLETED,
        )
        self.assertEqual(sync_job.total_items, 2)
        self.assertEqual(sync_job.processed_items, 2)
        self.assertEqual(sync_job.successful_items, 2)
        self.assertEqual(sync_job.failed_items, 0)

        self.assertEqual(
            SyncError.objects.count(),
            0,
        )

        self.assertEqual(
            mock_sync_item.call_count,
            2,
        )

    @patch(
        "synchronization.services.order_sync_job.sync_item"
    )
    @patch(
        "synchronization.services.order_sync_job.fetch_sync_items"
    )
    def test_partial_failure_records_sync_error(
        self,
        mock_fetch_sync_items,
        mock_sync_item,
    ):
        items = [
            type("Order", (), {"external_id": "order-001"})(),
            type("Order", (), {"external_id": "order-002"})(),
            type("Order", (), {"external_id": "order-003"})(),
        ]

        mock_fetch_sync_items.return_value = items

        def sync_side_effect(*args, **kwargs):
            item = kwargs["item"]

            if item.external_id == "order-002":
                raise ValueError("Order mapping failed.")

            return "synced"

        mock_sync_item.side_effect = sync_side_effect

        sync_job = sync_orders_with_job(
            store=self.store,
        )

        self.assertEqual(
            sync_job.status,
            SyncJob.Status.PARTIAL,
        )
        self.assertEqual(sync_job.total_items, 3)
        self.assertEqual(sync_job.processed_items, 3)
        self.assertEqual(sync_job.successful_items, 2)
        self.assertEqual(sync_job.failed_items, 1)

        self.assertEqual(
            SyncError.objects.count(),
            1,
        )

        sync_error = SyncError.objects.get()

        self.assertEqual(
            sync_error.entity_type,
            "order",
        )
        self.assertEqual(
            sync_error.entity_id,
            "order-002",
        )
        self.assertEqual(
            sync_error.error_type,
            "ValueError",
        )
        self.assertEqual(
            sync_error.message,
            "Order mapping failed.",
        )

        # Most importantly, the other orders continued.
        self.assertEqual(
            mock_sync_item.call_count,
            3,
        )