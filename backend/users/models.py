from django.contrib.auth.models import AbstractUser
from django.db import models
# from django.utils.translation import gettext_lazy as _

from .constants import (
    USERNAME_MAX_LENGTH, EMAIL_MAX_LENGTH, ROLE_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
)
from .validators import (validate_correct_username, validate_username)

class UserRoles(models.TextChoices):
    USER = "user"
    ADMIN = "admin"


class User(AbstractUser):
    """Модель переопределенного пользователя"""

    username = models.CharField(
        verbose_name='Логин',
        validators=[validate_correct_username, validate_username],
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        blank=False
    )
    email = models.EmailField(
        verbose_name='E-mail',
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        blank=False
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=USERNAME_MAX_LENGTH,
        blank=False
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=USERNAME_MAX_LENGTH,
        blank=False
    )
    is_subscribed = models.BooleanField(
        verbose_name='Подписаться на автора',
        default=False,
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=PASSWORD_MAX_LENGTH,
        blank=False,
    )
    role = models.CharField(
        verbose_name='Роль пользователя',
        max_length=ROLE_MAX_LENGTH,
        default=UserRoles.USER,
        choices=UserRoles.choices,
    )
    following = models.ManyToManyField(
        "self",
        through='Subscription',
        through_fields=('user', 'author'),
        symmetrical=False,
        related_name='following_relationships'
    )
    image = models.ImageField(
        upload_to='media/user/', 
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
    """Модель подписок"""
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='subscribers'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='followed_by'
    )

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscripting'
            ),
        ]

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
