from .mock import MockProvider
from .shopify_provider import ShopifyProvider
from .woocommerce_provider import WooCommerceProvider

def get_provider(store):
    provider_name = store.integration.provider

    if provider_name == "mock":
        return MockProvider(store)

    if provider_name == "shopify":
        return ShopifyProvider(store)

    if provider_name == "woocommerce":
        return WooCommerceProvider(store)

    raise ValueError(f"Unsupported provider: {provider_name}" )