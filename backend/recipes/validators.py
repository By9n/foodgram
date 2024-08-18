import re

from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db.models import Field
from django.utils import timezone


class SlugValidator(Field):
    def init(self, regex, message=None):
        self.regex = regex
        self.message = (message
                        or 'Slug должен соответствовать '
                           'регулярному выражению %s' % regex
                        )

    def validate(self, value, modelinstance):
        if not self.regex.match(value):
            raise ValidationError(self.message)


def validateslug(slug):
    pattern = re.compile('^[a-zA-Z0-9]+$')
    return pattern.match(slug) is not None


def validate_correct_username(data):
    if data.lower() == 'me':
        raise ValidationError(
            f'Никнэйм пользователя не должен быть {data}'
        )


def validate_year(data):
    if data >= timezone.now().year:
        raise ValidationError(
            'Год выпуска произведения не может быть больше текущего.'
        )


validate_username = UnicodeUsernameValidator()
