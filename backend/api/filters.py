import django_filters
from django_filters.rest_framework import FilterSet
from rest_framework.filters import SearchFilter


from recipes.models import Recipe, Tag
from users.models import User

class IngredientFilter(SearchFilter):
    search_param = 'name'



class RecipeFilter(FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    author = django_filters.ModelMultipleChoiceFilter(
        field_name='author__id',
        to_field_name='id',
        queryset=User.objects.all()
    )
    # is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')
    # is_in_shopping_cart = django_filters.BooleanFilter(
    #     method='filter_is_in_shopping_cart'
    # )

    is_favorited = django_filters.NumberFilter(
        method='filter_is_favorited',
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart',
    )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset


    # def filter_is_favorited(self, queryset, name, value):
    #     user = self.request.user
    #     if user.is_authenticated:
    #         return queryset.filter(users_recipes__user=request.user)
    #     return queryset

    # def filter_is_in_shopping_cart(self, queryset, name, value):
    #     request = self.request
    #     if request.user.is_anonymous:
    #         return queryset.none()
    #     if value:
    #         return queryset.filter(in_shopping_carts__user=request.user)
    #     return queryset

    class Meta:
        model = Recipe
        fields = [
            'author',
            'is_favorited',
            'is_in_shopping_cart',
            'tags'
        ]

