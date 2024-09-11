from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Subscription, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Админ-модель пользователей"""
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'avatar_tag'
    )
    list_display_links = ('id', 'username',)
    search_fields = ('username', 'email')
    list_filter = ('username', 'email',)
    list_editable = (
        'email',
        'first_name',
        'last_name'
    )
    list_fields = ('first_name',)
    empty_value_display = '-пусто-'

    def avatar_tag(self, obj):
        if obj.avatar:
            return mark_safe(
                '<img src="{}" width="50" height="50" />'.format(
                    obj.avatar.url
                )
            )
        return None

    avatar_tag.short_description = 'Аватар'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-модель подписок"""
    list_display = (
        'id',
        'user',
        'author'
    )
    search_fields = (
        'user',
        'author'
    )
    list_editable = (
        'user',
        'author'
    )
    empty_value_display = '-пусто-'
