from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from accounts.models import User
from integrations.providers.schemas import (
    NormalizedProduct,
    NormalizedVariant,
)
from products.models import Product, Variant
from stores.models import Integration, Store
from synchronization.models import SyncJob
from synchronization.services.product_sync_job import sync_products_with_job


class ProductSyncJobTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="product-job-test@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.MOCK
        )

        cls.store = Store.objects.create(
            user=cls.user,
            integration=integration,
            name="Product Job Test Store",
            external_store_id="product-job-test-store",
        )

    def test_product_sync_creates_and_completes_sync_job(self):
        normalized_products = [
            NormalizedProduct(
                external_id="job-product-001",
                title="Black T-Shirt",
                description="Black cotton t-shirt",
                variants=[
                    NormalizedVariant(
                        external_id="job-variant-001",
                        sku="JOB-BLK-M",
                        price=Decimal("499.00"),
                        currency="INR",
                    )
                ],
            ),
            NormalizedProduct(
                external_id="job-product-002",
                title="White T-Shirt",
                description="White cotton t-shirt",
                variants=[
                    NormalizedVariant(
                        external_id="job-variant-002",
                        sku="JOB-WHT-M",
                        price=Decimal("599.00"),
                        currency="INR",
                    )
                ],
            ),
        ]

        with patch(
            "synchronization.services.product_sync_job.get_provider"
        ) as mock_get_provider:
            mock_provider = mock_get_provider.return_value
            mock_provider.get_products.return_value = normalized_products

            sync_job = sync_products_with_job(self.store)

        self.assertEqual(
            sync_job.status,
            SyncJob.Status.COMPLETED,
        )

        self.assertEqual(sync_job.total_items, 2)
        self.assertEqual(sync_job.processed_items, 2)
        self.assertEqual(sync_job.successful_items, 2)
        self.assertEqual(sync_job.failed_items, 0)

        self.assertIsNotNone(sync_job.started_at)
        self.assertIsNotNone(sync_job.completed_at)

        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(Variant.objects.count(), 2)

        mock_get_provider.assert_called_once_with(self.store)
        mock_provider.get_products.assert_called_once_with()