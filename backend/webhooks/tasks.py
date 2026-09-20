from celery import shared_task
from django.utils import timezone
import logging
from webhooks.models import WebhookEvent

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_webhook_event(self, webhook_event_id):
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

    except Exception as error:
        if self.request.retries < self.max_retries:
            logger.warning(
                "Webhook processing failed; retrying.",
                extra={
                    "webhook_event_id": webhook_event.id,
                    "store_id": webhook_event.store_id,
                    "event_type": webhook_event.event_type,
                    "retry_attempt": self.request.retries + 1,
                    "max_retries": self.max_retries,
                    "error": str(error),
                },
            )
            raise self.retry(
                exc=error,
                countdown=2,
            )
        logger.error(
            "Webhook processing failed permanently.",
            extra={
                "webhook_event_id": webhook_event.id,
                "store_id": webhook_event.store_id,
                "event_type": webhook_event.event_type,
                "retry_attempt": self.request.retries,
                "max_retries": self.max_retries,
                "error": str(error),
            }
        )
        webhook_event.status = WebhookEvent.Status.FAILED
        webhook_event.save(
            update_fields=["status"],
        )

        raise

    return {
        "webhook_event_id": webhook_event.id,
        "status": webhook_event.status,
    }