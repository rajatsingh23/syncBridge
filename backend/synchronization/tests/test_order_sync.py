from datetime import datetime, timezone
from decimal import Decimal

from django.test import TestCase

from accounts.models import User
from orders.models import Order, OrderItem
from products.models import ExternalVariant, Product, Variant
from stores.models import Integration, Store

from integrations.providers.schemas import (
    NormalizedOrder,
    NormalizedOrderItem,
)

from synchronization.services.order_sync import sync_order


class OrderSyncTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="order-sync@example.com",
            password="TestPass123",
        )

        self.integration = Integration.objects.get_or_create(
            provider="mock",
            defaults={
                "name": "Mock Store",
            }
        )[0]

        self.store = Store.objects.create(
            user=self.user,
            integration=self.integration,
            name="Test Store",
            external_store_id="store-001",
            credentials={},
        )

        self.product = Product.objects.create(
            owner=self.user,
            title="Test Product",
            description="Test description",
        )

        self.variant = Variant.objects.create(
            product=self.product,
            sku="SKU-001",
            title="Test Variant",
            price=Decimal("999.00"),
            currency="INR",
        )

        self.external_variant = ExternalVariant.objects.create(
            variant=self.variant,
            store=self.store,
            external_id="external-variant-001",
        )

    def build_order(self, quantity=2, total="1998.00"):
        return NormalizedOrder(
            external_id="order-001",
            customer_name="Test Customer",
            customer_email="test@example.com",
            status="paid",
            total_amount=Decimal(total),
            currency="INR",
            ordered_at=datetime(
                2026,
                9,
                16,
                10,
                30,
                tzinfo=timezone.utc,
            ),
            items=[
                NormalizedOrderItem(
                    external_variant_id="external-variant-001",
                    sku="SKU-001",
                    quantity=quantity,
                    unit_price=Decimal("999.00"),
                )
            ],
        )

    def test_first_sync_creates_order_and_items(self):
        normalized_order = self.build_order()

        order = sync_order(
            store=self.store,
            normalized_order=normalized_order,
        )

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

        self.assertEqual(order.external_id, "order-001")
        self.assertEqual(order.customer_name, "Test Customer")
        self.assertEqual(
            order.customer_email,
            "test@example.com",
        )
        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )
        self.assertEqual(
            order.total_amount,
            Decimal("1998.00"),
        )

        item = order.items.get()

        self.assertEqual(item.variant, self.variant)
        self.assertEqual(item.sku, "SKU-001")
        self.assertEqual(item.quantity, 2)
        self.assertEqual(
            item.unit_price,
            Decimal("999.00"),
        )

    def test_second_sync_does_not_create_duplicates(self):
        normalized_order = self.build_order()

        sync_order(
            store=self.store,
            normalized_order=normalized_order,
        )

        sync_order(
            store=self.store,
            normalized_order=normalized_order,
        )

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

    def test_second_sync_updates_existing_order_and_item(self):
        first_order = self.build_order(
            quantity=2,
            total="1998.00",
        )

        sync_order(
            store=self.store,
            normalized_order=first_order,
        )

        updated_order = self.build_order(
            quantity=5,
            total="4995.00",
        )

        updated_order.customer_name = "Updated Customer"
        updated_order.customer_email = "updated@example.com"
        updated_order.status = "processing"

        order = sync_order(
            store=self.store,
            normalized_order=updated_order,
        )

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

        order.refresh_from_db()

        self.assertEqual(
            order.customer_name,
            "Updated Customer",
        )
        self.assertEqual(
            order.customer_email,
            "updated@example.com",
        )
        self.assertEqual(
            order.status,
            Order.Status.CONFIRMED,
        )
        self.assertEqual(
            order.total_amount,
            Decimal("4995.00"),
        )

        item = order.items.get()

        self.assertEqual(item.quantity, 5)

    def test_missing_external_variant_mapping_raises_error(self):
        normalized_order = self.build_order()

        normalized_order.items[0].external_variant_id = (
            "missing-variant"
        )

        with self.assertRaisesMessage(
            ValueError,
            "External variant mapping not found: missing-variant",
        ):
            sync_order(
                store=self.store,
                normalized_order=normalized_order,
            )

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)