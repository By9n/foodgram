from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


class IngredientAdminForm(forms.ModelForm):
    class Meta:
        model = RecipeIngredient
        field = ['name', 'measurement_unit']

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        if not name:
            raise ValidationError("Название ингредиента не может быть пустым.")
        return cleaned_data


class RecipeIngredientInline(admin.TabularInline):
    """Админ-модель рецептов_ингредиентов"""
    model = RecipeIngredient
    # form = IngredientAdminForm
    extra = 1
    min_num = 1


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


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'author',
        'image_tag', 'favorites_count'
    )
    inlines = (RecipeIngredientInline,)
    search_fields = ('name', 'author__username',
                     'author__email', 'ingredients')
    list_filter = ('author', 'name', 'tags', 'ingredients')
    ordering = ('-id',)

    def image_tag(self, obj):
        if obj.image:
            return mark_safe('<img src="{}" width="150"'
                             'height="100" />'.format(obj.image.url))
        return None

    image_tag.short_description = 'Фото рецепта'

    @admin.display(description='Количество в избранных')
    def favorites_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        if Favorite.objects.filter(recipe=obj).exists():
            return Favorite.objects.filter(recipe=obj).count()
        return 0

    def save_model(self, request, obj, form, change):
        # Проверяем наличие ингредиентов перед сохранением рецепта
        ingredients = obj.recipeingredient_set.all()
        if not ingredients.exists():
            raise ValidationError("Необходимо добавить хотя бы один ингредиент к рецепту.")
        
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        # Переопределяем save_related для проверки ингредиентов в инлайн-формсетах
        instances = form.save(commit=False)
        for instance in instances:
            ingredients = instance.recipeingredient_set.all()
            if not ingredients.exists():
                raise ValidationError("Необходимо добавить хотя бы один ингредиент к рецепту.")
        
        super().save_related(request, form, formsets, change)


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
    ordering = ('name',)


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
