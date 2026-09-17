from synchronization.models import SyncJob
from synchronization.services.inventory_sync_job import sync_inventory_with_job
from synchronization.services.order_sync_job import sync_orders_with_job
from synchronization.services.product_sync_job import sync_products_with_job

def run_sync_job(store, sync_type):
    if sync_type == SyncJob.SyncType.PRODUCTS:
        return sync_products_with_job(store)
    
    if sync_type == SyncJob.SyncType.INVENTORY:
        return sync_inventory_with_job(store)

    if sync_type == SyncJob.SyncType.ORDERS:
        return sync_orders_with_job(store)

    raise ValueError(
        f"Unsupported sync type: {sync_type}"
    )