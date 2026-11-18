from rest_framework.permissions import BasePermission


class IsOfferOwner(BasePermission):
    """Allow access only to the user who created the offer."""

    message = "Only the creator of the offer can perform this action."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
