from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly, SAFE_METHODS

)
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.decorators import action

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag, RecipeShortLink)
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageLimitPagination
from .permissions import AuthorOrStaffOrReadOnly
from .serializers import (
    CreateRecipeSerializer, FavoriteSerializer,
    IngredientSerializer, RecipeSerializer,
    ShortLinkSerializer,
    ShoppingCartSerializer, ShowSubscriptionsSerializer,
    SubscriptionSerializer, TagSerializer, TokenCreateSerializer,
    RecipeMinifiedSerializer, CustomUserSerializer,
    CreateCustomUserSerializer, UserSubscriptionSerializer,
    AvatarUserSerializer
)
from .shopping_list import shopping_list


class TokenCreateView(APIView):
    """
    Вьюсет для получения токена авторизации.
    """
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


class UserSubscriptionViewSet(UserViewSet):
    """Вьюсет создания и удаления подписки."""
    http_method_names = ['get', 'post', 'delete']
    pagination_class = PageLimitPagination

    @action(detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSubscriptionSerializer(page,
                                                    many=True,
                                                    context={'request': request})
            return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            serializer = UserSubscriptionSerializer(author,
                                                    data=request.data,
                                                    context={'request': request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=user,
                                        author=author)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            instance = get_object_or_404(Subscription,
                                         user=user,
                                         author=author)
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()


class CustomUserViewSet(UserViewSet):
    """ViewSet модели пользователей"""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    lookup_field = 'id'
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    permission_classes = [IsAuthenticatedOrReadOnly,]
    pagination_class = PageLimitPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCustomUserSerializer
        return CustomUserSerializer

    def get_subscribed_recipes(self, user):
        subscribed_users = user.following.all()
        subscribed_recipes = Recipe.objects.filter(
            author__in=subscribed_users
        )
        return subscribed_recipes

    def paginate_and_serialize(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True,
                context={'request': self.request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True,
            context={'request': self.request})
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        is_subscribed = request.query_params.get('is_subscribed', False)

        if is_subscribed:
            user = request.user
            queryset = User.objects.prefetch_related(
                'recipes').filter(subscriptions__user=user)
        else:
            queryset = User.objects.prefetch_related('recipes')

        return self.paginate_and_serialize(queryset)

    @action(detail=False, methods=['POST'])
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']

            if self.request.user.check_password(current_password):
                self.request.user.set_password(new_password)
                self.request.user.save()
                return Response(status=204)
            else:
                return Response({'detail': 'Пароли не совпадают.'},
                                status=400)
        else:
            return Response(serializer.errors, status=400)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        recipes_limit = self.request.query_params.get('recipes_limit', None)

        if recipes_limit is not None:
            recipes_queryset = instance.recipes.all()[:recipes_limit]
        else:
            recipes_queryset = instance.recipes.all()

        representation['recipes'] = RecipeMinifiedSerializer(recipes_queryset,
                                                             many=True).data
        return representation

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])  # IsAuthenticated
    def me(self, request, *args, **kwargs):
        """
        Получение информации о текущем аутентифицированном пользователе.
        """
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request, *args, **kwargs):
        """
        Добавления, обновления и удаления аватара пользователя.
        """
        user = request.user

        if request.method == 'PUT':
            serializer = AvatarUserSerializer(user, data=request.data)
            if not request.data.get('avatar'):
                return Response(
                    {'detail': 'Поле avatar обязательно.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_200_OK)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'detail': 'Аватар отсутствует.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    @action(detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSubscriptionSerializer(page,
                                                    many=True,
                                                    context={'request': request})
            return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            serializer = UserSubscriptionSerializer(author,
                                                    data=request.data,
                                                    context={'request': request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=user,
                                        author=author)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            instance = get_object_or_404(Subscription,
                                         user=user,
                                         author=author)
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

# class SubscribeView(APIView):
#     """ Операция подписки/отписки. """

#     permission_classes = [IsAuthenticated, ]

#     def post(self, request, id):
#         data = {
#             'user': request.user.id,
#             'author': id
#         }
#         serializer = SubscriptionSerializer(
#             data=data,
#             context={'request': request}
#         )
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, id):
#         author = get_object_or_404(User, id=id)
#         if Subscription.objects.filter(
#            user=request.user, author=author).exists():
#             subscription = get_object_or_404(
#                 Subscription, user=request.user, author=author
#             )
#             subscription.delete()
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         return Response(status=status.HTTP_400_BAD_REQUEST)


# class SubscriptionsView(ListAPIView):
#     """ Отображение подписок. """

#     permission_classes = [IsAuthenticated, ]
#     pagination_class = PageLimitPagination

#     def get(self, request):
#         user = request.user
#         queryset = User.objects.filter(author__user=user)
#         page = self.paginate_queryset(queryset)
#         serializer = ShowSubscriptionsSerializer(
#             page, many=True, context={'request': request}
#         )
#         return self.get_paginated_response(serializer.data)


class FavoriteView(APIView):
    """ Добавление/удаление рецепта из избранного. """

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
    """ Отображение тегов. """

    permission_classes = [AllowAny, ]
    pagination_class = None
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ Отображение ингредиентов. """

    permission_classes = [AllowAny, ]
    pagination_class = None
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = [IngredientFilter, ]
    search_fields = ['^name', ]


class RecipeViewSet(viewsets.ModelViewSet):
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

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = RecipeSerializer(recipe, data=request.data,
                                          context={"request": request})
            serializer.is_valid(raise_exception=True)
            if not Favorite.objects.filter(user=request.user,
                                           recipe=recipe).exists():
                Favorite.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт уже в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            get_object_or_404(Favorite, user=request.user,
                              recipe=recipe).delete()
            return Response({'detail': 'Рецепт успешно удален из избранного.'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """ 
        Добавить или удалить рецепт из списка покупок текущего пользователя. 
        Использует метод запроса для определения действия: 
        - POST: добавить рецепт в список покупок 
        - DELETE: удалить рецепт из списка покупок 
        """
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен в список покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = ShoppingCartSerializer(
                recipe
            )  # RecipeResponseSerializer
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not ShoppingCart.objects.filter(user=user,
                                               recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт не был добавлен в список покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    # @action(detail=True, methods=['post', 'delete'],
    #         permission_classes=(IsAuthenticated,),
    #         pagination_class=None)
    # def get_shopping_cart(self, request, **kwargs):
    #     recipe = get_object_or_404(Recipe, id=kwargs['id'])

    #     if request.method == 'POST':
    #         serializer = RecipeSerializer(recipe, data=request.data,
    #                                       context={"request": request})
    #         serializer.is_valid(raise_exception=True)
    #         if not ShoppingCart.objects.filter(user=request.user,
    #                                             recipe=recipe).exists():
    #             ShoppingCart.objects.create(user=request.user, recipe=recipe)
    #             return Response(serializer.data,
    #                             status=status.HTTP_201_CREATED)
    #         return Response({'errors': 'Рецепт уже в списке покупок.'},
    #                         status=status.HTTP_400_BAD_REQUEST)

    #     if request.method == 'DELETE':
    #         get_object_or_404(ShoppingCart, user=request.user,
    #                           recipe=recipe).delete()
    #         return Response(
    #             {'detail': 'Рецепт успешно удален из списка покупок.'},
    #             status=status.HTTP_204_NO_CONTENT
    #         )

    # @action(detail=False, methods=['get'],
    #         permission_classes=(IsAuthenticated,))
    # def download_shopping_cart(self, request, **kwargs):
    #     ingredients = (
    #         RecipeIngredient.objects
    #         .filter(recipe__shopping_recipe__user=request.user)
    #         .values('ingredient')
    #         .annotate(total_amount=Sum('amount'))
    #         .values_list('ingredient__name', 'total_amount',
    #                      'ingredient__measurement_unit')
    #     )
    #     file_list = []
    #     [file_list.append(
    #         '{} - {} {}.'.format(*ingredient)) for ingredient in ingredients]
    #     file = HttpResponse('Cписок покупок:\n' + '\n'.join(file_list),
    #                         content_type='text/plain')
    #     file['Content-Disposition'] = (f'attachment; filename={'foodgram'}')
    #     return file


@api_view(['GET'])
def get_short_link(request, recipe_id):
    """
    Получение или создание короткой ссылки для рецепта.
    """
    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        return Response({'detail': 'Рецепт не найден.'},
                        status=status.HTTP_404_NOT_FOUND)

    short_link, created = RecipeShortLink.objects.get_or_create(recipe=recipe)

    serializer = ShortLinkSerializer(short_link)
    return Response(serializer.data, status=status.HTTP_200_OK)


# @action(detail=True, methods=['post', 'delete'],
#             permission_classes=(IsAuthenticated,),
#             pagination_class=None)
# def get_shopping_cart(self, request, **kwargs):
#     recipe = get_object_or_404(Recipe, id=kwargs['pk'])

#     if request.method == 'POST':
#         serializer = RecipeSerializer(recipe, data=request.data,
#                                         context={"request": request})
#         serializer.is_valid(raise_exception=True)
#         if not ShoppingCart.objects.filter(user=request.user,
#                                             recipe=recipe).exists():
#             ShoppingCart.objects.create(user=request.user, recipe=recipe)
#             return Response(serializer.data,
#                             status=status.HTTP_201_CREATED)
#         return Response({'errors': 'Рецепт уже в списке покупок.'},
#                         status=status.HTTP_400_BAD_REQUEST)

#     if request.method == 'DELETE':
#         get_object_or_404(ShoppingCart, user=request.user,
#                             recipe=recipe).delete()
#         return Response(
#             {'detail': 'Рецепт успешно удален из списка покупок.'},
#             status=status.HTTP_204_NO_CONTENT
#         )

# class ShoppingCartView(APIView):
#     """ Добавление рецепта в корзину или его удаление. """

#     permission_classes = [IsAuthenticated, ]

#     def post(self, request, id):
#         id = int(id)
#         data = {
#             'user': request.user.id,
#             'recipe': id
#         }
#         recipe = get_object_or_404(Recipe, id=id)
#         if not ShoppingCart.objects.filter(
#            user=request.user, recipe=recipe).exists():
#             serializer = ShoppingCartSerializer(
#                 data=data, context={'request': request}
#             )
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(
#                     serializer.data, status=status.HTTP_201_CREATED)
#         return Response(status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, id):
#         id = int(id)
#         recipe = get_object_or_404(Recipe, id=(id))
#         if ShoppingCart.objects.filter(
#            user=request.user, recipe=recipe).exists():
#             ShoppingCart.objects.filter(
#                 user=request.user, recipe=recipe
#             ).delete()
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         return Response(status=status.HTTP_400_BAD_REQUEST)


# @api_view(['GET'])
# def get_download_shopping_cart(request):
#     ingredient_list = "Cписок покупок:"
#     ingredients = RecipeIngredient.objects.filter(
#         recipe__shopping_cart__user=request.user
#     ).values(
#         'ingredient__name', 'ingredient__measurement_unit'
#     ).annotate(amount=Sum('amount'))
#     for num, i in enumerate(ingredients):
#         ingredient_list += (
#             f"\n{i['ingredient__name']} - "
#             f"{i['amount']} {i['ingredient__measurement_unit']}"
#         )
#         if num < ingredients.count() - 1:
#             ingredient_list += ', '
#     file = 'shopping_list'
#     response = HttpResponse(ingredient_list, 'Content-Type: application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="{file}.pdf"'
#     return response
