import string, random

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User
from .validators import  validateslug
from .constants import (
    MAX_LENGTH_NAME_RECIPE, MAX_LENGTH_TAG, 
)




class Tag(models.Model):
    """Модель тегов"""
    name = models.CharField(
        verbose_name='Название тега',
        max_length=MAX_LENGTH_TAG,
        unique=True,
        blank=False,
    )
    slug = models.SlugField(
        verbose_name='slug',
        validators=[validateslug],
        max_length=MAX_LENGTH_TAG,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('id',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов"""
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Список тегов',
        help_text='Поставьте теги',
    )
    author = models.ForeignKey(
        get_user_model(),
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        verbose_name='Список ингредиентов',
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        help_text='Выберете ингредиенты'
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_NAME_RECIPE,
        help_text='Введите название рецепта'
    )
    image = models.ImageField(
        verbose_name='Ссылка на картинку на сайте',
        upload_to='rescipes/image/',
        null=True,
        help_text='Загрузите картинку'
    )
    text = models.CharField(
        verbose_name='Описание',
        max_length=1256,
        help_text='Составьте описание'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                1,
                'Минимальное время готовки - одна минуты'
            ),
            MaxValueValidator(
                1440,
                'Время готовки не больше 24 часов'
            )
        ],
        help_text='Введите время готовки (мин.)'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-id',)
        default_related_name = 'recipes'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов"""
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=128,
        blank=False,
        help_text='Введите название ингредиента'
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=64,
        blank=False,
        help_text='Введите единицы измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient')
        ]


class RecipeIngredient(models.Model):
    """Модель рецепты_ингредиенты"""
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='recipe_ingredients',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        related_name='recipe_ingredients',
        on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                1,
                'Количество не должно быть меньше 1'
            ),
            MaxValueValidator(
                666666,
                'Количество не должно быть больше 666666'
            )
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('id',)
        unique_together = ('recipe', 'ingredient')


class RecipeTag(models.Model):
    """ Модель связи тега и рецепта. """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tag'],
                name='recipe_tag_unique'
            )
        ]


class Favorite(models.Model):
    """Модель избранных рецептов"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites_user',
        verbose_name='Пользователь',
        help_text='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites_recipe',
        related_query_name='favorites',
        verbose_name='Рецепт',
        help_text='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} >> {self.recipe}'


class ShoppingCart(models.Model):
    """ Модель корзины покупок """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
        help_text='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
        help_text='Рецепт',
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart')
        ]
    
    def __str__(self):
        return f'{self.user} >> {self.recipe}'


class RecipeShortLink(models.Model):
    """Модель коротких ссылок на рецепты."""

    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE,
                                  related_name='short_link')
    short_link = models.CharField(max_length=3, unique=True,
                                  blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)

    def generate_short_link(self):
        length = 3
        characters = string.ascii_letters + string.digits
        while True:
            short_link = ''.join(random.choices(characters, k=length))
            if not RecipeShortLink.objects.filter(short_link=short_link).exists():
                break
        return short_link