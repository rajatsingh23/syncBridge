from integrations.providers.factory import get_provider
from synchronization.models import SyncJob
from synchronization.services.product_sync import sync_product
from synchronization.services.sync_job import (
    complete_sync_job,
    start_sync_job
)

def sync_products_with_job(store):
    sync_job = start_sync_job(
        store=store,
        sync_type=SyncJob.SyncType.PRODUCTS,
    )

    provider = get_provider(store)
    normalized_products = provider.get_products()

    sync_job.total_items = len(normalized_products)
    sync_job.save(update_fields=["total_items"])

    for normalized_product in normalized_products:
        sync_product(
            store=store,
            normalized_product=normalized_product,
        )

        sync_job.processed_items += 1
        sync_job.successful_items += 1
        sync_job.save(
            update_fields=[
                "processed_items",
                "successful_items"
            ]
        )

    complete_sync_job(sync_job)

    return sync_job