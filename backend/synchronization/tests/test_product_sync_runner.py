from unittest.mock import patch

from django.test import TestCase

from accounts.models import User
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

    def test_sync_products_delegates_to_common_runner(self):
        expected_result = ["product-1", "product-2"]

        with patch(
            "synchronization.services.product_sync_runner.run_sync"
        ) as mock_run_sync:
            mock_run_sync.return_value = expected_result

            result = sync_products(self.store)

        mock_run_sync.assert_called_once_with(
            store=self.store,
            sync_type="products",
        )

        self.assertEqual(result, expected_result)