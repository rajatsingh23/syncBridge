from django.db import transaction

from orders.models import Order, OrderItem
from products.models import ExternalVariant


def normalize_order_status(status):
    status = (status or "").lower()

    status_map = {
        "pending": Order.Status.PENDING,
        "awaiting_payment": Order.Status.PENDING,
        "on-hold": Order.Status.PENDING,

        "paid": Order.Status.CONFIRMED,
        "processing": Order.Status.CONFIRMED,
        "confirmed": Order.Status.CONFIRMED,

        "shipped": Order.Status.SHIPPED,

        "completed": Order.Status.DELIVERED,
        "delivered": Order.Status.DELIVERED,

        "cancelled": Order.Status.CANCELLED,
        "canceled": Order.Status.CANCELLED,
        "refunded": Order.Status.CANCELLED,
        "failed": Order.Status.CANCELLED,
    }

    return status_map.get(status, Order.Status.PENDING)


@transaction.atomic
def sync_order(store, normalized_order):
    order, created = Order.objects.get_or_create(
        store=store,
        external_id=normalized_order.external_id,
        defaults={
            "customer_name": normalized_order.customer_name,
            "customer_email": normalized_order.customer_email,
            "status": normalize_order_status(normalized_order.status),
            "total_amount": normalized_order.total_amount,
            "currency": normalized_order.currency,
            "ordered_at": normalized_order.ordered_at,
        },
    )

    if not created:
        order.customer_name = normalized_order.customer_name
        order.customer_email = normalized_order.customer_email
        order.status = normalize_order_status(normalized_order.status)
        order.total_amount = normalized_order.total_amount
        order.currency = normalized_order.currency
        order.ordered_at = normalized_order.ordered_at

        order.save(
            update_fields=[
                "customer_name",
                "customer_email",
                "status",
                "total_amount",
                "currency",
                "ordered_at",
                "updated_at",
            ]
        )

    for normalized_item in normalized_order.items:
        external_variant = (
            ExternalVariant.objects
            .select_related("variant")
            .filter(
                store=store,
                external_id=normalized_item.external_variant_id,
            )
            .first()
        )

        if external_variant is None:
            raise ValueError(
                "External variant mapping not found: "
                f"{normalized_item.external_variant_id}"
            )

        OrderItem.objects.update_or_create(
            order=order,
            variant=external_variant.variant,
            defaults={
                "sku": normalized_item.sku,
                "quantity": normalized_item.quantity,
                "unit_price": normalized_item.unit_price,
            },
        )

    return order