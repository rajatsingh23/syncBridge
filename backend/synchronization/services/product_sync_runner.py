from synchronization.models import SyncJob
from synchronization.services.sync_runner import run_sync

def sync_products(store):
    return run_sync(
        store=store,
        sync_type=SyncJob.SyncType.PRODUCTS,
    )