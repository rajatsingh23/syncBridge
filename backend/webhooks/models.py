from django.db import models
from stores.models import Store


class WebhookEvent(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        PROCESSING = "processing", "Processing"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="webhook_events",
    )

    event_id = models.CharField(max_length=255)

    event_type = models.CharField(max_length=100)

    payload = models.JSONField(default=dict)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED,
    )

    received_at = models.DateTimeField(auto_now_add=True)

    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "event_id"],
                name="unique_store_webhook_event",
            )
        ]

    def __str__(self):
        return f"{self.store} - {self.event_type} - {self.event_id}"