from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from integrations.providers.shopify_credentials import ShopifyCredentials

from stores.models import Integration, Store

class ShopifyCredentialsTests(TestCase):
    def test_credentials_store_access_and_refresh_tokens(self):
        credentials = ShopifyCredentials(
            shop_domain="example.myshopify.com",
            access_token="access-token",
            refresh_token="refresh-token",
        )

        self.assertEqual(credentials.shop_domain, "example.myshopify.com")
        self.assertEqual(credentials.access_token, "access-token")
        self.assertEqual(credentials.refresh_token, "refresh-token")

    def test_credentials_store_token_expiry(self):
        access_token_expires_at = timezone.now() + timedelta(hours=1)
        refresh_token_expires_at = timezone.now() + timedelta(days=90)

        credentials = ShopifyCredentials(
            shop_domain="example.myshopify.com",
            access_token="access-token",
            refresh_token="refresh-token",
            access_token_expires_at=access_token_expires_at,
            refresh_token_expires_at=refresh_token_expires_at,
        )

        self.assertEqual(
            credentials.access_token_expires_at,
            access_token_expires_at,
        )
        self.assertEqual(
            credentials.refresh_token_expires_at,
            refresh_token_expires_at,
        )

    def test_shopify_credentials_can_be_persisted_on_store(self):
        user = get_user_model().objects.create_user(
            email="shopify@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.SHOPIFY
        )

        store = Store.objects.create(
            user=user,
            integration=integration,
            name="My Shopify Store",
            external_store_id="example.myshopify.com",
            credentials={
                "shop_domain": "example.myshopify.com",
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "access_token_expires_at": "2026-09-13T13:00:00+00:00",
                "refresh_token_expires_at": "2026-12-12T12:00:00+00:00",
            },
        )

        store.refresh_from_db()

        self.assertEqual(
            store.credentials["shop_domain"],
            "example.myshopify.com",
        )
        self.assertEqual(
            store.credentials["access_token"],
            "access-token",
        )
        self.assertEqual(
            store.credentials["refresh_token"],
            "refresh-token",
        )

    def test_shopify_credentials_are_not_exposed_by_store_api(self):
        user = get_user_model().objects.create_user(
            email="shopify-api@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.SHOPIFY
        )

        Store.objects.create(
            user=user,
            integration=integration,
            name="My Shopify Store",
            external_store_id="example.myshopify.com",
            credentials={
                "shop_domain": "example.myshopify.com",
                "access_token": "secret-access-token",
                "refresh_token": "secret-refresh-token",
                "access_token_expires_at": "2026-09-13T13:00:00+00:00",
                "refresh_token_expires_at": "2026-12-12T12:00:00+00:00",
            },
        )

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/stores/")

        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        self.assertNotIn("credentials", response_data[0])
        self.assertNotIn("secret-access-token", response.content.decode())
        self.assertNotIn("secret-refresh-token", response.content.decode())