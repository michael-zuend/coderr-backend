from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsProfileOwnerOrReadOnly(BasePermission):
    """Allow read access to everyone, write access only to the owner."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user


def has_profile_type(user, profile_type):
    """Return True if the user has a profile of the given type."""
    profile = getattr(user, "profile", None)
    return profile is not None and profile.type == profile_type


class IsBusinessUser(BasePermission):
    """Allow access only to users with a business profile."""

    message = "Only business users can perform this action."

    def has_permission(self, request, view):
        return has_profile_type(request.user, "business")


class IsCustomerUser(BasePermission):
    """Allow access only to users with a customer profile."""

    message = "Only customer users can perform this action."

    def has_permission(self, request, view):
        return has_profile_type(request.user, "customer")
