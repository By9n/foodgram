from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorAdminAuthenticatedOrReadOnly(BasePermission):
    """
    Разрешение  для админа и авториованного пользователя(автора).
    Остальным только чтение объекта.
    """

    def has_permission(self, request, view):
        if view.action in ('list', 'retrieve'):
            return True
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated
                )

    def has_object_permission(
            self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            and request.user == obj.author
            or request.user.is_staff
        )


class UserPermission(BasePermission):
    """
    Разрешения для UserViewSet, обеспечивающие разные уровни доступа
    в зависимости от действия (action) и аутентификации пользователя.
    """
    def has_permission(self, request, view):
        if view.action in ('list', 'retrieve'):
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(
            self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            and request.user == obj.author
            or request.user.is_staff
        )
