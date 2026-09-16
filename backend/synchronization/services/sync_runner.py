from integrations.providers.factory import get_provider
from synchronization.models import SyncJob
from synchronization.services.inventory_sync import sync_inventory
from synchronization.services.product_sync import sync_product


def fetch_sync_items(store, sync_type):
    provider = get_provider(store)

    if sync_type == SyncJob.SyncType.PRODUCTS:
        return provider.get_products()

    if sync_type == SyncJob.SyncType.INVENTORY:
        return provider.get_inventory()

    raise ValueError(f"Unsupported sync type: {sync_type}")


def sync_item(store, sync_type, item):
    if sync_type == SyncJob.SyncType.PRODUCTS:
        return sync_product(
            store=store,
            normalized_product=item,
        )

    if sync_type == SyncJob.SyncType.INVENTORY:
        return sync_inventory(
            store=store,
            normalized_inventory=item,
        )

    raise ValueError(f"Unsupported sync type: {sync_type}")


def run_sync(store, sync_type):
    items = fetch_sync_items(
        store=store,
        sync_type=sync_type,
    )

    return [
        sync_item(
            store=store,
            sync_type=sync_type,
            item=item,
        )
        for item in items
    ]