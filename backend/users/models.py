from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH
from .validators import validate_alfanumeric_content, validate_username


class User(AbstractUser):
    """Модель переопределенного пользователя"""

    email = models.EmailField(
        verbose_name='E-mail',
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
    )
    username = models.CharField(
        verbose_name='Юзернейм',
        validators=[validate_username, ],
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        validators=[validate_alfanumeric_content, ],
        max_length=USERNAME_MAX_LENGTH,
    )

    last_name = models.CharField(
        verbose_name='Фамилия',
        validators=[validate_alfanumeric_content, ],
        max_length=USERNAME_MAX_LENGTH,
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='user/',
        null=True,
        default=None
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписот"""
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
        ordering = ('-user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscripting'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='selfsubscription_not_allowed'
            )
        ]

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
