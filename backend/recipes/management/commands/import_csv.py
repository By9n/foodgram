import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag

ModelsCSV = {
    Ingredient: 'ingredients.csv',
    Tag: 'tags.csv',
}

EXPECTED_HEADERS = {
    Ingredient: ['name', 'measurement_unit'],
    Tag: ['name', 'slug'],
}


class Command(BaseCommand):
    help = 'Импорт данных из csv файлов'

    def handle(self, *args, **options):
        for model, csv_file in ModelsCSV.items():
            model.objects.all().delete()
            path_to_file = f'{settings.CCSV_DIR}/{csv_file}'
            print(f'Начат импорт данных из файла {path_to_file}')

            with open(path_to_file, mode='r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                header = reader.fieldnames

                if header != EXPECTED_HEADERS[model]:
                    raise ValueError(
                        f'Неверный формат файла {
                            csv_file.name}: неправильные заголовки полей.'
                    )
                model.objects.bulk_create(model(**data) for data in reader)
            self.stdout.write(
                f'Завершен импорт данных в модель {model.__name__}')
        self.stdout.write('Импорт всех данных завершен.')
