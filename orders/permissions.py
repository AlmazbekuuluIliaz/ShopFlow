from rest_framework.permissions import BasePermission


def is_admin(user):
    """ADMIN role, or a Django staff/superuser."""
    return bool(user and user.is_authenticated and (user.is_staff or user.is_admin))


class IsOwnerOrAdmin(BasePermission):
    """Object-level: an order is reachable only by the user who placed it,
    or by an admin. This is what makes "чужие заказы недоступны" true."""

    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True
        return obj.user_id == request.user.id
