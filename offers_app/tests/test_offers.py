from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from offers_app.models import Offer, OfferDetail
from profile_app.tests.helpers import authenticate, create_user


def detail_payload(offer_type, price, days):
    """Return the request data of one offer detail."""
    return {
        "title": f"{offer_type} package",
        "revisions": 2,
        "delivery_time_in_days": days,
        "price": price,
        "features": ["Logo Design"],
        "offer_type": offer_type,
    }


def offer_payload(title="Grafikdesign-Paket"):
    """Return the request data of a complete offer."""
    return {
        "title": title,
        "description": "Ein umfassendes Paket.",
        "details": [
            detail_payload("basic", 100, 5),
            detail_payload("standard", 200, 7),
            detail_payload("premium", 500, 10),
        ],
    }


class OfferTestCase(APITestCase):
    """Common setup for the offer tests."""

    def setUp(self):
        self.business = create_user("business", "business")
        self.other_business = create_user("other", "business")
        self.customer = create_user("customer", "customer")
        authenticate(self.client, self.business)
        response = self.client.post(
            reverse("offer-list"), offer_payload(), format="json"
        )
        self.offer = Offer.objects.get(pk=response.data["id"])
        self.detail_url = reverse("offer-detail", kwargs={"pk": self.offer.id})


class OfferCreateTests(OfferTestCase):
    """Tests for creating offers."""

    def test_business_user_can_create_offer(self):
        response = self.client.post(
            reverse("offer-list"), offer_payload("Neu"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["details"]), 3)
        self.assertEqual(response.data["details"][0]["price"], 100)

    def test_customer_cannot_create_offer(self):
        authenticate(self.client, self.customer)
        response = self.client.post(
            reverse("offer-list"), offer_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_create_offer(self):
        self.client.credentials()
        response = self.client.post(
            reverse("offer-list"), offer_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_offer_needs_three_details(self):
        payload = offer_payload()
        payload["details"] = payload["details"][:2]
        response = self.client.post(
            reverse("offer-list"), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_offer_without_details_fails(self):
        payload = {"title": "Ohne Details"}
        response = self.client.post(
            reverse("offer-list"), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_offer_types_fail(self):
        payload = offer_payload()
        payload["details"][1]["offer_type"] = "basic"
        response = self.client.post(
            reverse("offer-list"), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_detail_values_fail(self):
        payload = offer_payload()
        payload["details"][0].update(
            {"revisions": -2, "delivery_time_in_days": 0, "features": [1]}
        )
        response = self.client.post(
            reverse("offer-list"), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data["details"][0]
        self.assertEqual(
            set(errors), {"revisions", "delivery_time_in_days", "features"}
        )


class OfferListTests(OfferTestCase):
    """Tests for the paginated and filtered offer list."""

    def test_list_is_public_and_paginated(self):
        self.client.credentials()
        response = self.client.get(reverse("offer-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        offer = response.data["results"][0]
        self.assertEqual(offer["min_price"], 100)
        self.assertEqual(offer["min_delivery_time"], 5)
        self.assertEqual(offer["user_details"]["username"], "business")
        url = offer["details"][0]["url"]
        self.assertTrue(url.startswith("/offerdetails/"))

    def test_list_filters(self):
        url = reverse("offer-list")
        cases = [
            ({"creator_id": self.other_business.id}, 0),
            ({"min_price": 150}, 0),
            ({"max_delivery_time": 4}, 0),
            ({"search": "grafik"}, 1),
            ({"search": "nichts"}, 0),
            ({"ordering": "-min_price", "creator_id": ""}, 1),
        ]
        for params, expected in cases:
            response = self.client.get(url, params)
            self.assertEqual(response.data["count"], expected, params)

    def test_invalid_filter_returns_400(self):
        response = self.client.get(reverse("offer-list"), {"min_price": "x"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OfferRetrieveTests(OfferTestCase):
    """Tests for single offers and offer details."""

    def test_retrieve_offer_has_absolute_detail_urls(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = response.data["details"][0]["url"]
        self.assertTrue(url.startswith("http://testserver/api/offerdetails/"))

    def test_retrieve_offer_requires_authentication(self):
        self.client.credentials()
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_unknown_offer_returns_404(self):
        url = reverse("offer-detail", kwargs={"pk": 999})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_retrieve_offer_detail(self):
        detail = self.offer.details.get(offer_type="basic")
        url = reverse("offerdetail-detail", kwargs={"pk": detail.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["offer_type"], "basic")

    def test_str_methods(self):
        detail = self.offer.details.get(offer_type="basic")
        self.assertEqual(str(self.offer), "Grafikdesign-Paket")
        self.assertEqual(str(detail), "Grafikdesign-Paket - basic")


class OfferUpdateDeleteTests(OfferTestCase):
    """Tests for updating and deleting offers."""

    def test_owner_can_update_offer_and_detail(self):
        basic = self.offer.details.get(offer_type="basic")
        payload = {"title": "Updated", "details": [
            {"title": "Basic Updated", "price": 120, "offer_type": "basic"}
        ]}
        response = self.client.patch(self.detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated")
        basic.refresh_from_db()
        self.assertEqual(basic.title, "Basic Updated")
        self.assertEqual(OfferDetail.objects.count(), 3)

    def test_update_detail_without_offer_type_fails(self):
        payload = {"details": [{"price": 120}]}
        response = self.client.patch(self.detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_unknown_offer_type_fails(self):
        self.offer.details.filter(offer_type="premium").delete()
        payload = {"details": [{"price": 1, "offer_type": "premium"}]}
        response = self.client.patch(self.detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_user_cannot_update_or_delete(self):
        authenticate(self.client, self.other_business)
        response = self.client.patch(self.detail_url, {"title": "Hack"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_delete_offer(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Offer.objects.exists())
