from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from offers_app.models import Offer, OfferDetail
from orders_app.models import Order
from profile_app.tests.helpers import authenticate, create_user


class OrderTestCase(APITestCase):
    """Common setup with a business offer and a customer."""

    def setUp(self):
        self.business = create_user("business", "business")
        self.other_business = create_user("other", "business")
        self.customer = create_user("customer", "customer")
        offer = Offer.objects.create(user=self.business, title="Logo")
        self.detail = OfferDetail.objects.create(
            offer=offer, title="Logo Design", revisions=3,
            delivery_time_in_days=5, price=150,
            features=["Logo Design"], offer_type="basic",
        )
        authenticate(self.client, self.customer)

    def create_order(self):
        response = self.client.post(
            reverse("order-list"), {"offer_detail_id": self.detail.id}
        )
        return Order.objects.get(pk=response.data["id"])


class OrderCreateListTests(OrderTestCase):
    """Tests for creating and listing orders."""

    def test_customer_can_create_order(self):
        response = self.client.post(
            reverse("order-list"), {"offer_detail_id": self.detail.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["business_user"], self.business.id)
        self.assertEqual(response.data["price"], 150)
        self.assertEqual(response.data["status"], "in_progress")

    def test_business_user_cannot_create_order(self):
        authenticate(self.client, self.business)
        response = self.client.post(
            reverse("order-list"), {"offer_detail_id": self.detail.id}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_offer_detail_id_returns_400(self):
        response = self.client.post(reverse("order-list"), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_offer_detail_returns_404(self):
        response = self.client.post(
            reverse("order-list"), {"offer_detail_id": 999}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_contains_only_own_orders(self):
        self.create_order()
        response = self.client.get(reverse("order-list"))
        self.assertEqual(len(response.data), 1)
        authenticate(self.client, self.other_business)
        response = self.client.get(reverse("order-list"))
        self.assertEqual(len(response.data), 0)

    def test_list_requires_authentication(self):
        self.client.credentials()
        response = self.client.get(reverse("order-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OrderUpdateTests(OrderTestCase):
    """Tests for updating the status of an order."""

    def setUp(self):
        super().setUp()
        self.order = self.create_order()
        self.url = reverse("order-detail", kwargs={"pk": self.order.id})

    def test_business_user_can_update_status(self):
        authenticate(self.client, self.business)
        response = self.client.patch(self.url, {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")

    def test_invalid_status_returns_400(self):
        authenticate(self.client, self.business)
        response = self.client.patch(self.url, {"status": "unknown"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_fields_return_400(self):
        authenticate(self.client, self.business)
        payload = {"status": "completed", "price": 1}
        response = self.client.patch(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_cannot_update_status(self):
        response = self.client.patch(self.url, {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_business_cannot_update_status(self):
        authenticate(self.client, self.other_business)
        response = self.client.patch(self.url, {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_order_returns_404(self):
        authenticate(self.client, self.business)
        url = reverse("order-detail", kwargs={"pk": 999})
        response = self.client.patch(url, {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_order_str(self):
        self.assertIn("Logo Design", str(self.order))


class OrderCountTests(OrderTestCase):
    """Tests for the order count endpoints."""

    def test_counts_orders_by_status(self):
        self.create_order()
        completed = self.create_order()
        completed.status = "completed"
        completed.save()
        kwargs = {"business_user_id": self.business.id}
        response = self.client.get(reverse("order-count", kwargs=kwargs))
        self.assertEqual(response.data, {"order_count": 1})
        response = self.client.get(
            reverse("completed-order-count", kwargs=kwargs)
        )
        self.assertEqual(response.data, {"completed_order_count": 1})

    def test_unknown_business_user_returns_404(self):
        kwargs = {"business_user_id": self.customer.id}
        response = self.client.get(reverse("order-count", kwargs=kwargs))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
