from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import OfferDetail
from orders_app.models import Order
from profile_app.api.permissions import IsBusinessUser, IsCustomerUser

from .permissions import IsOrderBusinessUser
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusSerializer,
)


def create_order_from_detail(detail, customer):
    """Create an order that copies the data of an offer detail."""
    return Order.objects.create(
        customer_user=customer,
        business_user=detail.offer.user,
        title=detail.title,
        revisions=detail.revisions,
        delivery_time_in_days=detail.delivery_time_in_days,
        price=detail.price,
        features=detail.features,
        offer_type=detail.offer_type,
    )


class OrderListCreateView(ListCreateAPIView):
    """List the orders of the user or create a new order."""

    serializer_class = OrderSerializer

    def get_permissions(self):
        """Only customers can create orders."""
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomerUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Return the orders where the user is customer or business."""
        user = self.request.user
        return Order.objects.filter(
            Q(customer_user=user) | Q(business_user=user)
        )

    def create(self, request, *args, **kwargs):
        """Create an order based on an offer detail."""
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        detail = get_object_or_404(
            OfferDetail.objects.select_related("offer__user"),
            pk=serializer.validated_data["offer_detail_id"],
        )
        order = create_order_from_detail(detail, request.user)
        data = OrderSerializer(order).data
        return Response(data, status=status.HTTP_201_CREATED)


class OrderUpdateView(UpdateAPIView):
    """Update the status of an order."""

    queryset = Order.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [
        IsAuthenticated, IsBusinessUser, IsOrderBusinessUser
    ]
    http_method_names = ["patch", "options"]

    def partial_update(self, request, *args, **kwargs):
        """Update the status and return the complete order."""
        order = self.get_object()
        serializer = self.get_serializer(order, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)


class BaseOrderCountView(APIView):
    """Count the orders of a business user with a given status."""

    permission_classes = [IsAuthenticated]
    order_status = ""
    response_key = ""

    def get(self, request, business_user_id):
        business_user = get_object_or_404(
            User, pk=business_user_id, profile__type="business"
        )
        count = Order.objects.filter(
            business_user=business_user, status=self.order_status
        ).count()
        return Response({self.response_key: count})


class OrderCountView(BaseOrderCountView):
    """Count the orders of a business user that are in progress."""

    order_status = "in_progress"
    response_key = "order_count"


class CompletedOrderCountView(BaseOrderCountView):
    """Count the completed orders of a business user."""

    order_status = "completed"
    response_key = "completed_order_count"
