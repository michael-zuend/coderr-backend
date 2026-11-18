from django.db.models import Min, Q
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from offers_app.models import Offer, OfferDetail
from profile_app.api.permissions import IsBusinessUser

from .pagination import OfferPagination
from .permissions import IsOfferOwner
from .serializers import (
    OfferDetailSerializer,
    OfferListSerializer,
    OfferRetrieveSerializer,
    OfferWriteSerializer,
)

ORDERING_FIELDS = {"updated_at", "-updated_at", "min_price", "-min_price"}


def parse_number(params, name, number_type):
    """Read an optional numeric query parameter or raise a 400 error."""
    value = params.get(name, "")
    if value == "":
        return None
    try:
        return number_type(value)
    except ValueError:
        raise ValidationError({name: "Must be a valid number."})


class OfferViewSet(viewsets.ModelViewSet):
    """List, create, retrieve, update and delete offers."""

    queryset = Offer.objects.select_related("user").prefetch_related(
        "details"
    )
    pagination_class = OfferPagination
    http_method_names = ["get", "post", "patch", "delete", "options"]

    def get_permissions(self):
        """Return the permissions required for the current action."""
        if self.action == "list":
            return [AllowAny()]
        if self.action == "create":
            return [IsAuthenticated(), IsBusinessUser()]
        if self.action in ("partial_update", "destroy"):
            return [IsAuthenticated(), IsOfferOwner()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """Return the serializer for the current action."""
        if self.action == "list":
            return OfferListSerializer
        if self.action == "retrieve":
            return OfferRetrieveSerializer
        return OfferWriteSerializer

    def get_queryset(self):
        """Annotate summary values and apply filters to the list."""
        queryset = super().get_queryset().annotate(
            min_price=Min("details__price"),
            min_delivery_time=Min("details__delivery_time_in_days"),
        )
        if self.action == "list":
            queryset = self.filter_queryset_by_params(queryset)
        return queryset

    def filter_queryset_by_params(self, queryset):
        """Apply the query parameters of the offer list."""
        params = self.request.query_params
        creator_id = parse_number(params, "creator_id", int)
        min_price = parse_number(params, "min_price", float)
        max_time = parse_number(params, "max_delivery_time", int)
        if creator_id is not None:
            queryset = queryset.filter(user_id=creator_id)
        if min_price is not None:
            queryset = queryset.filter(min_price__gte=min_price)
        if max_time is not None:
            queryset = queryset.filter(min_delivery_time__lte=max_time)
        queryset = self.search_queryset(queryset, params.get("search", ""))
        return self.order_queryset(queryset, params.get("ordering", ""))

    def search_queryset(self, queryset, search):
        """Search the title and the description of the offers."""
        if not search:
            return queryset
        return queryset.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    def order_queryset(self, queryset, ordering):
        """Order the offers by an allowed field."""
        if ordering in ORDERING_FIELDS:
            return queryset.order_by(ordering)
        return queryset.order_by("-updated_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        """Update an offer and return it with all its packages."""
        offer = self.get_object()
        serializer = self.get_serializer(
            offer, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        offer.refresh_from_db()
        return Response(self.get_serializer(offer).data)


class OfferDetailRetrieveView(RetrieveAPIView):
    """Retrieve a single offer package."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]
