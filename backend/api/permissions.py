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

    # def has_permission(self, request, view):
    #     # Разрешаем доступ к списку (list) для всех пользователей
    #     if view.action == 'list':
    #         return True

    #     # Запрещаем доступ к retrieve (например, /me/) для неавторизованных пользователей
    #     if view.action == 'retrieve' and not request.user.is_authenticated:
    #         return False

    #     # Разрешаем безопасные методы (например, GET) для авторизованных пользователей
    #     if request.method in SAFE_METHODS:
    #         return request.user.is_authenticated

    #     # Для всех других действий пользователь должен быть авторизован
    #     return request.user.is_authenticated

    # def has_object_permission(self, request, view, obj):
    #     # Разрешаем безопасные методы для всех
    #     if request.method in SAFE_METHODS:
    #         return True

    #     # Проверяем, что пользователь авторизован
    #     if not request.user.is_authenticated:
    #         return False

    #     # Разрешаем доступ к объекту, если пользователь является автором или администратором
    #     return request.user == obj.author or request.user.is_staff



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
 