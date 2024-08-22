
import re

from django.core.exceptions import ValidationError


def validate_name(value):
    if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s\-.()]*$', value):
        raise ValidationError(
            'Недопустимые символы в имени рецепта. ($%^&#:;!)')
