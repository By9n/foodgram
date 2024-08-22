from re import match

from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError


def validate_alfanumeric_content(data):
    if not match(r'^[A-Za-z0-9]*$', data):
        raise ValidationError(
            'Имя пользователя должно содержать только буквы и цифры.'
        )


validate_username = UnicodeUsernameValidator()
