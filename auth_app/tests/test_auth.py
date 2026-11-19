from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.throttling import ScopedRateThrottle

from profile_app.tests.helpers import create_user


class RegistrationTests(APITestCase):
    """Tests for the registration endpoint."""

    url = reverse("registration")

    def setUp(self):
        cache.clear()

    def get_payload(self, **overrides):
        payload = {
            "username": "newuser",
            "email": "new@mail.de",
            "password": "examplePassword",
            "repeated_password": "examplePassword",
            "type": "customer",
        }
        payload.update(overrides)
        return payload

    def test_registration_creates_user_and_profile(self):
        response = self.client.post(self.url, self.get_payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            set(response.data), {"token", "username", "email", "user_id"}
        )
        user = User.objects.get(username="newuser")
        self.assertEqual(user.profile.type, "customer")

    def test_registration_with_different_passwords_fails(self):
        payload = self.get_payload(repeated_password="other")
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_with_used_email_fails(self):
        create_user("existing", "customer")
        payload = self.get_payload(email="existing@mail.de")
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_with_invalid_type_fails(self):
        response = self.client.post(self.url, self.get_payload(type="x"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    """Tests for the login endpoint."""

    url = reverse("login")

    def setUp(self):
        cache.clear()
        self.user = create_user("loginuser", "business")

    def test_login_returns_token(self):
        payload = {"username": "loginuser", "password": "testpass123"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user_id"], self.user.id)
        self.assertIn("token", response.data)

    def test_login_with_wrong_password_fails(self):
        payload = {"username": "loginuser", "password": "wrong"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch.object(
        ScopedRateThrottle, "THROTTLE_RATES", {"login": "5/minute"}
    )
    def test_too_many_login_attempts_are_throttled(self):
        payload = {"username": "loginuser", "password": "wrong"}
        for _ in range(5):
            self.client.post(self.url, payload)
        response = self.client.post(self.url, payload)
        self.assertEqual(
            response.status_code, status.HTTP_429_TOO_MANY_REQUESTS
        )


class GuestUserCommandTests(APITestCase):
    """Tests for the create_guest_users management command."""

    def test_command_creates_guest_users_once(self):
        call_command("create_guest_users", stdout=StringIO())
        call_command("create_guest_users", stdout=StringIO())
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(
            User.objects.get(username="kevin").profile.type, "business"
        )
