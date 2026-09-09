from django.test import SimpleTestCase

from integrations.providers.errors import (
    AuthenticationError,
    NotFoundError,
    ProviderError,
    ProviderRequestError,
    RateLimitError,
    TemporaryProviderError,
)


class ProviderErrorTests(SimpleTestCase):

    def test_base_provider_error_is_not_retryable(self):
        self.assertFalse(ProviderError.retryable)

    def test_authentication_error_is_not_retryable(self):
        self.assertFalse(AuthenticationError.retryable)

    def test_not_found_error_is_not_retryable(self):
        self.assertFalse(NotFoundError.retryable)

    def test_rate_limit_error_is_retryable(self):
        self.assertTrue(RateLimitError.retryable)

    def test_temporary_provider_error_is_retryable(self):
        self.assertTrue(TemporaryProviderError.retryable)

    def test_provider_request_error_is_not_retryable(self):
        self.assertFalse(ProviderRequestError.retryable)