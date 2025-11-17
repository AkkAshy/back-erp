"""
Скрипт для создания базовых единиц измерения и категорий через Django ORM
Запускать из корневой директории проекта: python populate_base_data.py
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from products.models import Unit, Category
from users.models import Store
from django.utils.text import slugify as django_slugify


def slugify(text):
    """Создает slug из кириллического текста"""
    # Таблица транслитерации кириллицы в латиницу
    transliteration_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
        'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    result = []
    for char in text.lower():
        result.append(transliteration_map.get(char, char))
    return django_slugify(''.join(result))


def create_base_data(schema_name):
    """Создает базовые данные для указанной схемы"""

    print(f"\n{'='*60}")
    print(f"Создание базовых данных для схемы: {schema_name}")
    print(f"{'='*60}\n")

    # Устанавливаем search_path для работы с нужной схемой
    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {schema_name}, public")

    # Единицы измерения
    units_data = [
        {"name": "Штука", "short_name": "шт", "description": "Поштучный учет"},
        {"name": "Килограмм", "short_name": "кг", "description": "Единица массы"},
        {"name": "Грамм", "short_name": "г", "description": "Единица массы"},
        {"name": "Литр", "short_name": "л", "description": "Единица объема"},
        {"name": "Миллилитр", "short_name": "мл", "description": "Единица объема"},
        {"name": "Метр", "short_name": "м", "description": "Единица длины"},
        {"name": "Упаковка", "short_name": "уп", "description": "Упаковка товара"},
    ]

    print("Создание единиц измерения:")
    print("-" * 60)
    for unit_data in units_data:
        try:
            unit, created = Unit.objects.using('default').get_or_create(
                name=unit_data["name"],
                defaults={
                    "short_name": unit_data["short_name"],
                    "description": unit_data["description"],
                    "is_active": True
                }
            )
            status = "✓ Создано" if created else "○ Уже существует"
            print(f"  {status}: {unit.name} ({unit.short_name})")
        except Exception as e:
            print(f"  ✗ Ошибка при создании '{unit_data['name']}': {e}")

    # Категории
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

    print("\nСоздание категорий:")
    print("-" * 60)
    for cat_data in categories_data:
        try:
            cat, created = Category.objects.using('default').get_or_create(
                name=cat_data["name"],
                defaults={
                    "slug": slugify(cat_data["name"]),
                    "description": cat_data["description"],
                    "is_active": True
                }
            )
            status = "✓ Создано" if created else "○ Уже существует"
            print(f"  {status}: {cat.name} (slug: {cat.slug})")
        except Exception as e:
            print(f"  ✗ Ошибка при создании '{cat_data['name']}': {e}")

    # Итоговая статистика
    print(f"\n{'='*60}")
    try:
        units_count = Unit.objects.using('default').count()
        categories_count = Category.objects.using('default').count()
        print(f"✓ Готово!")
        print(f"  Всего единиц измерения: {units_count}")
        print(f"  Всего категорий: {categories_count}")
    except Exception as e:
        print(f"Не удалось получить статистику: {e}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Получаем все магазины
    stores = Store.objects.all()

    if not stores.exists():
        print("\n✗ Магазины не найдены!")
        print("Сначала зарегистрируйте магазин через API.\n")
        exit(1)

    print("\nНайдены следующие магазины:")
    print("-" * 60)
    for idx, store in enumerate(stores, 1):
        print(f"{idx}. {store.name} (схема: {store.schema_name})")
    print("-" * 60)

    # Создаем данные для всех магазинов
    for store in stores:
        try:
            create_base_data(store.schema_name)
        except Exception as e:
            print(f"\n✗ Ошибка при создании данных для {store.name}: {e}\n")
            import traceback
            traceback.print_exc()
