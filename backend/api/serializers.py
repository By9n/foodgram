from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from api.validators import validate_tags
from recipes.constants import MIN_AMOUNT_INGREDIENT
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            RecipeShortLink, ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user or user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()


class ShowFavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор укороченной информации о рецепте."""
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']
        read_only_fields = ('__all__',)


class RecipeMixin:
    """Миксин для сериализаторов, работающих с рецептами."""

    def get_recipes(self, obj):
        """Функция выдачи рецептов автора с лимитом."""
        limit = self.context['request'].query_params.get('recipes_limit')
        queryset = obj.recipes.all()
        try:
            limit = int(limit) if limit and int(limit) > 0 else None
        except (ValueError, TypeError):
            limit = None
        if limit:
            queryset = queryset[:limit]
        serializer = ShowFavoriteSerializer(queryset, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        """Функция расчета количества рецептов автора."""
        return obj.recipes.count()


class ShortLinkSerializer(serializers.ModelSerializer, RecipeMixin):
    """Сериализатор для короткой ссылки."""

    short_link = serializers.SerializerMethodField()

    class Meta:
        model = RecipeShortLink
        fields = ('short_link',)

    def get_short_link(self, obj):
        """Создает полный URL для короткой ссылки."""
        return f"/s/{obj.short_link}"

    def to_representation(self, instance):
        """Преобразует ключи в формат с дефисом."""
        representation = super().to_representation(instance)
        return {
            'short-link': representation['short_link']
        }


class SubscriptionSerializer(serializers.ModelSerializer, RecipeMixin):
    """Сериализатор для подписок пользователя."""

    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()


class AvatarUserSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления/удаления аватара."""
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели Тегов."""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор связывающей модели ингредиентов и рецептов."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'amount', 'measurement_unit']


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели Ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра модели Рецепт."""
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited')
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        ]
    read_only_fields = ('author', 'tags', 'ingredients')

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор добавления ингредиента в рецепт. """

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор создания/обновления рецепта."""
    author = UserSerializer(read_only=True)
    ingredients = AddIngredientRecipeSerializer(
        many=True, required=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        ]

    def validate(self, data):
        tags = self.initial_data.get('tags')
        tags = validate_tags(tags)
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужен хоть один ингридиент для рецепта'})
        ingredient_list = []
        for ingredient_item in ingredients:
            try:
                ingredient = get_object_or_404(Ingredient,
                                               id=ingredient_item['id']
                                               )
            except Http404:
                raise serializers.ValidationError({
                    'ingredients': ('Убедитесь, что такой '
                                    'ингредиент существует')
                })
            if ingredient in ingredient_list:
                raise serializers.ValidationError('Ингридиенты должны '
                                                  'быть уникальными')
            ingredient_list.append(ingredient)
            if int(ingredient_item['amount']) < MIN_AMOUNT_INGREDIENT:
                raise serializers.ValidationError({
                    'ingredients': ('Убедитесь, что значение количества '
                                    'ингредиента больше 0')
                })
        data['ingredients'] = ingredients
        return data

    def create_ingredients(self, ingredients, recipe):
        for ingredient_for_create in ingredients:
            ingredient = Ingredient.objects.get(id=ingredient_for_create['id'])
            RecipeIngredient.objects.create(
                ingredient=ingredient,
                recipe=recipe,
                amount=ingredient_for_create['amount']
            )

    def create(self, validated_data):
        """Создание рецепта."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Изменение рецепта."""
        instance.tags.clear()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        ingredients = validated_data.pop('ingredients', None)
        self.create_ingredients(ingredients, instance)
        instance.name = validated_data.pop('name')
        instance.text = validated_data.pop('text')
        if validated_data.get('image'):
            instance.image = validated_data.pop('image')
        instance.cooking_time = validated_data.pop('cooking_time')
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """ Сериализатор для списка покупок."""
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор модели Избранное."""
    class Meta:
        model = Favorite
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        return ShowFavoriteSerializer(
            instance.recipe,
            context={
                'request': self.context.get('request')
            }
        ).data


# class SubscriptionSerializer(UserSerializer):
#     """Сериализатор для подписок пользователя."""
#     recipes = serializers.SerializerMethodField(read_only=True)
#     recipes_count = serializers.SerializerMethodField()
#     is_subscribed = serializers.SerializerMethodField(
#         read_only=True
#     )

#     class Meta:
#         model = User
#         fields = (
#             'email',
#             'id',
#             'username',
#             'first_name',
#             'last_name',
#             'is_subscribed',
#             'recipes',
#             'recipes_count',
#             'avatar'
#         )

#     def get_recipes(self, obj):
#         request = self.context['request']
#         limit = request.GET.get('recipes_limit')
#         recipes = Recipe.objects.filter(author=obj)
#         try:
#             limit = int(limit) if limit and int(limit) > 0 else None
#         except (ValueError, TypeError):
#             limit = None
#         if limit:
#             recipes = recipes[:limit]
#         serializer = ShowFavoriteSerializer(
#             recipes,
#             many=True
#         )
#         return serializer.data

#     def get_recipes_count(self, object):
#         return object.recipes.count()

#     def get_is_subscribed(self, obj):
#         user = self.context.get('request').user
#         if user.is_anonymous:
#             return False
#         return Subscription.objects.filter(user=user, author=obj).exists()
