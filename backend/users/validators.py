from re import match

from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError


def validate_alfanumeric_content(data):
    if not match(r'^[a-zA-Zа-яА-ЯёЁ\s\-.()]*$', data):
        raise ValidationError(
            'Недопустимые символы в имени рецепта. ($%^&#:;!).'
        )


validate_username = UnicodeUsernameValidator()
