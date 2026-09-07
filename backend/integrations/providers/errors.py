class ProviderError(Exception):
    """Base exception for provider-related errors."""


class AuthenticationError(ProviderError):
    """Raised when provider authentication fails."""


class NotFoundError(ProviderError):
    """Raised when a requested provider resource does not exist."""


class RateLimitError(ProviderError):
    """Raised when the provider rate-limits a request."""


class TemporaryProviderError(ProviderError):
    """Raised for temporary provider failures that may be retried."""


class ProviderRequestError(ProviderError):
    """Raised for other provider request failures."""