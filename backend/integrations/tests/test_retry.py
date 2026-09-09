from django.test import SimpleTestCase

from integrations.retry import calculate_backoff_delay


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