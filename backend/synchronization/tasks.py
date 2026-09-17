from celery import shared_task

from stores.models import Store
from synchronization.services.sync_job_runner import run_sync_job


@shared_task(
        bind=True,
        autoretry_for=(),
        max_retries=3,
)
def run_sync_task(self, store_id, sync_type):
    store = Store.objects.get(id=store_id)
    try:
        sync_job = run_sync_job(
            store=store,
            sync_type=sync_type,
        )
    except Exception as error:
        if getattr(error, "retryable", False):
            raise self.retry(
                exc=error,
                countdown=2,
            )
        raise

    return {
        "sync_job_id": sync_job.id,
        "store_id": store_id,
        "sync_type": sync_type,
        "status": sync_job.status,
        "total_items": sync_job.total_items,
        "processed_items": sync_job.processed_items,
        "successful_items": sync_job.successful_items,
        "failed_items": sync_job.failed_items,
    }