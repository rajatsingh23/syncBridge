from django.utils import timezone

from synchronization.models import SyncJob

def start_sync_job(store, sync_type):
    return SyncJob.objects.create(
        store=store,
        sync_type=sync_type,
        status=SyncJob.Status.RUNNING,
        total_items=0,
        processed_items=0,
        successful_items=0,
        failed_items=0,
    )

def complete_sync_job(sync_job):
    sync_job.status = SyncJob.Status.COMPLETED
    sync_job.completed_at = timezone.now()

    sync_job.save(
        update_fields=[
            "status",
            "completed_at",
        ]
    )
    return sync_job