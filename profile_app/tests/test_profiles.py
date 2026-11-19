from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from profile_app.models import Profile

from .helpers import authenticate, create_user


class ProfileDetailTests(APITestCase):
    """Tests for retrieving and updating a single profile."""

    def setUp(self):
        self.business = create_user("business", "business")
        self.customer = create_user("customer", "customer")
        self.url = reverse("profile-detail", kwargs={"pk": self.business.id})

    def test_get_profile_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_returns_empty_strings(self):
        authenticate(self.client, self.customer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], self.business.id)
        self.assertEqual(response.data["location"], "")
        self.assertEqual(response.data["first_name"], "")

    def test_get_unknown_profile_returns_404(self):
        authenticate(self.client, self.customer)
        url = reverse("profile-detail", kwargs={"pk": 999})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_owner_can_update_profile(self):
        authenticate(self.client, self.business)
        payload = {"first_name": "Max", "location": "Berlin",
                   "email": "max@business.de"}
        response = self.client.patch(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.business.refresh_from_db()
        self.assertEqual(self.business.first_name, "Max")
        self.assertEqual(self.business.email, "max@business.de")
        self.assertEqual(response.data["location"], "Berlin")

    def test_other_user_cannot_update_profile(self):
        authenticate(self.client, self.customer)
        response = self.client.patch(self.url, {"location": "Hamburg"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_with_used_email_fails(self):
        authenticate(self.client, self.business)
        response = self.client.patch(self.url, {"email": "customer@mail.de"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_str(self):
        profile = Profile.objects.get(user=self.business)
        self.assertEqual(str(profile), "business (business)")


class ProfileListTests(APITestCase):
    """Tests for the business and customer profile lists."""

    def setUp(self):
        self.business = create_user("business", "business")
        self.customer = create_user("customer", "customer")
        authenticate(self.client, self.customer)

    def test_business_list_contains_only_business_users(self):
        response = self.client.get(reverse("business-profile-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["type"], "business")

    def test_customer_list_contains_only_customers(self):
        response = self.client.get(reverse("customer-profile-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("uploaded_at", response.data[0])

    def test_lists_require_authentication(self):
        self.client.credentials()
        response = self.client.get(reverse("customer-profile-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
