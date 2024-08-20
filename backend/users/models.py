from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import EMAIL_MAX_LENGTH, ROLE_MAX_LENGTH, USERNAME_MAX_LENGTH
from .validators import validate_correct_username, validate_username


class UserRoles(models.TextChoices):
    USER = "user"
    ADMIN = "admin"


class User(AbstractUser):
    """Модель переопределенного пользователя"""

    email = models.EmailField(
        verbose_name='E-mail',
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        blank=False
    )
    username = models.CharField(
        verbose_name='Юзернейм',
        validators=[validate_correct_username, validate_username],
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        blank=False
    )
    first_name = models.CharField(
        verbose_name='Имя',
        validators=[validate_username,],
        max_length=USERNAME_MAX_LENGTH,
        blank=False
    )

    last_name = models.CharField(
        verbose_name='Фамилия',
        validators=[validate_username,],
        max_length=USERNAME_MAX_LENGTH,
        blank=False
    )
    role = models.CharField(
        verbose_name='Роль пользователя',
        max_length=ROLE_MAX_LENGTH,
        default=UserRoles.USER,
        choices=UserRoles.choices,
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

    @property
    def is_user(self):
        return self.role == UserRoles.USER

    @property
    def is_admin(self):
        return (self.role == UserRoles.ADMIN
                or self.is_superuser
                or self.is_staff
                )

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
        ]

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
