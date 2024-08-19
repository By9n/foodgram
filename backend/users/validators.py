from re import match

from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError


def validate_correct_username(data):
    if data.lower() == 'me':
        raise ValidationError(
            f'Никнэйм пользователя не должен быть {data}'
        )

def validate_alfanumeric_username(data):
    if not match(r'^[A-Za-z0-9]*$', data):
        raise ValidationError(
            'Имя пользователя должно содержать только буквы и цифры.'
        )

validate_username = UnicodeUsernameValidator()
