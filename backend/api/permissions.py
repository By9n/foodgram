from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS, BasePermission


class AuthorOrAdminOReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated and request.user.is_staff
                or request.user == obj.author)


# class IsAuthorAdminAuthenticated(permissions.BasePermission):
#     """Досутуп для автора, администратора или только чтения. """
#     def has_permission(self, request, view):
#         return (
#             request.method in permissions.SAFE_METHODS
#             or request.user.is_authenticated
#         )

#     def has_object_permission(self, request, view, obj):
#         return (request.method in permissions.SAFE_METHODS
#                 or obj.author == request.user)


# class AuthorPermission(BasePermission):
#     """Делаем так, чтобы изменять и добавлять объекты
#        мог только их автор"""

#     def has_object_permission(self, request, view, obj):
#         return (request.method in SAFE_METHODS
#                 or obj.author == request.user)

