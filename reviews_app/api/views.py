from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated

from profile_app.api.permissions import IsCustomerUser
from reviews_app.models import Review

from .permissions import IsReviewOwner
from .serializers import ReviewSerializer, ReviewUpdateSerializer

ORDERING_FIELDS = {"updated_at", "-updated_at", "rating", "-rating"}
FILTER_PARAMS = {"business_user_id": "business_user_id",
                 "reviewer_id": "reviewer_id"}


class ReviewViewSet(viewsets.ModelViewSet):
    """List, create, update and delete reviews."""

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    http_method_names = ["get", "post", "patch", "delete", "options"]

    def get_permissions(self):
        """Return the permissions required for the current action."""
        if self.action == "create":
            return [IsAuthenticated(), IsCustomerUser()]
        if self.action in ("partial_update", "destroy"):
            return [IsAuthenticated(), IsReviewOwner()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """Use a restricted serializer for updates."""
        if self.action == "partial_update":
            return ReviewUpdateSerializer
        return ReviewSerializer

    def get_queryset(self):
        """Filter and order the reviews by the query parameters."""
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        params = self.request.query_params
        for param, field in FILTER_PARAMS.items():
            queryset = self.filter_by_id(queryset, params, param, field)
        ordering = params.get("ordering", "")
        if ordering in ORDERING_FIELDS:
            queryset = queryset.order_by(ordering)
        return queryset

    def filter_by_id(self, queryset, params, param, field):
        """Filter the queryset by an optional numeric id parameter."""
        value = params.get(param, "")
        if value == "":
            return queryset
        if not value.isdigit():
            raise ValidationError({param: "Must be a valid id."})
        return queryset.filter(**{field: int(value)})

    def perform_create(self, serializer):
        """Save the review if the user has not reviewed this user yet."""
        business_user = serializer.validated_data["business_user"]
        already_reviewed = Review.objects.filter(
            business_user=business_user, reviewer=self.request.user
        ).exists()
        if already_reviewed:
            raise PermissionDenied(
                "You have already reviewed this business user."
            )
        serializer.save(reviewer=self.request.user)
