from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from profile_app.tests.helpers import authenticate, create_user
from reviews_app.models import Review


class ReviewTestCase(APITestCase):
    """Common setup with a business user and two customers."""

    def setUp(self):
        self.business = create_user("business", "business")
        self.customer = create_user("customer", "customer")
        self.other_customer = create_user("other", "customer")
        self.review = Review.objects.create(
            business_user=self.business, reviewer=self.other_customer,
            rating=4, description="Gut",
        )
        self.url = reverse("review-detail", kwargs={"pk": self.review.id})
        authenticate(self.client, self.customer)


class ReviewCreateListTests(ReviewTestCase):
    """Tests for creating and listing reviews."""

    def post_review(self, business_user=None):
        payload = {"business_user": (business_user or self.business).id,
                   "rating": 5, "description": "Top"}
        return self.client.post(reverse("review-list"), payload)

    def test_customer_can_create_review(self):
        response = self.post_review()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["reviewer"], self.customer.id)

    def test_second_review_for_same_business_fails(self):
        self.post_review()
        response = self.post_review()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_business_user_cannot_create_review(self):
        authenticate(self.client, self.business)
        response = self.post_review()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_review_for_customer_fails(self):
        response = self.post_review(business_user=self.other_customer)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_filters_and_ordering(self):
        url = reverse("review-list")
        response = self.client.get(
            url, {"business_user_id": self.business.id, "ordering": "rating"}
        )
        self.assertEqual(len(response.data), 1)
        response = self.client.get(url, {"reviewer_id": self.customer.id})
        self.assertEqual(len(response.data), 0)

    def test_invalid_filter_returns_400(self):
        params = {"reviewer_id": "x"}
        response = self.client.get(reverse("review-list"), params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_requires_authentication(self):
        self.client.credentials()
        response = self.client.get(reverse("review-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReviewUpdateDeleteTests(ReviewTestCase):
    """Tests for updating and deleting reviews."""

    def test_author_can_update_review(self):
        authenticate(self.client, self.other_customer)
        payload = {"rating": 5, "description": "Noch besser"}
        response = self.client.patch(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rating"], 5)

    def test_update_of_other_fields_fails(self):
        authenticate(self.client, self.other_customer)
        payload = {"business_user": self.customer.id}
        response = self.client.patch(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_user_cannot_update_or_delete(self):
        response = self.client.patch(self.url, {"rating": 1})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_delete_review(self):
        authenticate(self.client, self.other_customer)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_unknown_review_returns_404(self):
        url = reverse("review-detail", kwargs={"pk": 999})
        self.assertEqual(self.client.delete(url).status_code, 404)

    def test_review_str(self):
        self.assertEqual(str(self.review), "other -> business: 4")
