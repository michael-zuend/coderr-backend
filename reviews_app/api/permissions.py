from rest_framework.permissions import BasePermission


class IsReviewOwner(BasePermission):
    """Allow access only to the author of the review."""

    message = "Only the author of the review can perform this action."

    def has_object_permission(self, request, view, obj):
        return obj.reviewer == request.user
