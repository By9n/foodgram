from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet,
                    get_short_link)

app_name = 'api'

router = DefaultRouter()

router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', UserViewSet, basename='user')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')


urlpatterns = [
    path('users/subscriptions/',
         UserViewSet.as_view({'get': 'get_subscriptions'}),
         name='user-subscriptions'),
    
    path('', include('djoser.urls')),

    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
   
    path('recipes/<int:recipe_id>/get-link/', get_short_link, name='get-link'),
]
