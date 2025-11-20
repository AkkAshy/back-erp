"""
Management command для применения миграций ко всем tenant схемам.

Usage:
    python manage.py migrate_tenant_schemas
    python manage.py migrate_tenant_schemas --store test_shop
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from users.models import Store
import sys


class Command(BaseCommand):
    help = 'Применяет миграции ко всем tenant схемам'

    def add_arguments(self, parser):
        parser.add_argument(
            '--store',
            type=str,
            help='Slug конкретного магазина (опционально)',
        )
        parser.add_argument(
            '--skip-public',
            action='store_true',
            help='Не применять миграции к public схеме перед tenant схемами',
        )

    def handle(self, *args, **options):
        store_slug = options.get('store')
        skip_public = options.get('skip_public', False)

        # Сначала применяем миграции к public (если не skip)
        if not skip_public:
            self.stdout.write('\n📦 Применение миграций к public схеме...')
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SET search_path TO public')

                call_command('migrate', verbosity=1, interactive=False)
                self.stdout.write(self.style.SUCCESS('✅ Public схема обновлена'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Ошибка обновления public: {e}'))
                return

        # Получаем магазины
        if store_slug:
            try:
                stores = [Store.objects.get(slug=store_slug)]
                self.stdout.write(f'\nОбработка магазина: {store_slug}')
            except Store.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Магазин "{store_slug}" не найден'))
                return
        else:
            stores = Store.objects.filter(is_active=True).order_by('created_at')
            self.stdout.write(f'\nНайдено магазинов: {stores.count()}')

        # Применяем миграции к каждой tenant схеме
        success_count = 0
        error_count = 0

        for store in stores:
            self.stdout.write(f'\n📦 {store.name} ({store.schema_name})...')

            try:
                # Переключаемся на tenant схему
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{store.schema_name}", public')

                # Сначала создаем таблицу django_migrations если ее нет
                with connection.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS django_migrations (
                            id SERIAL PRIMARY KEY,
                            app VARCHAR(255) NOT NULL,
                            name VARCHAR(255) NOT NULL,
                            applied TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                        )
                    """)
                    self.stdout.write('  ✓ Таблица django_migrations создана')

                # Применяем миграции с --run-syncdb для создания всех таблиц
                self.stdout.write('  Создание таблиц...')
                call_command('migrate', verbosity=1, interactive=False, run_syncdb=True)

                success_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Миграции применены к {store.name}'
                ))

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f'❌ Ошибка для {store.name}: {e}'
                ))
                import traceback
                self.stdout.write(self.style.ERROR(traceback.format_exc()))

            finally:
                # Возвращаем схему обратно в public
                with connection.cursor() as cursor:
                    cursor.execute('SET search_path TO public')

        # Итоги
        self.stdout.write('\n' + '='*60)
        self.stdout.write(f'Всего магазинов: {stores.count()}')
        self.stdout.write(self.style.SUCCESS(f'Успешно: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Ошибок: {error_count}'))
        self.stdout.write('='*60)

        if error_count == 0:
            self.stdout.write(self.style.SUCCESS('\n✅ Все миграции применены успешно!'))
        else:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Завершено с {error_count} ошибками'))
