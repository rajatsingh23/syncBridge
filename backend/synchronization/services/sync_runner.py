from integrations.providers.factory import get_provider
from synchronization.models import SyncJob
from synchronization.services.inventory_sync import sync_inventory
from synchronization.services.product_sync import sync_product


def run_sync(store, sync_type):
    provider = get_provider(store)

    if sync_type == SyncJob.SyncType.PRODUCTS:
        normalized_items = provider.get_products()

        return [
            sync_product(
                store=store,
                normalized_product=item,
            )
            for item in normalized_items
        ]

    if sync_type == SyncJob.SyncType.INVENTORY:
        normalized_items = provider.get_inventory()

        return [
            sync_inventory(
                store=store,
                normalized_inventory=item,
            )
            for item in normalized_items
        ]

    raise ValueError(f"Unsupported sync type: {sync_type}")