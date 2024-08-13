from djoser.serializers import UserCreateSerializer, UserSerializer
# from drf_extra_fields.fields import Base64ImageField
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth import authenticate

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient,
    RecipeTag, ShoppingCart, Tag
)
from users.models import Subscription, User


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


# class RecipeSerializer(serializers.ModelSerializer):
#     """ Сериализатор модели Рецептов. """

#     id = serializers.IntegerField()
#     tags = TagSerializer(many=True)
#     author = CustomUserSerializer(read_only=True)
#     ingredients = serializers.SerializerMethodField()
#     image = Base64ImageField()
#     is_favorited = serializers.SerializerMethodField(
#         method_name='get_is_favorited')
#     is_in_shopping_cart = serializers.SerializerMethodField(
#         method_name='get_is_in_shopping_cart')

#     class Meta:
#         model = Recipe
#         fields = [
#             'id',
#             'tags',
#             'author',
#             'ingredients',
#             'is_favorited',
#             'is_in_shopping_cart',
#             'name',
#             'image',
#             'text',
#             'cooking_time'
#         ]

#     def get_ingredients(self, obj):
#         ingredients = RecipeIngredient.objects.filter(recipe=obj)
#         return RecipeIngredientSerializer(ingredients, many=True).data

#     def get_is_favorited(self, obj):
#         request = self.context.get('request')
#         if request is None or request.user.is_anonymous:
#             return False
#         return Favorite.objects.filter(
#             user=request.user, recipe_id=obj
#         ).exists()

#     def get_is_in_shopping_cart(self, obj):
#         request = self.context.get('request')
#         if request is None or request.user.is_anonymous:
#             return False
#         return ShoppingCart.objects.filter(
#             user=request.user,
#             recipe_id=obj
#         ).exists()


# class AddIngredientRecipeSerializer(serializers.ModelSerializer):
#     """ Сериализатор добавления ингредиента в рецепт. """

#     id = serializers.IntegerField()
#     amount = serializers.IntegerField()

#     class Meta:
#         model = RecipeIngredient
#         fields = ['id', 'amount']


# class RecipeCreateSerializer(serializers.ModelSerializer):
#     """Сериализатор создания и обновления рецепта."""
#     tags = serializers.PrimaryKeyRelatedField(
#         many=True,
#         queryset=Tag.objects.all(),
#     )
#     ingredients = RecipeIngredientSerializer(
#         many=True
#     )
#     image = Base64ImageField()

#     class Meta:
#         model = Recipe
#         fields = (
#             'id', 'tags', 'author', 'ingredients', 'name',
#             'image', 'text', 'cooking_time',
#         )
#         read_only_fields = ('author',)
#         extra_kwargs = {
#             'name': {'required': True},
#             'text': {'required': True},
#             'cooking_time': {'required': True},
#             'image': {'required': True},
#             'ingredients': {'required': True},
#             'tags': {'required': True},
#         }

#     def validate_ingredients(self, ingredients) -> list:
#         if not ingredients:
#             raise serializers.ValidationError({
#                 'ingredients': 'Не передано ни одного ингридиента'
#             })
#         ingredient_list = []
#         for ingredient_item in ingredients:
#             if ingredient_item['pk'] in ingredient_list:
#                 raise serializers.ValidationError({
#                     'ingredients': 'Ингридиенты не должны повторяться'
#                 })
#             ingredient_list.append(ingredient_item['pk'])
#         return ingredients

#     def validate_tags(self, tags) -> list:
#         if not tags:
#             raise serializers.ValidationError({
#                 'tags': 'Не переданы тэги'
#             })
#         tag_list = []
#         for tag_item in tags:
#             if tag_item in tag_list:
#                 raise serializers.ValidationError({
#                     'tags': 'Тэги не должны повторяться'
#                 })
#             tag_list.append(tag_item)
#         return tags

#     def create_ingredients(self, ingredients_data, recipe) -> None:
#         ingredients = []
#         for ingredient in ingredients_data:
#             ingredients.append(RecipeIngredient(
#                 recipe=recipe,
#                 amount=ingredient.get('amount'),
#                 ingredient=ingredient.get('id')
#             ))
#         RecipeIngredient.objects.bulk_create(ingredients)

#     def create(self, validated_data) -> Recipe:
#         ingredients = validated_data.pop('ingredients')
#         tags = validated_data.pop('tags')
#         recipe = Recipe.objects.create(**validated_data)
#         self.create_ingredients(ingredients, recipe)
#         recipe.tags.set(tags)
#         return recipe

