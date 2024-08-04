# from django.conf import settings
# from django.contrib.auth.views import LogoutView
# from django.urls import path

# from . import views

# urlpatterns = [
#     path('signup/', views.SignUpView.as_view(), name='signup'),
#     path('logout/', LogoutView.as_view(),
#          {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
# ]

# from django.urls import include, path
# from rest_framework.routers import DefaultRouter

# from .views import CustomUserViewSet

# app_name = 'users'

# router = DefaultRouter()

# router.register('users', CustomUserViewSet)

# urlpatterns = [
#     path('', include(router.urls)),
#     path('', include('djoser.urls')),
#     path('auth/', include('djoser.urls.authtoken')),
# ]