from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.db.models import Field


@deconstructible
class SlugValidator(Field):
    def init(self, regex, message=None):
         self.regex = regex
         self.message = (message 
         or 'Slug должен соответствовать регулярному выражению %s' % regex
        )
    def validate(self, value, modelinstance):
        if not self.regex.match(value):
            raise ValidationError(self.message)