import io

from django.apps import apps
from django.contrib.auth import authenticate
from django.db.models import Sum
from django.db.models.aggregates import Sum
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            RecipeShortLink, ShoppingCart, Tag)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import filters, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view
from rest_framework.generics import ListAPIView
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageLimitPagination
from .permissions import AuthorOrStaffOrReadOnly
from .serializers import (AvatarUserSerializer, CreateCustomUserSerializer,
                          CreateRecipeSerializer, CustomUserSerializer,
                          FavoriteSerializer, IngredientSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          ShortLinkSerializer, ShowFavoriteSerializer,
                          SubscriptionSerializer, TagSerializer,
                          TokenCreateSerializer)
from .shopping_list import shopping_list


class TokenCreateView(APIView):
    """Вьюсет для получения токена авторизации."""
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
        if self.action in ('create', 'retrieve', 'list'):
            self.permission_classes = (AllowAny, )
        else:
            self.permission_classes = (IsAuthenticatedOrReadOnly, )
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCustomUserSerializer
        elif self.action == 'retrieve':
            return CustomUserSerializer
        elif self.action == 'list':
            return CustomUserSerializer
        return super().get_serializer_class()

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        """
        Получение информации о текущем аутентифицированном пользователе.
        """
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


    # def get_permissions(self, request):
    #     if self.action in ('create', 'list'):
    #         self.permission_classes = (AllowAny,)
    #     else:
    #         self.permission_classes = (IsAuthenticated,)
    #     return super().get_permissions()

    @action(detail=False, methods=['put'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request, *args, **kwargs):
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
        detail=False, methods=['GET']  # , permission_classes=[IsAuthenticated], 
    )
    def subscriptions(self, request, *args, **kwargs):
        # """Просмотр листа подписок пользователя."""
        # user = self.request.user
        # # subscriptions = User.objects.filter(subscriptions__user=user)
        # subscriptions = user.subscription.select_related( 'author' )
        # list = self.paginate_queryset(subscriptions)
        # serializer = SubscriptionSerializer(
        #     list,
        #     many=True,
        #     context={'request': request}
        # )
        # return self.get_paginated_response(serializer.data)
        return Response(
                {'detail': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
    """ Добавление/удаление рецепта из избранного."""

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
    """ Отображение тегов."""

    permission_classes = [AllowAny, ]
    pagination_class = None
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ Отображение ингредиентов."""

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

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
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

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавить\удалить рецепт из списка покупок пользователя."""
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = ShoppingCartSerializer(recipe)
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

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        """Скачиваем список с ингредиентами."""
        buffer = io.BytesIO()
        page = canvas.Canvas(buffer)
        pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf'))
        x_position, y_position = 50, 800
        shopping_cart = (
            request.user.shopping_cart.recipe.
            values(
                'ingredients__name',
                'ingredients__measurement_unit'
            ).annotate(amount=Sum('recipe__amount')).order_by())
        page.setFont('Vera', 14)
        if shopping_cart:
            indent = 20
            page.drawString(x_position, y_position, 'Cписок покупок:')
            for index, recipe in enumerate(shopping_cart, start=1):
                page.drawString(
                    x_position, y_position - indent,
                    f'{index}. {recipe["ingredients__name"]} - '
                    f'{recipe["amount"]} '
                    f'{recipe["ingredients__measurement_unit"]}.')
                y_position -= 15
                if y_position <= 50:
                    page.showPage()
                    y_position = 800
            page.save()
            buffer.seek(0)
            return FileResponse(
                buffer, as_attachment=True, filename='cart')
        page.setFont('Vera', 24)
        page.drawString(
            x_position,
            y_position,
            'Cписок покупок пуст!')
        page.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='cart')




@api_view(['GET'])
def get_short_link(request, recipe_id):
    """Получение\создание короткой ссылки для рецепта."""
    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        return Response({'detail': 'Рецепт не найден.'},
                        status=status.HTTP_404_NOT_FOUND)

    short_link, created = RecipeShortLink.objects.get_or_create(recipe=recipe)

    serializer = ShortLinkSerializer(short_link)
    return Response(serializer.data, status=status.HTTP_200_OK)
