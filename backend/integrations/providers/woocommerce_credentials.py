class WooCommerceCredentials:
    def __init__(self, store_url, consumer_key, consumer_secret):
        self.store_url = store_url.rstrip("/")
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    def validate(self):
        if not self.store_url:
            raise ValueError("WooCommerce store URL is required.")

        if not self.consumer_key:
            raise ValueError("WooCommerce consumer key is required.")

        if not self.consumer_secret:
            raise ValueError("WooCommerce consumer secret is required.")

        return True