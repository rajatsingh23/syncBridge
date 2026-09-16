from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from stores.models import Integration, Store
from synchronization.models import SyncError, SyncJob


class SyncJobAPITests(APITestCase):

    def setUp(self):
        self.user_a = User.objects.create_user(
            email="user-a@example.com",
            password="TestPass123",
        )

        self.user_b = User.objects.create_user(
            email="user-b@example.com",
            password="TestPass123",
        )

        self.integration = Integration.objects.get_or_create(
            provider="mock",
            defaults={
                "name": "Mock Store",
            },
        )[0]

        self.store_a = Store.objects.create(
            user=self.user_a,
            integration=self.integration,
            name="Store A",
            external_store_id="store-a",
            credentials={},
        )

        self.store_b = Store.objects.create(
            user=self.user_b,
            integration=self.integration,
            name="Store B",
            external_store_id="store-b",
            credentials={},
        )

        self.job_a = SyncJob.objects.create(
            store=self.store_a,
            sync_type=SyncJob.SyncType.PRODUCTS,
            status=SyncJob.Status.COMPLETED,
            total_items=10,
            processed_items=10,
            successful_items=10,
            failed_items=0,
        )

        self.job_b = SyncJob.objects.create(
            store=self.store_b,
            sync_type=SyncJob.SyncType.INVENTORY,
            status=SyncJob.Status.PARTIAL,
            total_items=5,
            processed_items=5,
            successful_items=4,
            failed_items=1,
        )

        SyncError.objects.create(
            sync_job=self.job_b,
            entity_type="inventory",
            entity_id="variant-001",
            error_type="ValueError",
            message="Inventory mapping failed.",
        )

    def test_unauthenticated_user_cannot_list_jobs(self):
        response = self.client.get("/api/sync/jobs/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_user_can_list_own_sync_jobs(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get("/api/sync/jobs/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["id"],
            self.job_a.id,
        )

    def test_user_can_retrieve_own_sync_job(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(
            f"/api/sync/jobs/{self.job_a.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.job_a.id,
        )

        self.assertEqual(
            response.data["status"],
            SyncJob.Status.COMPLETED,
        )

    def test_user_cannot_retrieve_another_users_sync_job(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(
            f"/api/sync/jobs/{self.job_b.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_sync_job_includes_errors(self):
        self.client.force_authenticate(user=self.user_b)

        response = self.client.get(
            f"/api/sync/jobs/{self.job_b.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["errors"]),
            1,
        )

        error = response.data["errors"][0]

        self.assertEqual(
            error["entity_type"],
            "inventory",
        )

        self.assertEqual(
            error["entity_id"],
            "variant-001",
        )

        self.assertEqual(
            error["message"],
            "Inventory mapping failed.",
        )

    def test_sync_job_is_read_only(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.patch(
            f"/api/sync/jobs/{self.job_a.id}/",
            {
                "status": SyncJob.Status.FAILED,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )