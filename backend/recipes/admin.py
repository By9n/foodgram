from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
)


class RecipeIngredientInline(admin.TabularInline):
    """Админ-модель рецептов_ингредиентов"""
    model = RecipeIngredient
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ-модель тегов"""
    list_display = (
        'id',
        'name',
        'slug'
    )
    list_display_links = ('name',)
    search_fields = ('name',)
    empty_value_display = '-пусто-'


# @admin.register(Recipe)
# class RecipeAdmin(admin.ModelAdmin):
#     """Админ-модель рецептов"""
#     inlines = (RecipeIngredientInline,)
#     list_display = (
#         'id',
#         'name',
#         'author',
#         'image'
#     )
#     list_display_links = ('name',)
#     search_fields = (
#         'name',
#         'author',
#         'text',
#         'ingredients'
#     )
#     list_editable = (
#         'author',
#     )
#     list_filter = ('tags',)
#     empty_value_display = '-пусто-'

    # @admin.display(description='В избранном')
    # def in_favorited(self, obj):
    #     return obj.in_favorite.count()
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'image_tag')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags',)
    ordering = ('-id',)

    def image_tag(self, obj):
        if obj.image:
            return mark_safe('<img src="{}" width="150"'
                             'height="100" />'.format(obj.image.url))
        return None

    image_tag.short_description = 'Фото рецепта'

    # @admin.display(description='Количество рецептов в избранном')
    # def favorites_count(self, obj):
    #     """Возвращает количество добавлений рецепта в избранное."""
    #     return obj.users_recipes.count()

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админ-модель ингредиентов"""
    list_display = (
        'id',
        'name',
        'measurement_unit'
    )
    list_filter = ('measurement_unit',)
    list = (
        'measurement_unit'
    )
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админ-модель избранного"""
    list_display = (
        'id',
        'user',
        'recipe'
    )
    list_editable = ('user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ-модель списка покупок"""
    list_display = (
        'id',
        'user',
        'recipe'
    )
    list_editable = ('user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = '-пусто-'
