from rest_framework.permissions import BasePermission


class IsOrderBusinessUser(BasePermission):
    """Allow access only to the business user of the order.

    This is an object permission, so a missing order returns 404 before
    the permission is checked.
    """

    message = "Only the business user of this order can update it."

    def has_object_permission(self, request, view, obj):
        return obj.business_user == request.user
