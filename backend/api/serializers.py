from djoser.serializers import UserCreateSerializer, UserSerializer
# from drf_extra_fields.fields import Base64ImageField
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest
from django.http import Http404

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient,
    RecipeTag, ShoppingCart, Tag, RecipeShortLink
)
from users.models import Subscription, User
from .validators import validate_tags


class TokenCreateSerializer(serializers.Serializer):
    """Сериализатор для получения токена."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError('Неверные учетные данные.')

        return attrs


class CreateCustomUserSerializer(UserCreateSerializer):
    """ Сериализатор создания пользователя. """

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        ]


class CustomUserSerializer(UserSerializer):
    """ Сериализатор модели пользователя. """

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        ]
        extra_kwargs = {
            'is_subscribed': {'read_only': True},
            'username': {'required': False},
        }

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=user, author=obj
        ).exists()

    def get_avatar(self, obj):
        '''Возвращает url аватара '''
        if obj.avatar:
            return obj.avatar.url
        return None


class ShortResipesSerializer(serializers.ModelSerializer):
    """
    Сериализатор укороченной информации о рецепте
    для выдачи в списке подписок.
    """
    class Meta:
        model = Recipe
        fields = 'id', 'name', 'image', 'cooking_time'
        read_only_fields = ('__all__',)


class ShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор для короткой ссылки."""
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = RecipeShortLink
        fields = ('short_link',)

    def get_short_link(self, obj):
        """Создает полный URL для короткой ссылки."""
        base_url = 'https://127.0.0.1:8000/s/'
        return f"{base_url}{obj.short_link}"

    def to_representation(self, instance):
        """Преобразует ключи в формат с дефисом."""
        representation = super().to_representation(instance)
        return {
            'short-link': representation['short_link']
        }


class UserSubscriptionSerializer(CustomUserSerializer):
    """
    Сериализатор, который возвращает пользователей,
    на которых подписан текущий пользователь.
    В выдачу добавляются рецепты с укороченной информацией.
    """
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
            'recipes_count',
            'recipes'
        ]
        read_only_fields = ('__all__',)

    def get_recipes_count(self, obj: User) -> int:
        """Функция динамического расчета количества рецептов автора."""
        return obj.recipes.count()

    def get_recipes(self, obj: User) -> dict:
        """
        Функция динамической выдачи рецептов автора,
        количество ограничено лимитом из QUERY PARAMETERS
        """
        limit = self.context['request'].query_params.get('recipes_limit')
        queryset = obj.recipes.all()
        if limit:
            queryset = queryset[:int(limit)]
        serializer = ShortResipesSerializer(queryset, many=True)
        return serializer.data

    def validate(self, attrs: dict) -> dict:
        """Валидация для создания подписки."""
        request = self.context.get('request')
        author_id = request.parser_context.get('kwargs').get('id')
        author = get_object_or_404(User, id=author_id)
        user = request.user
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя'
            )
        if Subscription.objects.filter(user=user,
                                       author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора'
            )
        return attrs


class AvatarUserSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления/удаления аватара."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeMinifiedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id',)


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer модели CustomUser"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        ]
        read_only_fields = ('id',)

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Subscription.objects.filter(user=user, author=obj).exists()
        else:
            return False


class TagSerializer(serializers.ModelSerializer):
    """ Сериализатор модели Тегов. """

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор связывающей модели ингредиентов и рецептов. """

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'amount', 'measurement_unit']


class IngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор модели Ингредиентов. """

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор просмотра модели Рецепт. """

    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
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
    """ Сериализатор создания/обновления рецепта. """

    author = CustomUserSerializer(read_only=True)
    ingredients = AddIngredientRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField(required=True)

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

    def validate(self, data):
        tags = self.initial_data.get('tags')
        tags = validate_tags(tags)
        # if not tags:
        #     raise serializers.ValidationError(
        #         'Нужен хотя бы один тэг для рецепта!')
        # tags_list = []
        # for tag_name in tags:
        #     if not Tag.objects.filter(name=tag_name).exists():
        #         raise serializers.ValidationError(
        #             f'Тэга {tag_name} не существует!')
        #     if tag_name in tags_list:
        #         raise serializers.ValidationError('Тэг должен '
        #                                           'быть уникальным')
        #     tags_list.append(tag_name)
        
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
            except Http404 as e:
                raise serializers.ValidationError({
                    'ingredients': ('Убедитесь, что такой '
                                    'ингредиент существует')
                })
            # ingredient = get_object_or_404(Ingredient,
            #                                id=ingredient_item['id'])
            if ingredient in ingredient_list:
                raise serializers.ValidationError('Ингридиенты должны '
                                                  'быть уникальными')
            ingredient_list.append(ingredient)
            if int(ingredient_item['amount']) < 1:
                raise serializers.ValidationError({
                    'ingredients': ('Убедитесь, что значение количества '
                                    'ингредиента больше 0')
                })
        data['ingredients'] = ingredients
        return data

    # def validate(self, data):
    #     ingredients = self.initial_data.get('ingredients')
    #     list = []
    #     for i in ingredients:
    #         amount = i['amount']
    #         if int(amount) < 1:
    #             raise serializers.ValidationError({
    #                 'amount': 'Количество ингредиента должно быть больше 0!'
    #             })
    #         if i['id'] in list:
    #             raise serializers.ValidationError({
    #                 'ingredient': 'Ингредиенты должны быть уникальными!'
    #             })
    #         list.append(i['id'])
    #     return data

    def create_ingredients(self, ingredients, recipe):
        for i in ingredients:
            ingredient = Ingredient.objects.get(id=i['id'])
            RecipeIngredient.objects.create(
                ingredient=ingredient, recipe=recipe, amount=i['amount']
            )

    def create_tags(self, tags, recipe):
        for tag in tags:
            RecipeTag.objects.create(recipe=recipe, tag=tag)

    def create(self, validated_data):
        """
        Создание рецепта.
        Доступно только авторизированному пользователю.
        """

        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.create_ingredients(ingredients, recipe)
        self.create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        """
        Изменение рецепта.
        Доступно только автору.
        """

        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        self.create_ingredients(ingredients, instance)
        self.create_tags(tags, instance)
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


class ShowFavoriteSerializer(serializers.ModelSerializer):
    """ Сериализатор для отображения избранного. """

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class TagSerializer(serializers.ModelSerializer):
    """Serializer модели Tag"""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """ Сериализатор для списка покупок. """

    class Meta:
        model = ShoppingCart
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        return ShowFavoriteSerializer(instance.recipe, context={
            'request': self.context.get('request')
        }).data


class FavoriteSerializer(serializers.ModelSerializer):
    """ Сериализатор модели Избранное. """

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


class ShowSubscriptionsSerializer(serializers.ModelSerializer):
    """ Сериализатор для отображения подписок пользователя. """

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipes = Recipe.objects.filter(author=obj)
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return ShowFavoriteSerializer(
            recipes, many=True, context={'request': request}).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class SubscriptionSerializer(serializers.ModelSerializer):
    """ Сериализатор подписок. """

    class Meta:
        model = Subscription
        fields = ['user', 'author']
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author'],
            )
        ]

    def to_representation(self, instance):
        return ShowSubscriptionsSerializer(instance.author, context={
            'request': self.context.get('request')
        }).data
