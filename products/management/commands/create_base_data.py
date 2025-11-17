"""
Management command для создания базовых данных (категории, единицы измерения)
"""
from django.core.management.base import BaseCommand
from django.db import connection
from users.models import Store
from products.models import Unit, Category
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Создает базовые категории и единицы измерения для tenant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--schema',
            type=str,
            help='Имя схемы tenant (например: tenant_asc)',
        )

    def handle(self, *args, **options):
        schema_name = options.get('schema')

        if schema_name:
            # Используем указанную схему
            stores = Store.objects.filter(schema_name=schema_name)
            if not stores.exists():
                self.stdout.write(self.style.ERROR(f'Схема {schema_name} не найдена'))
                return
            store = stores.first()
        else:
            # Используем первый найденный магазин
            store = Store.objects.first()
            if not store:
                self.stdout.write(self.style.ERROR('Магазины не найдены'))
                return
            schema_name = store.schema_name

        self.stdout.write(f'Создаем данные для магазина: {store.name} (схема: {schema_name})')

        # Переключаемся на схему tenant
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {schema_name}')

        # Создаем единицы измерения
        units_data = [
            {"name": "Штука", "short_name": "шт", "description": "Поштучный учет"},
            {"name": "Килограмм", "short_name": "кг", "description": "Единица массы"},
            {"name": "Грамм", "short_name": "г", "description": "Единица массы"},
            {"name": "Литр", "short_name": "л", "description": "Единица объема"},
            {"name": "Миллилитр", "short_name": "мл", "description": "Единица объема"},
            {"name": "Метр", "short_name": "м", "description": "Единица длины"},
            {"name": "Упаковка", "short_name": "уп", "description": "Упаковка товара"},
        ]

        self.stdout.write('\nСоздаем единицы измерения...')
        for unit_data in units_data:
            unit, created = Unit.objects.get_or_create(
                name=unit_data["name"],
                defaults={
                    "short_name": unit_data["short_name"],
                    "description": unit_data["description"]
                }
            )
            status = "✓ Создано" if created else "- Уже существует"
            self.stdout.write(f'  {status}: {unit.name} ({unit.short_name})')

        # Создаем базовые категории
        categories_data = [
            {"name": "Одежда", "description": "Одежда и текстиль"},
            {"name": "Обувь", "description": "Обувь всех видов"},
            {"name": "Аксессуары", "description": "Аксессуары и украшения"},
            {"name": "Электроника", "description": "Электронные товары"},
            {"name": "Продукты питания", "description": "Продукты и напитки"},
            {"name": "Косметика", "description": "Косметика и парфюмерия"},
            {"name": "Спорт", "description": "Спортивные товары"},
            {"name": "Дом и сад", "description": "Товары для дома и сада"},
        ]

        self.stdout.write('\nСоздаем категории...')
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_data["name"],
                defaults={
                    "slug": slugify(cat_data["name"]),
                    "description": cat_data["description"]
                }
            )
            status = "✓ Создано" if created else "- Уже существует"
            self.stdout.write(f'  {status}: {cat.name} (slug: {cat.slug})')

        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✓ Готово! Всего единиц измерения: {Unit.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Готово! Всего категорий: {Category.objects.count()}'))
        self.stdout.write('='*50)
