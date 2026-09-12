from django.test import TestCase
from django.urls import reverse


class ShopifyOAuthViewTests(TestCase):

    def test_connect_shopify_stores_state_in_session(self):
        response = self.client.get(
            reverse("shopify-oauth-start"),
            {
                "shop": "example.myshopify.com",
            },
        )

        self.assertEqual(response.status_code, 302)

        state = self.client.session.get("shopify_oauth_state")

        self.assertIsNotNone(state)
        self.assertGreaterEqual(len(state), 32)

    def test_connect_shopify_redirects_to_shopify_authorization(self):
        response = self.client.get(
            reverse("shopify-oauth-start"),
            {
                "shop": "example.myshopify.com",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            response.url.startswith(
                "https://example.myshopify.com/admin/oauth/authorize?"
            )
        )

        self.assertIn("client_id=test-client-id", response.url)
        self.assertIn("scope=read_products%2Cread_inventory", response.url)
        self.assertIn(
            "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fintegrations%2Fshopify%2Fcallback%2F",
            response.url,
        )
        self.assertIn("state=", response.url)

    def test_connect_shopify_rejects_invalid_shop_domain(self):
        response = self.client.get(
            reverse("shopify-oauth-start"),
            {
                "shop": "evil.com",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_connect_shopify_rejects_deceptive_shop_domain(self):
        response = self.client.get(
            reverse("shopify-oauth-start"),
            {
                "shop": "example.myshopify.com.evil.com",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_connect_shopify_accepts_valid_shop_domain(self):
        response = self.client.get(
            reverse("shopify-oauth-start"),
            {
                "shop": "example.myshopify.com",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(
                "https://example.myshopify.com/admin/oauth/authorize?"
            )
        )

    def test_callback_rejects_invalid_state(self):
        session = self.client.session
        session["shopify_oauth_state"] = "expected-state"
        session.save()

        response = self.client.get(
            reverse("shopify-oauth-callback"),
            {
                "shop": "example.myshopify.com",
                "code": "test-code",
                "state": "attacker-state",
            },
        )

        self.assertEqual(response.status_code, 400)