from io import BytesIO
from django.contrib.auth.models import User
from django.db.models import Sum
from recipes.models import Recipe, RecipeIngredient


def get_shopping_list(user: User) -> BytesIO:
    """
    Генерирует список покупок для пользователя.
    И возвращает его в виде объекта BytesIO.
    """
    shopping_cart_recipes = Recipe.objects.filter(shopping_carts__user=user)

    if not shopping_cart_recipes.exists():
        raise ValueError("Список покупок пуст.")

    ingredients = RecipeIngredient.objects.filter(
        recipe__in=shopping_cart_recipes
    ).values(
        'ingredient__name',
        'ingredient__measurement_unit'
    ).annotate(
        total_quantity=Sum('amount')
    )

    file_content = "Необходимо купить:\n"
    for item in ingredients:
        file_content += (f"{item['ingredient__name']} - "
                         f"{item['total_quantity']} "
                         f"{item['ingredient__measurement_unit']}\n")

    file_buffer = BytesIO(file_content.encode('utf-8'))
    return file_buffer
