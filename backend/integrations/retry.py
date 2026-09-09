import time
from integrations.providers.errors import ProviderError

def calculate_backoff_delay(retry_number, base_delay=1):
    return base_delay * (2 ** retry_number)

def retry_call(operation, max_retries=3, base_delay=1):
    for retry_number in range(max_retries + 1):
        try:
            return operation()
        except ProviderError as error:
            if not error.retryable:
                raise

            if retry_number == max_retries:
                raise

            delay = calculate_backoff_delay(retry_number, base_delay)
            time.sleep(delay)