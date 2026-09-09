from django.test import SimpleTestCase

from integrations.providers.errors import ProviderError, RateLimitError

class ProviderErrorTests(SimpleTestCase):

    def test_provider_error_stores_structured_details(self):
        error = ProviderError(
            message="Something went wrong",
            provider="mock",
            status_code=500,
            error_code="SERVER_ERROR",
        )

        self.assertEqual(str(error), "Something went wrong")
        self.assertEqual(error.provider, "mock")
        self.assertEqual(error.status_code, 500)
        self.assertEqual(error.error_code, "SERVER_ERROR")

    def test_rate_limit_error_stores_structured_details(self):
        error = RateLimitError(
            message="Too many requests",
            provider="mock",
            status_code=429,
            error_code="RATE_LIMITED",
            retry_after=5,
        )

        self.assertEqual(str(error), "Too many requests")
        self.assertEqual(error.provider, "mock")
        self.assertEqual(error.status_code, 429)
        self.assertEqual(error.error_code, "RATE_LIMITED")
        self.assertEqual(error.retry_after, 5)