from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from offers_app.models import Offer
from profile_app.tests.helpers import create_user
from reviews_app.models import Review


class BaseInfoTests(APITestCase):
    """Tests for the platform statistics endpoint."""

    def test_empty_platform(self):
        response = self.client.get(reverse("base-info"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["average_rating"], 0)

    def test_statistics(self):
        business = create_user("business", "business")
        customer = create_user("customer", "customer")
        other = create_user("other", "customer")
        Offer.objects.create(user=business, title="Logo")
        for reviewer, rating in ((customer, 4), (other, 5)):
            Review.objects.create(
                business_user=business, reviewer=reviewer, rating=rating
            )
        response = self.client.get(reverse("base-info"))
        self.assertEqual(response.data, {
            "review_count": 2,
            "average_rating": 4.5,
            "business_profile_count": 1,
            "offer_count": 1,
        })
