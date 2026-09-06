from .mock import MockProvider

def get_provider(store):
    provider_name = store.integration.provider

    if provider_name == "mock":
        return MockProvider(store)

    raise ValueError(f"Unsupported provider: {provider_name}" )