def calculate_backoff_delay(retry_number, base_delay=1):
    return base_delay * (2 ** retry_number)