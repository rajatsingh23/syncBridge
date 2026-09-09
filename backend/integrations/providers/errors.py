class ProviderError(Exception):
    """Base exception for provider-related errors."""

    retryable = False


class AuthenticationError(ProviderError):
    """Raised when provider authentication fails."""


class NotFoundError(ProviderError):
    """Raised when a requested provider resource does not exist."""


class RateLimitError(ProviderError):
    """Raised when the provider rate-limits a request."""

    retryable = True


class TemporaryProviderError(ProviderError):
    """Raised for temporary provider failures that may be retried."""

    retryable = True


class ProviderRequestError(ProviderError):
    """Raised for other provider request failures."""