from django.db import models
from stores.models import Store

# Create your models here.
class Product(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DRAFT = "draft", "Draft"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=225)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Variant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )

    sku = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    currency = models.CharField(
        max_length = 3,
        default="INR",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.title} - {self.title}"

class Inventory(models.Model):
    variant = models.ForeignKey(
        Variant,
        on_delete=models.CASCADE,
        related_name="inventory_records",
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="inventory_records",
    )

    quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["variant", "store"],
                name="unique_variant_store_inventory",
            )
        ]

    def __str__(self):
        return f"{self.variant} - {self.store}: {self.quantity}"

class ExternalProduct(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="external_products",
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="external_products",
    )

    external_id = models.CharField(max_length=255)

    external_data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "external_id"],
                name="unique_store_external_product",
            )
        ]

    def __str__(self):
        return f"{self.store} - {self.external_id}"

class ExternalVariant(models.Model):
    variant = models.ForeignKey(
        Variant,
        on_delete=models.CASCADE,
        related_name="external_variants",
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="external_variants",
    )

    external_id = models.CharField(max_length=255)

    external_data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "external_id"],
                name="unique_store_external_variant",
            )
        ]

    def __str__(self):
        return f"{self.store} - {self.external_id}"