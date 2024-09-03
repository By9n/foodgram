from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import PageLimitPagination
from api.permissions import IsAuthorAdminAuthenticatedOrReadOnly
from api.serializers import (AvatarUserSerializer, CreateRecipeSerializer,
                             IngredientSerializer, RecipeSerializer,
                             ShortLinkSerializer, ShowFavoriteSerializer,
                             SubscriptionSerializer, TagSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            RecipeShortLink, ShoppingCart, Tag)
from users.models import Subscription, User


class UserViewSet(viewsets.GenericViewSet):
    """ViewSet модели пользователей"""
    queryset = User.objects.all()
    pagination_class = PageLimitPagination

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
        methods=['get'], url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def get_subscriptions(self, request, *args, **kwargs):
        """Просмотр листа подписок пользователя."""
        user = self.request.user
        author_ids = user.following.values_list('author_id', flat=True)
        subscriptions = User.objects.filter(id__in=author_ids)
        list = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(
            list, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True, methods=['POST'], url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def get_subscribe(self, request, pk=None):
        """Подписка на автора."""
        user = request.user
        author = get_object_or_404(User, pk=pk)
        serializer = SubscriptionSerializer(
            author,
            context={'request': request}
        )
        if user == author:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Subscription.objects.filter(user=user, author=author).exists():
            return Response(
                {'detail': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.create(user=user, author=author)
        serializer = SubscriptionSerializer(
            author, context={'request': request}
        )
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

    @get_subscribe.mapping.delete
    def delete_subscribe(self, request, pk=None):
        """Отписка от автора."""
        follower = request.user
        author = get_object_or_404(User, pk=pk)
        subscription = Subscription.objects.filter(
            user=follower, author=author)
        if not subscription.exists():
            return Response({'detail': 'Вы не подписаны на этого автора.'},
                            status=status.HTTP_400_BAD_REQUEST)
        del_count, _ = subscription.delete()
        if del_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Ошибка удаления подписки.'},
                        status=status.HTTP_400_BAD_REQUEST)


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
    permission_classes = (IsAuthorAdminAuthenticatedOrReadOnly, )
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

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавить рецепт в корзину пользователя."""
        self.model_class = ShoppingCart
        self.action_name = 'корзина'
        return self.add_to_list(request, pk)

    @shopping_cart.mapping.delete
    def remove_shopping_cart(self, request, pk=None):
        """Удалить рецепт из корзины пользователя."""
        self.model_class = ShoppingCart
        self.action_name = 'корзина'
        return self.remove_from_list(request, pk)

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
    recipe = get_object_or_404(Recipe, id=recipe_id)
    short_link, created = RecipeShortLink.objects.get_or_create(recipe=recipe)
    serializer = ShortLinkSerializer(short_link)
    return Response(serializer.data, status=status.HTTP_200_OK)
