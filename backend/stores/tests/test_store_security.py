from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from stores.models import Integration, Store


User = get_user_model()


class StoreSecurityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user1@example.com",
            password="StrongPassword123!",
        )

        self.other_user = User.objects.create_user(
            email="user2@example.com",
            password="StrongPassword123!",
        )

        self.integration, _ = Integration.objects.get_or_create(
            provider=Integration.Provider.MOCK,
            defaults={
                "name": "Mock Integration",
            },
        )

        self.store = Store.objects.create(
            user=self.other_user,
            integration=self.integration,
            name="Other User Store",
            external_store_id="other-store-123",
        )

        self.url = "/api/stores/"

    def test_unauthenticated_user_cannot_access_stores(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_invalid_status_is_rejected(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {
                "name": "Test Store",
                "integration": self.integration.id,
                "external_store_id": "test-store-123",
                "status": "invalid_status",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn("status", response.data)

    def test_missing_required_name_is_rejected(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {
                "integration": self.integration.id,
                "external_store_id": "test-store-123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn("name", response.data)

    def test_user_cannot_access_another_users_store(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f"{self.url}{self.store.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_user_cannot_update_another_users_store(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f"{self.url}{self.store.id}/",
            {
                "name": "Unauthorized Update",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_user_cannot_delete_another_users_store(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(
            f"{self.url}{self.store.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            Store.objects.filter(id=self.store.id).exists()
        )