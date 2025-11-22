"""
Management command для создания таблицы products_category_attribute во всех tenant-схемах.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from users.models import Store


class Command(BaseCommand):
    help = 'Создать таблицу products_category_attribute во всех tenant-схемах'

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS products_category_attribute (
        id SERIAL PRIMARY KEY,
        category_id INTEGER NOT NULL,
        attribute_id INTEGER NOT NULL,
        is_required BOOLEAN NOT NULL DEFAULT FALSE,
        is_variant BOOLEAN NOT NULL DEFAULT FALSE,
        "order" INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

        CONSTRAINT products_category_attribute_category_id_attribute_id_key
            UNIQUE (category_id, attribute_id)
    );

    CREATE INDEX IF NOT EXISTS products_category_attribute_category_id_idx
        ON products_category_attribute (category_id);

    CREATE INDEX IF NOT EXISTS products_category_attribute_attribute_id_idx
        ON products_category_attribute (attribute_id);
    """

    def handle(self, *args, **options):
        stores = Store.objects.all().order_by('name')

        self.stdout.write(f"Найдено магазинов: {stores.count()}")
        self.stdout.write("="*60)

        success_count = 0
        error_count = 0

        for store in stores:
            schema_name = store.schema_name
            self.stdout.write(f"\n📦 {store.name} ({schema_name})")

            try:
                with connection.cursor() as cursor:
                    # Переключаемся на схему
                    cursor.execute(f'SET search_path TO "{schema_name}", public')

                    # Создаём таблицу
                    cursor.execute(self.CREATE_TABLE_SQL)

                    # Проверяем что таблица создалась
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = 'products_category_attribute'
                    """, [schema_name])

                    if cursor.fetchone()[0] > 0:
                        self.stdout.write(self.style.SUCCESS(f"   ✅ Таблица создана успешно"))
                        success_count += 1
                    else:
                        self.stdout.write(self.style.ERROR(f"   ❌ Таблица не найдена после создания"))
                        error_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Ошибка: {e}"))
                error_count += 1

        self.stdout.write("\n" + "="*60)
        self.stdout.write(f"ИТОГО:")
        self.stdout.write(self.style.SUCCESS(f"  ✅ Успешно: {success_count}"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"  ❌ Ошибок: {error_count}"))
        self.stdout.write("="*60)
