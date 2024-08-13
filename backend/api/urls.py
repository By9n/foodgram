from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, RecipeViewSet,
                    get_short_link,
                    TagViewSet, CustomUserViewSet
                    )
# UserSubscriptionViewSet, ShoppingCartView, SubscriptionsView, FavoriteView, SubscribeView
app_name = 'api'

router = DefaultRouter()

router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'users', CustomUserViewSet, basename='subscriptions')
urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
    path('', include(router.urls)),
    path('recipes/<int:recipe_id>/get-link/', get_short_link, name='get-link'),
    # path(
    #     'users/<int:id>/subscribe/',
    #     SubscribeView.as_view(),
    #     name='subscribe'
    # ),
    # path(
    #     'users/subscriptions/',
    #     SubscriptionsView.as_view(),
    #     name='subscriptions'
    # ),
    # path(
    #     'recipes/<int:id>/favorite/',
    #     FavoriteView.as_view(),
    #     name='favorite'
    # ),
    # path(
    #     'recipes/<int:id>/shopping_cart/',
    #     ShoppingCartView.as_view(),
    #     name='shopping_cart'
    # ),
    # path(
    #     'recipes/download_shopping_cart/',
    #     download_shopping_cart,
    #     name='download_shopping_cart'
    # ),
]