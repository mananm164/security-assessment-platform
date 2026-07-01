from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class AuthEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.email = "consultant@sarp.local"
        self.password = "test-pass-12345"
        self.user = get_user_model().objects.create_user(
            email=self.email,
            password=self.password,
            first_name="Test",
            last_name="Consultant",
            role=get_user_model().Role.CONSULTANT,
        )

    def test_health_returns_200_without_token(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_me_returns_401_without_token(self):
        response = self.client.get(reverse("auth_me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_credentials_return_access_and_refresh_tokens(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": self.email, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_invalid_credentials_return_generic_authentication_failure(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "missing@sarp.local", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json()["detail"],
            "Unable to authenticate with the provided credentials.",
        )

    def test_valid_access_token_returns_current_user(self):
        token_response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": self.email, "password": self.password},
            format="json",
        )
        access_token = token_response.json()["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(reverse("auth_me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["email"], self.email)
        self.assertEqual(response.json()["role"], get_user_model().Role.CONSULTANT)

    def test_malformed_access_token_is_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer not-a-valid-token")
        response = self.client.get(reverse("auth_me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
