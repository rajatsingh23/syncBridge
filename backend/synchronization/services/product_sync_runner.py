from integrations.providers.factory import get_provider
from synchronization.services.product_sync import sync_product

def sync_products(store):
    provider = get_provider(store)

    normalized_products = provider.get_products()

    synced_products = []

    for normalized_product in normalized_products:
        product = sync_product(
            store=store,
            normalized_product=normalized_product,
        )

        synced_products.append(product)

    return synced_products