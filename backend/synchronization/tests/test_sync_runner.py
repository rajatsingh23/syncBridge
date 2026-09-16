from decimal import Decimal
from unittest.mock import patch, Mock

from django.test import TestCase

from accounts.models import User
from integrations.providers.schemas import (
    NormalizedInventory,
    NormalizedProduct,
    NormalizedVariant,
)
from products.models import (
    ExternalVariant,
    Inventory,
    Product,
    Variant,
)
from stores.models import Integration, Store
from synchronization.models import SyncJob
from synchronization.services.sync_runner import run_sync, fetch_sync_items, sync_item


class SyncRunnerTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="sync-runner-test@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.MOCK
        )

        cls.store = Store.objects.create(
            user=cls.user,
            integration=integration,
            name="Sync Runner Test Store",
            external_store_id="sync-runner-test-store",
        )

        cls.product = Product.objects.create(
            owner=cls.user,
            title="Runner Inventory Product",
        )

        cls.variant = Variant.objects.create(
            product=cls.product,
            sku="RUNNER-INV-001",
            title="Runner Inventory Variant",
            price="499.00",
            currency="INR",
        )

        ExternalVariant.objects.create(
            variant=cls.variant,
            store=cls.store,
            external_id="runner-external-variant-001",
        )

    def test_run_sync_products(self):
        normalized_products = [
            NormalizedProduct(
                external_id="runner-product-001",
                title="Runner Product",
                description="Test product",
                variants=[
                    NormalizedVariant(
                        external_id="runner-variant-001",
                        sku="RUNNER-PROD-001",
                        price=Decimal("499.00"),
                        currency="INR",
                    )
                ],
            )
        ]

        with patch(
            "synchronization.services.sync_runner.get_provider"
        ) as mock_get_provider:
            mock_provider = mock_get_provider.return_value
            mock_provider.get_products.return_value = normalized_products

            results = run_sync(
                store=self.store,
                sync_type=SyncJob.SyncType.PRODUCTS,
            )

        mock_get_provider.assert_called_once_with(self.store)
        mock_provider.get_products.assert_called_once_with()

        self.assertEqual(len(results), 1)
        self.assertEqual(Product.objects.count(), 2)

        product = Product.objects.get(
            title="Runner Product"
        )

        self.assertEqual(product.description, "Test product")

    def test_run_sync_inventory(self):
        normalized_inventory = [
            NormalizedInventory(
                external_variant_id="runner-external-variant-001",
                sku="RUNNER-INV-001",
                quantity=100,
                reserved_quantity=10,
            )
        ]

        with patch(
            "synchronization.services.sync_runner.get_provider"
        ) as mock_get_provider:
            mock_provider = mock_get_provider.return_value
            mock_provider.get_inventory.return_value = normalized_inventory

            results = run_sync(
                store=self.store,
                sync_type=SyncJob.SyncType.INVENTORY,
            )

        mock_get_provider.assert_called_once_with(self.store)
        mock_provider.get_inventory.assert_called_once_with()

        self.assertEqual(len(results), 1)

        inventory = Inventory.objects.get(
            variant=self.variant,
            store=self.store,
        )

        self.assertEqual(inventory.quantity, 100)
        self.assertEqual(inventory.reserved_quantity, 10)

    def test_unsupported_sync_type_raises_error(self):
        with patch(
            "synchronization.services.sync_runner.get_provider"
        ) as mock_get_provider:
            with self.assertRaises(ValueError) as context:
                run_sync(
                    store=self.store,
                    sync_type="unsupported",
                )

        mock_get_provider.assert_called_once_with(self.store)

        self.assertIn(
            "Unsupported sync type",
            str(context.exception),
        )

    def test_fetch_sync_items_inventory(self):
        normalized_inventory = [
            NormalizedInventory(
                external_variant_id="runner-external-variant-001",
                sku="RUNNER-INV-001",
                quantity=100,
                reserved_quantity=10,
            )
        ]

        with patch(
            "synchronization.services.sync_runner.get_provider"
        ) as mock_get_provider:
            mock_provider = mock_get_provider.return_value
            mock_provider.get_inventory.return_value = normalized_inventory

            result = fetch_sync_items(
                store=self.store,
                sync_type=SyncJob.SyncType.INVENTORY,
            )

        mock_get_provider.assert_called_once_with(self.store)
        mock_provider.get_inventory.assert_called_once_with()

        self.assertEqual(result, normalized_inventory)

    def test_sync_item_inventory(self):
        normalized_inventory = NormalizedInventory(
            external_variant_id="runner-external-variant-001",
            sku="RUNNER-INV-001",
            quantity=100,
            reserved_quantity=10,
        )

        result = sync_item(
            store=self.store,
            sync_type=SyncJob.SyncType.INVENTORY,
            item=normalized_inventory,
        )

        self.assertEqual(result.variant, self.variant)
        self.assertEqual(result.store, self.store)
        self.assertEqual(result.quantity, 100)
        self.assertEqual(result.reserved_quantity, 10)

    @patch("synchronization.services.sync_runner.sync_order")
    def test_sync_item_dispatches_orders(self, mock_sync_order):
        item = Mock()

        mock_sync_order.return_value = "synced-order"

        result = sync_item(
            store=self.store,
            sync_type=SyncJob.SyncType.ORDERS,
            item=item,
        )

        mock_sync_order.assert_called_once_with(
            store=self.store,
            normalized_order=item,
        )

        self.assertEqual(result, "synced-order")

    @patch("synchronization.services.sync_runner.get_provider")
    def test_fetch_sync_items_fetches_orders(
        self,
        mock_get_provider,
    ):
        provider = mock_get_provider.return_value

        provider.get_orders.return_value = [
            "order-1",
            "order-2",
        ]

        result = fetch_sync_items(
            store=self.store,
            sync_type=SyncJob.SyncType.ORDERS,
        )

        provider.get_orders.assert_called_once_with()

        self.assertEqual(
            result,
            ["order-1", "order-2"],
        )