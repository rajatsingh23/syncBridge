from django.db import models
from stores.models import Store
from products.models import Variant


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    external_id = models.CharField(max_length=255)

    customer_name = models.CharField(max_length=255)

    customer_email = models.EmailField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    currency = models.CharField(
        max_length=3,
        default="INR",
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    ordered_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "external_id"],
                name="unique_store_external_order",
            )
        ]

    def __str__(self):
        return f"{self.store} - {self.external_id}"

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    variant = models.ForeignKey(
        Variant,
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    sku = models.CharField(max_length=100)

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    def __str__(self):
        return f"{self.order.external_id} - {self.sku}"