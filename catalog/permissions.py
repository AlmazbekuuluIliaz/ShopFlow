from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Catalog access rule from the spec.

    - Safe methods (GET/HEAD/OPTIONS): allowed for everyone, including guests.
    - Writes (POST/PUT/PATCH/DELETE): only for admins.

    "Admin" means an authenticated user whose ``role`` is ADMIN, or a Django
    staff/superuser (so the created superuser works out of the box).
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not (user and user.is_authenticated):
            return False

        return bool(user.is_staff or user.is_admin)
