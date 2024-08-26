# Generated by Django 3.2.3 on 2024-08-26 12:46

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import users.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Избранное',
                'verbose_name_plural': 'Избранное',
                'abstract': False,
                'default_related_name': 'favorites',
            },
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Введите название ингредиента', max_length=128, validators=[users.validators.validate_alfanumeric_content], verbose_name='Название ингредиента')),
                ('measurement_unit', models.CharField(help_text='Введите единицы измерения', max_length=64, verbose_name='Единица измерения')),
            ],
            options={
                'verbose_name': 'Ингредиент',
                'verbose_name_plural': 'Ингредиенты',
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Введите название рецепта', max_length=256, validators=[users.validators.validate_alfanumeric_content], verbose_name='Название')),
                ('image', models.ImageField(help_text='Загрузите картинку', null=True, upload_to='rescipes/image/', verbose_name='Ссылка на картинку на сайте')),
                ('text', models.CharField(help_text='Составьте описание', max_length=1256, verbose_name='Описание')),
                ('cooking_time', models.PositiveIntegerField(help_text='Введите время готовки (мин.)', validators=[django.core.validators.MinValueValidator(1, 'Минимальное время готовки - одна минуты'), django.core.validators.MaxValueValidator(1440, 'Время готовки не больше 24 часов')], verbose_name='Время приготовления (в минутах)')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipes', to=settings.AUTH_USER_MODEL, verbose_name='Автор рецепта')),
            ],
            options={
                'verbose_name': 'Рецепт',
                'verbose_name_plural': 'Рецепты',
                'ordering': ('-id',),
                'default_related_name': 'recipes',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, unique=True, validators=[users.validators.validate_alfanumeric_content], verbose_name='Название тега')),
                ('slug', models.SlugField(max_length=32, unique=True, verbose_name='slug')),
            ],
            options={
                'verbose_name': 'Тег',
                'verbose_name_plural': 'Теги',
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='ShoppingCart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_cart', to='recipes.recipe', verbose_name='Рецепт')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_cart', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Корзина',
                'verbose_name_plural': 'Корзина',
                'abstract': False,
                'default_related_name': 'shopping_cart',
            },
        ),
        migrations.CreateModel(
            name='RecipeShortLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_link', models.CharField(blank=True, max_length=3, null=True, unique=True)),
                ('recipe', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='short_link', to='recipes.recipe')),
            ],
        ),
        migrations.CreateModel(
            name='RecipeIngredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1, 'Количество не должно быть меньше 1'), django.core.validators.MaxValueValidator(666666, 'Количество не должно быть больше 666666')], verbose_name='Количество')),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='recipes.ingredient', verbose_name='Ингредиент')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.recipe', verbose_name='Рецепт')),
            ],
            options={
                'verbose_name': 'Ингредиент',
                'verbose_name_plural': 'Ингредиенты',
                'ordering': ('id',),
            },
        ),
        migrations.AddField(
            model_name='recipe',
            name='tags',
            field=models.ManyToManyField(help_text='Поставьте теги', related_name='recipes', to='recipes.Tag', verbose_name='Список тегов'),
        ),
        migrations.AddConstraint(
            model_name='ingredient',
            constraint=models.UniqueConstraint(fields=('name', 'measurement_unit'), name='unique_ingredient'),
        ),
        migrations.AddField(
            model_name='favorite',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to='recipes.recipe', verbose_name='Рецепт'),
        ),
        migrations.AddField(
            model_name='favorite',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AddConstraint(
            model_name='shoppingcart',
            constraint=models.UniqueConstraint(fields=('user', 'recipe'), name='recipes_shoppingcart_unique'),
        ),
        migrations.AlterUniqueTogether(
            name='recipeingredient',
            unique_together={('recipe', 'ingredient')},
        ),
        migrations.AddConstraint(
            model_name='favorite',
            constraint=models.UniqueConstraint(fields=('user', 'recipe'), name='recipes_favorite_unique'),
        ),
    ]