#     def update(self, instance, validated_data) -> Recipe:
#         try:
#             ingredients = validated_data.pop('ingredients')
#             tags = validated_data.pop('tags')
#             for key in self.Meta.extra_kwargs:
#                 if key not in ['ingredients', 'tags']:
#                     setattr(instance, key, validated_data.pop(key))
#         except KeyError:
#             raise serializers.ValidationError('Не переданы обязательные поля')
#         instance.tags.set(tags)
#         RecipeIngredient.objects.filter(recipe=instance).delete()
#         self.create_ingredients(ingredients, instance)
#         instance.save()
#         return instance

#     def to_representation(self, instance) -> dict:
#         request = self.context.get('request')
#         context = {'request': request}
#         return RecipeSerializer(instance, context=context).data


# class RecipeCreateSerializer(serializers.ModelSerializer):
#     """ Сериализатор создания/обновления рецепта. """

#     author = CustomUserSerializer(read_only=True)
#     ingredients = AddIngredientRecipeSerializer(many=True)
#     tags = serializers.PrimaryKeyRelatedField(
#         queryset=Tag.objects.all(),
#         many=True
#     )
#     image = Base64ImageField()

#     class Meta:
#         model = Recipe
#         fields = [
#             'id',
#             'author',
#             'ingredients',
#             'tags',
#             'image',
#             'name',
#             'text',
#             'cooking_time'
#         ]

#     def validate(self, data):
#         ingredients = self.initial_data.get('ingredients')
#         list = []
#         for i in ingredients:
#             amount = i['amount']
#             if int(amount) < 1:
#                 raise serializers.ValidationError({
#                     'amount': 'Количество ингредиента должно быть больше 0!'
#                 })
#             if i['id'] in list:
#                 raise serializers.ValidationError({
#                     'ingredient': 'Ингредиенты должны быть уникальными!'
#                 })
#             list.append(i['id'])
#         return data

#     def create_ingredients(self, ingredients, recipe):
#         for i in ingredients:
#             ingredient = Ingredient.objects.get(id=i['id'])
#             RecipeIngredient.objects.create(
#                 ingredient=ingredient, recipe=recipe, amount=i['amount']
#             )

#     def create_tags(self, tags, recipe):
#         for tag in tags:
#             RecipeTag.objects.create(recipe=recipe, tag=tag)

#     def create(self, validated_data):
#         tags = validated_data.pop('tags', [])
#         _ = self.context.get('request').user
#         ingredients = validated_data.pop('ingredients')
#         instance = super().create(validated_data)
#         instance.tags.set(tags)

#         recipe_ingredients = [
#             RecipeIngredient(
#                 recipe=instance,
#                 ingredient=ingredient_data['ingredient'],
#                 amount=ingredient_data['amount']
#             ) for ingredient_data in ingredients
#         ]
#         RecipeIngredient.objects.bulk_create(recipe_ingredients)
#         return instance

#     # def create(self, validated_data):
#     #     """
#     #     Создание рецепта.
#     #     Доступно только авторизированному пользователю.
#     #     """

#     #     ingredients = validated_data.pop('ingredients')
#     #     tags = validated_data.pop('tags')
#     #     author_ = self.context.get('request').user
#     #     recipe = Recipe.objects.create(author=author_, **validated_data)
#     #     self.create_ingredients(ingredients, recipe)
#     #     self.create_tags(tags, recipe)
#     #     return recipe

#     def update(self, instance, validated_data):
#         """
#         Изменение рецепта.
#         Доступно только автору.
#         """

#         RecipeTag.objects.filter(recipe=instance).delete()
#         RecipeIngredient.objects.filter(recipe=instance).delete()
#         ingredients = validated_data.pop('ingredients')
#         tags = validated_data.pop('tags')
#         self.create_ingredients(ingredients, instance)
#         self.create_tags(tags, instance)
#         instance.name = validated_data.pop('name')
#         instance.text = validated_data.pop('text')
#         if validated_data.get('image'):
#             instance.image = validated_data.pop('image')
#         instance.cooking_time = validated_data.pop('cooking_time')
#         instance.save()
#         return instance

#     def to_representation(self, instance):
#         return RecipeSerializer(instance, context={
#             'request': self.context.get('request')
#         }).data


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
        ingredients = self.initial_data.get('ingredients')
        list = []
        for i in ingredients:
            amount = i['amount']
            if int(amount) < 1:
                raise serializers.ValidationError({
                    'amount': 'Количество ингредиента должно быть больше 0!'
                })
            if i['id'] in list:
                raise serializers.ValidationError({
                    'ingredient': 'Ингредиенты должны быть уникальными!'
                })
            list.append(i['id'])
        return data

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
