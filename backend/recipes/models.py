import uuid

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from recipes.constants import (MAX_AMOUNT_INGREDIENT, MAX_COOKING_TIME,
                               MAX_LENGTH_MEASUREMENT_UNIT,
                               MAX_LENGTH_NAME_INGREDIENT,
                               MAX_LENGTH_NAME_RECIPE, MAX_LENGTH_SHORT_LINK,
                               MAX_LENGTH_TAG, MAX_LENGTH_TEXT_RECIPE,
                               MIN_AMOUNT_INGREDIENT, MIN_COOKING_TIME)
from users.validators import validate_alfanumeric_content

User = get_user_model()


class Tag(models.Model):
    """Модель тегов"""
    name = models.CharField(
        verbose_name='Название тега',
        validators=[validate_alfanumeric_content, ],
        max_length=MAX_LENGTH_TAG,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='slug',
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
        User,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(
        verbose_name='Название',
        validators=[validate_alfanumeric_content, ],
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
        max_length=MAX_LENGTH_TEXT_RECIPE,
        help_text='Составьте описание'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                'Минимальное время готовки - одна минуты'
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
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
        validators=[validate_alfanumeric_content, ],
        max_length=MAX_LENGTH_NAME_INGREDIENT,
        help_text='Введите название ингредиента'
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=MAX_LENGTH_MEASUREMENT_UNIT,
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

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель рецепты_ингредиенты"""
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        related_name='+',
        on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                MIN_AMOUNT_INGREDIENT,
                'Количество не должно быть меньше 1'
            ),
            MaxValueValidator(
                MAX_AMOUNT_INGREDIENT,
                'Количество не должно быть больше 666666'
            )
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('id',)
        unique_together = ('recipe', 'ingredient')


class FavoriteShoppingCart(models.Model):
    """ Связывающая модель списка покупок и избранного. """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',

    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(app_label)s_%(class)s_unique'
            )
        ]

    def __str__(self):
        return f'{self.user} >> {self.recipe}'


class Favorite(FavoriteShoppingCart):
    """ Модель добавление в избраное. """

    class Meta(FavoriteShoppingCart.Meta):
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(FavoriteShoppingCart):
    """ Модель списка покупок. """

    class Meta(FavoriteShoppingCart.Meta):
        default_related_name = 'shopping_cart'
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'


class RecipeShortLink(models.Model):
    """Модель коротких ссылок на рецепты."""
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='short_link'
    )
    short_link = models.CharField(
        max_length=MAX_LENGTH_SHORT_LINK,
        unique=True,
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)

    def generate_short_link(self):
        short_link = uuid.uuid4().hex[:MAX_LENGTH_SHORT_LINK]
        return short_link
