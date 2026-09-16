from django.utils import timezone

from synchronization.models import SyncError, SyncJob
from synchronization.services.sync_job import (
    complete_sync_job,
    start_sync_job,
)
from synchronization.services.sync_runner import (
    fetch_sync_items,
    sync_item,
)


def sync_orders_with_job(store):
    sync_job = start_sync_job(
        store=store,
        sync_type=SyncJob.SyncType.ORDERS,
    )

    normalized_items = fetch_sync_items(
        store=store,
        sync_type=SyncJob.SyncType.ORDERS,
    )

    sync_job.total_items = len(normalized_items)
    sync_job.save(update_fields=["total_items"])

    for item in normalized_items:
        try:
            sync_item(
                store=store,
                sync_type=SyncJob.SyncType.ORDERS,
                item=item,
            )

            sync_job.processed_items += 1
            sync_job.successful_items += 1

        except Exception as error:
            sync_job.processed_items += 1
            sync_job.failed_items += 1

            SyncError.objects.create(
                sync_job=sync_job,
                entity_type="order",
                entity_id=item.external_id,
                error_type=error.__class__.__name__,
                status_code=getattr(error, "status_code", None),
                message=str(error),
            )

        sync_job.save(
            update_fields=[
                "processed_items",
                "successful_items",
                "failed_items",
            ]
        )

    if sync_job.failed_items == 0:
        complete_sync_job(sync_job)
    else:
        sync_job.status = SyncJob.Status.PARTIAL
        sync_job.completed_at = timezone.now()
        sync_job.save(
            update_fields=[
                "status",
                "completed_at",
            ]
        )

    return sync_job