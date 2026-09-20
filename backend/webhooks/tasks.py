from celery import shared_task
from django.utils import timezone

from webhooks.models import WebhookEvent

@shared_task
def process_webhook_event(webhook_event_id):
    webhook_event = WebhookEvent.objects.get(
        id=webhook_event_id,
    )

    if webhook_event.status == WebhookEvent.Status.PROCESSED:
        return {
            "webhook_event_id": webhook_event.id,
            "status": webhook_event.status,
            "message": "Webhook event was already processed.",
        }

    webhook_event.status = WebhookEvent.Status.PROCESSING
    webhook_event.save(
        update_fields=["status"],
    )

    try:
        # Business processing will be added here.
        # For now, we confirm that the event can be processed.
        webhook_event.status = WebhookEvent.Status.PROCESSED
        webhook_event.processed_at = timezone.now()
        webhook_event.save(
            update_fields=["status", "processed_at"],
        )
    except Exception:
        webhook_event.status = WebhookEvent.Status.FAILED
        webhook_event.save(
            update_fields=["status"],
        )
        raise

    return {
        "webhook_event_id": webhook_event.id,
        "status": webhook_event.status,
    }