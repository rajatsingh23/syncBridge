from django.test import TestCase

from accounts.models import User
from stores.models import Integration, Store
from synchronization.models import SyncJob
from synchronization.services.sync_job import (
    complete_sync_job,
    start_sync_job,
)


class SyncJobTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="sync-job-test@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.MOCK
        )

        cls.store = Store.objects.create(
            user=cls.user,
            integration=integration,
            name="Sync Job Test Store",
            external_store_id="sync-job-test-store",
        )

    def test_start_sync_job_creates_running_job(self):
        sync_job = start_sync_job(
            store=self.store,
            sync_type=SyncJob.SyncType.PRODUCTS,
        )

        self.assertEqual(sync_job.store, self.store)
        self.assertEqual(
            sync_job.sync_type,
            SyncJob.SyncType.PRODUCTS,
        )
        self.assertEqual(
            sync_job.status,
            SyncJob.Status.RUNNING,
        )

        self.assertEqual(sync_job.total_items, 0)
        self.assertEqual(sync_job.processed_items, 0)
        self.assertEqual(sync_job.successful_items, 0)
        self.assertEqual(sync_job.failed_items, 0)

        self.assertIsNotNone(sync_job.started_at)
        self.assertIsNone(sync_job.completed_at)

    def test_complete_sync_job_marks_job_completed(self):
        sync_job = start_sync_job(
            store=self.store,
            sync_type=SyncJob.SyncType.PRODUCTS,
        )

        completed_job = complete_sync_job(sync_job)

        self.assertEqual(
            completed_job.status,
            SyncJob.Status.COMPLETED,
        )

        self.assertIsNotNone(completed_job.started_at)
        self.assertIsNotNone(completed_job.completed_at)