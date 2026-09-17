from unittest.mock import patch

from django.test import TestCase

from accounts.models import User
from integrations.providers.errors import (
    AuthenticationError,
    TemporaryProviderError,
)
from stores.models import Integration, Store
from synchronization.tasks import run_sync_task


class RunSyncTaskTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="task-test@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.MOCK
        )

        cls.store = Store.objects.create(
            user=cls.user,
            integration=integration,
            name="Task Test Store",
            external_store_id="task-test-store",
        )

    @patch("synchronization.tasks.run_sync_job")
    def test_successful_task_returns_sync_job_result(
        self,
        mock_run_sync_job,
    ):
        mock_run_sync_job.return_value = type(
            "SyncJobResult",
            (),
            {
                "id": 123,
                "status": "completed",
                "total_items": 4,
                "processed_items": 4,
                "successful_items": 4,
                "failed_items": 0,
            },
        )()

        result = run_sync_task.apply(
            args=[
                self.store.id,
                "products",
            ]
        )

        self.assertTrue(result.successful())

        self.assertEqual(
            result.result["sync_job_id"],
            123,
        )

        self.assertEqual(
            result.result["status"],
            "completed",
        )

        mock_run_sync_job.assert_called_once_with(
            store=self.store,
            sync_type="products",
        )

    @patch("synchronization.tasks.run_sync_job")
    def test_retryable_error_triggers_retry(
        self,
        mock_run_sync_job,
    ):
        error = TemporaryProviderError(
            "Temporary provider failure"
        )

        mock_run_sync_job.side_effect = error

        result = run_sync_task.apply(
            args=[
                self.store.id,
                "products",
            ],
            throw=False,
        )

        self.assertTrue(result.failed())

        self.assertIsInstance(
            result.result,
            TemporaryProviderError,
        )

        self.assertEqual(
            str(result.result),
            "Temporary provider failure",
        )

        self.assertEqual(
            mock_run_sync_job.call_count,
            4,
        )

    @patch("synchronization.tasks.run_sync_job")
    def test_non_retryable_error_is_not_retried(
        self,
        mock_run_sync_job,
    ):
        error = AuthenticationError(
            "Invalid provider credentials"
        )

        mock_run_sync_job.side_effect = error

        result = run_sync_task.apply(
            args=[
                self.store.id,
                "products",
            ],
            throw=False,
        )

        self.assertTrue(result.failed())

        self.assertIsInstance(
            result.result,
            AuthenticationError,
        )

        self.assertEqual(
            mock_run_sync_job.call_count,
            1,
        )