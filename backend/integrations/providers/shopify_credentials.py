class ShopifyCredentials:
    def __init__(
        self,
        shop_domain,
        access_token,
        refresh_token=None,
        access_token_expires_at=None,
        refresh_token_expires_at=None,
    ):
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.access_token_expires_at = access_token_expires_at
        self.refresh_token_expires_at = refresh_token_expires_at