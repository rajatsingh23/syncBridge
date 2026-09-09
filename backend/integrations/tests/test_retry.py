from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from unittest.mock import Mock, patch, call
from integrations.retry import calculate_backoff_delay, retry_call
from integrations.providers.errors import (
    AuthenticationError,
    TemporaryProviderError,
    RateLimitError,
)


class BackoffTests(SimpleTestCase):

    def test_first_retry_uses_base_delay(self):
        self.assertEqual(calculate_backoff_delay(0), 1)

    def test_second_retry_doubles_delay(self):
        self.assertEqual(calculate_backoff_delay(1), 2)

    def test_third_retry_doubles_again(self):
        self.assertEqual(calculate_backoff_delay(2), 4)

    def test_custom_base_delay(self):
        self.assertEqual(
            calculate_backoff_delay(2, base_delay=3),
            12,
        )

    def test_fourth_retry_doubles_again(self):
        self.assertEqual(calculate_backoff_delay(3), 8)


class RetryCallTests(SimpleTestCase):

    def test_successful_call_does_not_retry(self):
        operation = Mock(return_value="success")

        result = retry_call(operation)

        self.assertEqual(result, "success")
        operation.assert_called_once_with()

    def test_retryable_error_is_retried(self):
        operation = Mock(
            side_effect=[
                TemporaryProviderError(),
                "success",
            ]
        )

        with patch("integrations.retry.time.sleep") as mock_sleep:
            result = retry_call(operation, max_retries=1)

        self.assertEqual(result, "success")
        self.assertEqual(operation.call_count, 2)
        mock_sleep.assert_called_once_with(1)

    def test_non_retryable_error_is_not_retried(self):
        operation = Mock(
            side_effect=AuthenticationError()
        )

        with patch("integrations.retry.time.sleep") as mock_sleep:
            with self.assertRaises(AuthenticationError):
                retry_call(operation, max_retries=3)

        operation.assert_called_once_with()
        mock_sleep.assert_not_called()

    def test_multiple_retries_use_exponential_backoff(self):
        operation = Mock(
            side_effect=[
                TemporaryProviderError(),
                TemporaryProviderError(),
                TemporaryProviderError(),
                "success",
            ]
        )

        with patch("integrations.retry.time.sleep") as mock_sleep:
            result = retry_call(operation, max_retries=3)

        self.assertEqual(result, "success")
        self.assertEqual(operation.call_count, 4)
        mock_sleep.assert_has_calls(
            [
                call(1),
                call(2),
                call(4),
            ]
        )

    def test_retry_uses_retry_after_when_provided(self):
        error = RateLimitError(retry_after=5)

        operation = Mock(side_effect=[error, "success"])

        with patch("integrations.retry.time.sleep") as mock_sleep:
            result = retry_call(operation)

        self.assertEqual(result, "success")
        mock_sleep.assert_called_once_with(5)

    def test_rate_limit_without_retry_after_uses_exponential_backoff(self):
        error = RateLimitError()

        operation = Mock(side_effect=[error, "success"])

        with patch("integrations.retry.time.sleep") as mock_sleep:
            result = retry_call(operation)

        self.assertEqual(result, "success")
        mock_sleep.assert_called_once_with(1)

    def test_retry_stops_after_max_retries(self):
        error = TemporaryProviderError()

        operation = Mock(side_effect=error)

        with patch("integrations.retry.time.sleep"):
            with self.assertRaises(TemporaryProviderError):
                retry_call(operation, max_retries=3)

        self.assertEqual(operation.call_count, 4)

    def test_zero_max_retries_makes_only_one_attempt(self):
        error = TemporaryProviderError()
        operation = Mock(side_effect=error)

        with patch("integrations.retry.time.sleep") as mock_sleep:
            with self.assertRaises(TemporaryProviderError):
                retry_call(operation, max_retries=0)

        self.assertEqual(operation.call_count, 1)
        mock_sleep.assert_not_called()