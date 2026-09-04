from django.conf import settings
from django.db import models


class Integration(models.Model):
    class Provider(models.TextChoices):
        MOCK = "mock", "Mock Store"
        SHOPIFY = "shopify", "Shopify"
        WOOCOMMERCE = "woocommerce", "WooCommerce"

    name = models.CharField(max_length=100)
    provider = models.CharField(
        max_length=50,
        choices=Provider.choices,
        unique=True,
    )

    def __str__(self):
        return self.name


class Store(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        ERROR = "error", "Error"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stores",
    )

    integration = models.ForeignKey(
        Integration,
        on_delete=models.PROTECT,
        related_name="stores",
    )

    name = models.CharField(max_length=255)
    external_store_id = models.CharField(max_length=255)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    credentials = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name