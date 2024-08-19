from rest_framework import permissions


class IsAuthorAdminAuthenticated(permissions.BasePermission):
    """Досутуп для автора, администратора или только чтения. """
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)
