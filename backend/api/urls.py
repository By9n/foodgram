from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet, IngredientViewSet, RecipeViewSet,
    TagViewSet, get_short_link
)

app_name = 'api'

router = DefaultRouter()

router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'users', CustomUserViewSet, basename='user')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
    path('recipes/<int:recipe_id>/get-link/', get_short_link, name='get-link'),
]
