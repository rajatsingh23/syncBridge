from django.test import TestCase
from django.contrib.auth import get_user_model
from stores.shopify_credentials import ShopifyCredentials
from stores.models import Integration, Store

class ShopifyCredentialsTests(TestCase):
    def test_shopify_credentials_can_be_stored_on_store(self):
        User = get_user_model()

        user = User.objects.create_user(
            email="shopify-test@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.SHOPIFY,
        )

        credentials = ShopifyCredentials(
            shop_domain="example.myshopify.com",
            access_token="test-token",
        )

        store = Store.objects.create(
            user=user,
            integration=integration,
            name="My Shopify Store",
            external_store_id=credentials.shop_domain,
            credentials={
                "shop_domain": credentials.shop_domain,
                "access_token": credentials.access_token,
            },
        )

        self.assertEqual(
            store.credentials["shop_domain"],
            "example.myshopify.com",
        )
        self.assertEqual(
            store.credentials["access_token"],
            "test-token",
        )

    def test_store_api_does_not_expose_credentials(self):
        User = get_user_model()

        user = User.objects.create_user(
            email="shopify-api@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.SHOPIFY,
        )

        Store.objects.create(
            user=user,
            integration=integration,
            name="My Shopify Store",
            external_store_id="example.myshopify.com",
            credentials={
                "shop_domain": "example.myshopify.com",
                "access_token": "secret-test-token",
            },
        )

        from stores.serializers import StoreSerializer

        store = Store.objects.get(name="My Shopify Store")
        data = StoreSerializer(store).data

        self.assertNotIn("credentials", data)
        self.assertNotIn("access_token", str(data))
        self.assertNotIn("secret-test-token", str(data))
    def test_store_api_response_does_not_expose_credentials(self):
        from rest_framework.test import APIClient

        User = get_user_model()

        user = User.objects.create_user(
            email="shopify-api-endpoint@example.com",
            password="TestPass123",
        )

        integration = Integration.objects.get(
            provider=Integration.Provider.SHOPIFY,
        )

        Store.objects.create(
            user=user,
            integration=integration,
            name="My Shopify Store",
            external_store_id="example.myshopify.com",
            credentials={
                "shop_domain": "example.myshopify.com",
                "access_token": "secret-test-token",
            },
        )

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/stores/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("credentials", response.data[0])
        self.assertNotIn("access_token", str(response.data))
        self.assertNotIn("secret-test-token", str(response.data))