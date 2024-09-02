from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorAdminAuthenticatedOrReadOnly(BasePermission):
    """
    Разрешение авториованного пользователя.
    Остальным только чтение объекта.
    """

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated
                )

    def has_object_permission(
            self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            and request.user == obj.author
        )
