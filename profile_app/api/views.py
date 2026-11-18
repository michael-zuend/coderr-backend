from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from profile_app.models import Profile

from .permissions import IsProfileOwnerOrReadOnly
from .serializers import (
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
    ProfileDetailSerializer,
)


class ProfileDetailView(RetrieveUpdateAPIView):
    """Retrieve a profile by user id or update the own profile."""

    queryset = Profile.objects.select_related("user")
    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated & IsProfileOwnerOrReadOnly]
    lookup_field = "user"
    lookup_url_kwarg = "pk"
    http_method_names = ["get", "patch", "options"]


class BusinessProfileListView(ListAPIView):
    """List all business profiles."""

    queryset = Profile.objects.filter(type="business").select_related("user")
    serializer_class = BusinessProfileListSerializer
    permission_classes = [IsAuthenticated]


class CustomerProfileListView(ListAPIView):
    """List all customer profiles."""

    queryset = Profile.objects.filter(type="customer").select_related("user")
    serializer_class = CustomerProfileListSerializer
    permission_classes = [IsAuthenticated]
