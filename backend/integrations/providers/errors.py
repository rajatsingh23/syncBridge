class ProviderError(Exception):
    """Base exception for provider-related errors."""

    retryable = False

    def __init__(
            self, 
            message,
            provider=None,
            status_code=None,
            error_code=None,
    ):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.error_code = error_code


class AuthenticationError(ProviderError):
    """Raised when provider authentication fails."""


class NotFoundError(ProviderError):
    """Raised when a requested provider resource does not exist."""


class RateLimitError(ProviderError):
    """Raised when the provider rate-limits a request."""

    retryable = True

    def __init__(
            self,
            message="Provider rate limit exceeded.", 
            retry_after=None,
            provider=None,
            status_code=None,
            error_code=None,
            ):
                super().__init__(
                     message=message,
                     provider=provider,
                     status_code=status_code,
                     error_code=error_code,
                     )
                self.retry_after = retry_after


class TemporaryProviderError(ProviderError):
    """Raised for temporary provider failures that may be retried."""

    retryable = True


class ProviderRequestError(ProviderError):
    """Raised for other provider request failures."""