from django.contrib.auth import authenticate
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import PageLimitPagination
from api.permissions import AuthorOrStaffOrReadOnly
from api.serializers import (AvatarUserSerializer, CreateRecipeSerializer,
                             FavoriteSerializer, IngredientSerializer,
                             RecipeSerializer, ShoppingCartSerializer,
                             ShortLinkSerializer, ShowFavoriteSerializer,
                             SubscriptionSerializer, TagSerializer,
                             TokenCreateSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            RecipeShortLink, ShoppingCart, Tag)
from users.models import Subscription, User


class TokenCreateView(APIView):
    """Вьюсет для получения токена авторизации. """
    permission_classes = (AllowAny, )
    serializer_class = TokenCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(email=email, password=password)

            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({'auth_token': token.key},
                                status=status.HTTP_201_CREATED)
            return Response({'detail': 'Неверные учетные данные.'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomUserViewSet(UserViewSet):
    """ViewSet модели пользователей"""

    queryset = User.objects.all()
    pagination_class = PageLimitPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (AllowAny(),)
        return super().get_permissions()

    @action(detail=False, methods=['put'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request, *args, **kwargs):
        """Добавление-обновление аватара пользователя."""
        user = request.user
        serializer = AvatarUserSerializer(user, data=request.data)

        if not request.data.get('avatar'):
            return Response(
                {'detail': 'Поле avatar обязательно.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        """Удаление аватара пользователя."""
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Аватар отсутствует.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Просмотр листа подписок пользователя."""
        user = self.request.user
        subscriptions = User.objects.filter(follower__user=user)
        list = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(
            list, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        """Подписка на пользователей."""
        user = request.user
        author = get_object_or_404(User, pk=id)

        if user.id == author.id:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance = Subscription.objects.filter(author=author, user=user)
        if request.method == 'POST':
            if instance.exists():
                return Response('Вы уже подписаны',
                                status=status.HTTP_400_BAD_REQUEST)
            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(author,
                                                context={'request': request})
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if instance.exists():
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response('Вы не подписаны на автора',
                            status=status.HTTP_400_BAD_REQUEST)


class FavoriteView(APIView):
    """Добавление/удаление рецепта из избранного."""
    permission_classes = [IsAuthenticated, ]
    pagination_class = PageLimitPagination

    def post(self, request, id):
        data = {
            'user': request.user.id,
            'recipe': id
        }

        if not Favorite.objects.filter(
           user=request.user, recipe__id=id).exists():
            serializer = FavoriteSerializer(
                data=data, context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        if Favorite.objects.filter(
           user=request.user, recipe=recipe).exists():
            Favorite.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Отображение тегов."""
    permission_classes = [AllowAny, ]
    pagination_class = None
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Отображение ингредиентов."""
    permission_classes = [AllowAny, ]
    pagination_class = None
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = [IngredientFilter, ]
    search_fields = ['^name', ]


class RecipeListMixin:
    model_class = None
    action_name = None

    def add_to_list(self, request, pk=None):
        """Добавить рецепт(корзина или избранное)."""
        recipe = self.get_object()
        user = request.user
        if self.model_class.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': f'Рецепт уже добавлен в {self.action_name}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.model_class.objects.create(user=user, recipe=recipe)
        serializer = ShowFavoriteSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_list(self, request, pk=None):
        """Удалить рецепт(корзина или избранное)."""
        recipe = self.get_object()
        user = request.user
        if not self.model_class.objects.filter(user=user,
                                               recipe=recipe).exists():
            return Response(
                {'errors': f'Рецепт не был добавлен в {self.action_name}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.model_class.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(
    RecipeListMixin,
    viewsets.ModelViewSet
):
    """ViewSet для рецептов."""
    queryset = Recipe.objects.all()
    pagination_class = PageLimitPagination
    permission_classes = (AuthorOrStaffOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return CreateRecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def post_delete(self, request, pk, model, serializer_class):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            serializer = serializer_class(data={'user': user,
                                                'recipe': recipe})
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user,
                            recipe=recipe)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            instance = get_object_or_404(model,
                                         user=user,
                                         recipe=recipe)
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавить рецепт в избранное текущего пользователя."""
        self.model_class = Favorite
        self.action_name = 'избранное'
        return self.add_to_list(request, pk)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        """Удалить рецепт из избранного текущего пользователя."""
        self.model_class = Favorite
        self.action_name = 'избранное'
        return self.remove_from_list(request, pk)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавить-удалить рецепт из списка покупок пользователя."""
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = ShoppingCartSerializer(
                recipe
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not ShoppingCart.objects.filter(user=user,
                                               recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт не был добавлен.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачивание списка покупок в формате TXT."""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Пользователь не авторизован.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user = self.request.user
        shopping_cart_recipes = Recipe.objects.filter(
            shopping_cart__user=user)

        if not shopping_cart_recipes.exists():
            return Response({'detail': 'Список покупок пуст.'},
                            status=status.HTTP_400_BAD_REQUEST)

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).order_by(
            'ingredient__name'
        ).annotate(
            total_quantity=Sum('amount')
        )

        lines = []
        for item in ingredients:
            lines.append(
                f"{item['ingredient__name']} - {item['total_quantity']} "
                f"{item['ingredient__measurement_unit']}\n"
            )

        file_content = "Необходимо купить:\n" + ''.join(lines)
        response = HttpResponse(file_content, content_type='text/plain')
        response['Content-Disposition'] = ('attachment;'
                                           'filename="shopping_cart.txt"')
        return response


@api_view(['GET'])
def get_short_link(request, recipe_id):
    """Получение-создание короткой ссылки для рецепта."""
    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        return Response({'detail': 'Рецепт не найден.'},
                        status=status.HTTP_404_NOT_FOUND)

    short_link, created = RecipeShortLink.objects.get_or_create(recipe=recipe)

    serializer = ShortLinkSerializer(short_link)
    return Response(serializer.data, status=status.HTTP_200_OK)
