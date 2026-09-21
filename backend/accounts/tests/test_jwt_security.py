from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class JWTSecurityTests(APITestCase):
    def setUp(self):
        self.email = "jwt-test@example.com"
        self.password = "StrongPassword123!"

        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
        )

    def test_user_can_obtain_jwt_tokens(self):
        response = self.client.post(
            "/api/auth/token/",
            {
                "email": self.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_token_rotation_invalidates_old_token(self):
        token_response = self.client.post(
            "/api/auth/token/",
            {
                "email": self.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            token_response.status_code,
            status.HTTP_200_OK,
        )

        old_refresh_token = token_response.data["refresh"]

        refresh_response = self.client.post(
            "/api/auth/token/refresh/",
            {
                "refresh": old_refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn("access", refresh_response.data)
        self.assertIn("refresh", refresh_response.data)

        new_refresh_token = refresh_response.data["refresh"]

        self.assertNotEqual(
            old_refresh_token,
            new_refresh_token,
        )

        old_token_reuse_response = self.client.post(
            "/api/auth/token/refresh/",
            {
                "refresh": old_refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            old_token_reuse_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        new_token_response = self.client.post(
            "/api/auth/token/refresh/",
            {
                "refresh": new_refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            new_token_response.status_code,
            status.HTTP_200_OK,
        )