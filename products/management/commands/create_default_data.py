"""
Management command для создания дефолтных данных в магазине.

Создает:
- Базовые единицы измерения (шт, кг, л и др.)
- Базовые категории товаров

Usage:
    python manage.py create_default_data --store test_shop
"""

from django.core.management.base import BaseCommand
from django.db import connection
from users.models import Store
from products.models import Unit, Category


class Command(BaseCommand):
    help = 'Создает дефолтные данные (категории и единицы) для магазина'

    def add_arguments(self, parser):
        parser.add_argument(
            '--store',
            type=str,
            required=True,
            help='Slug магазина',
        )

    def handle(self, *args, **options):
        store_slug = options.get('store')

        # Получаем магазин
        try:
            store = Store.objects.get(slug=store_slug)
        except Store.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Магазин "{store_slug}" не найден'))
            return

        self.stdout.write(f'\n📦 Создание дефолтных данных для {store.name}...')
        self.stdout.write(f'   Schema: {store.schema_name}\n')

        # Переключаемся на tenant схему
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{store.schema_name}", public')

        try:
            # Создаем единицы измерения
            self.stdout.write('📏 Создание единиц измерения...')
            units_data = [
                {'name': 'штука', 'short_name': 'шт'},
                {'name': 'килограмм', 'short_name': 'кг'},
                {'name': 'грамм', 'short_name': 'г'},
                {'name': 'литр', 'short_name': 'л'},
                {'name': 'миллилитр', 'short_name': 'мл'},
                {'name': 'метр', 'short_name': 'м'},
                {'name': 'упаковка', 'short_name': 'уп'},
                {'name': 'коробка', 'short_name': 'кор'},
                {'name': 'пара', 'short_name': 'пар'},
                {'name': 'набор', 'short_name': 'наб'},
            ]

            units_created = 0
            for unit_data in units_data:
                unit, created = Unit.objects.get_or_create(
                    name=unit_data['name'],
                    defaults={'short_name': unit_data['short_name']}
                )
                if created:
                    units_created += 1
                    self.stdout.write(f'   ✓ {unit.name} ({unit.short_name})')
                else:
                    self.stdout.write(f'   ⊙ {unit.name} (уже есть)')

            # Создаем категории
            self.stdout.write('\n📁 Создание категорий...')
            categories_data = [
                {'name': 'Продукты питания', 'slug': 'food'},
                {'name': 'Напитки', 'slug': 'beverages'},
                {'name': 'Молочные продукты', 'slug': 'dairy'},
                {'name': 'Хлебобулочные изделия', 'slug': 'bakery'},
                {'name': 'Мясо и птица', 'slug': 'meat'},
                {'name': 'Овощи и фрукты', 'slug': 'fruits-vegetables'},
                {'name': 'Кондитерские изделия', 'slug': 'confectionery'},
                {'name': 'Бытовая химия', 'slug': 'household-chemicals'},
                {'name': 'Личная гигиена', 'slug': 'personal-care'},
                {'name': 'Канцелярия', 'slug': 'stationery'},
                {'name': 'Хозтовары', 'slug': 'household-goods'},
                {'name': 'Одежда', 'slug': 'clothing'},
                {'name': 'Обувь', 'slug': 'footwear'},
                {'name': 'Электроника', 'slug': 'electronics'},
                {'name': 'Игрушки', 'slug': 'toys'},
                {'name': 'Разное', 'slug': 'other'},
            ]

            categories_created = 0
            for cat_data in categories_data:
                category, created = Category.objects.get_or_create(
                    slug=cat_data['slug'],
                    defaults={'name': cat_data['name']}
                )
                if created:
                    categories_created += 1
                    self.stdout.write(f'   ✓ {category.name}')
                else:
                    self.stdout.write(f'   ⊙ {category.name} (уже есть)')

            # Итоги
            self.stdout.write('\n' + '='*60)
            self.stdout.write(f'Единиц измерения создано: {units_created}')
            self.stdout.write(f'Категорий создано: {categories_created}')
            self.stdout.write('='*60)

            if units_created > 0 or categories_created > 0:
                self.stdout.write(self.style.SUCCESS('\n✅ Дефолтные данные успешно созданы!'))
            else:
                self.stdout.write(self.style.WARNING('\n⊙ Все данные уже существовали'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Ошибка: {e}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))

        finally:
            # Возвращаем схему обратно
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO public')
