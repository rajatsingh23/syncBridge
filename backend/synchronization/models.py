from django.db import models
from stores.models import Store

# Create your models here.
class SyncJob(models.Model):
    class SyncType(models.TextChoices):
        PRODUCTS = "products", "Products"
        INVENTORY = "inventory", "Inventory"
        ORDERS = "orders", "Orders"
        FULL = "full", "Full"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        PARTIAL = "partial", "Partial"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="sync_jobs"
    )

    sync_type = models.CharField(
        max_length=20,
        choices=SyncType.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    total_items = models.PositiveIntegerField(default=0)
    processed_items = models.PositiveIntegerField(default=0)
    successful_items = models.PositiveIntegerField(default=0)
    failed_items = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.store} - {self.sync_type} - {self.status}"

class SyncError(models.Model):
    sync_job = models.ForeignKey(
        SyncJob,
        on_delete=models.CASCADE,
        related_name="errors",
    )

    entity_type = models.CharField(max_length=50)

    entity_id = models.CharField(max_length=255)

    error_type = models.CharField(max_length=100)

    status_code = models.PositiveIntegerField(null=True, blank=True)

    message = models.TextField()

    retry_count = models.PositiveIntegerField(default=0)

    resolved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.entity_type} - {self.entity_id} - {self.error_type}"