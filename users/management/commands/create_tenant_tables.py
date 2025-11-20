"""
Management command для создания таблиц в tenant схемах.

Этот command создает все таблицы напрямую из моделей Django,
используя SchemaEditor, минуя систему миграций.

Usage:
    python manage.py create_tenant_tables
    python manage.py create_tenant_tables --store test_shop
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps
from django.conf import settings
from users.models import Store


class Command(BaseCommand):
    help = 'Создает таблицы в tenant схемах напрямую из моделей'

    def add_arguments(self, parser):
        parser.add_argument(
            '--store',
            type=str,
            help='Slug конкретного магазина (опционально)',
        )
        parser.add_argument(
            '--drop-existing',
            action='store_true',
            help='Удалить существующие таблицы перед созданием',
        )

    def handle(self, *args, **options):
        store_slug = options.get('store')
        drop_existing = options.get('drop_existing', False)

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
            self.stdout.write(f'\nНайдено магазинов: {len(stores)}')

        # Получаем tenant apps
        tenant_app_labels = [app.split('.')[0] for app in settings.TENANT_APPS]
        self.stdout.write(f'Tenant apps: {", ".join(tenant_app_labels)}\n')

        # Собираем все модели из tenant apps
        tenant_models = []
        for app_label in tenant_app_labels:
            try:
                app_config = apps.get_app_config(app_label)
                models = list(app_config.get_models())
                tenant_models.extend(models)
                self.stdout.write(f'  {app_label}: {len(models)} models')
            except LookupError:
                self.stdout.write(self.style.WARNING(f'  ⚠️  App {app_label} not found'))

        self.stdout.write(f'\nВсего моделей для создания: {len(tenant_models)}\n')

        # Обрабатываем каждый магазин
        success_count = 0
        error_count = 0

        for store in stores:
            self.stdout.write(f'\n📦 {store.name} ({store.schema_name})...')

            try:
                # Переключаемся на tenant схему
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{store.schema_name}", public')

                    # Проверяем что схема существует
                    cursor.execute(f"""
                        SELECT schema_name FROM information_schema.schemata
                        WHERE schema_name = '{store.schema_name}'
                    """)
                    if not cursor.fetchone():
                        self.stdout.write(self.style.ERROR(f'  ❌ Схема {store.schema_name} не существует!'))
                        error_count += 1
                        continue

                # Удаляем существующие таблицы если указано
                if drop_existing:
                    self.stdout.write('  Удаление существующих таблиц...')
                    with connection.schema_editor() as schema_editor:
                        for model in reversed(tenant_models):  # Reverse для FK dependencies
                            try:
                                schema_editor.delete_model(model)
                            except Exception:
                                pass  # Игнорируем если таблицы нет

                # Создаем таблицы
                self.stdout.write('  Создание таблиц...')
                created_count = 0

                with connection.schema_editor() as schema_editor:
                    for model in tenant_models:
                        try:
                            # Проверяем существует ли таблица
                            table_name = model._meta.db_table
                            with connection.cursor() as cursor:
                                cursor.execute(f"""
                                    SELECT EXISTS (
                                        SELECT FROM information_schema.tables
                                        WHERE table_schema = '{store.schema_name}'
                                        AND table_name = '{table_name}'
                                    )
                                """)
                                exists = cursor.fetchone()[0]

                            if not exists:
                                schema_editor.create_model(model)
                                created_count += 1
                                self.stdout.write(f'    ✓ {model._meta.label}')
                            else:
                                self.stdout.write(f'    ⊙ {model._meta.label} (exists)')

                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f'    ⚠️  {model._meta.label}: {e}')
                            )

                # Создаем таблицу django_migrations и заполняем ее
                self.stdout.write('  Создание django_migrations...')
                with connection.cursor() as cursor:
                    # Создаем таблицу
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS django_migrations (
                            id SERIAL PRIMARY KEY,
                            app VARCHAR(255) NOT NULL,
                            name VARCHAR(255) NOT NULL,
                            applied TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                        )
                    """)

                    # Копируем записи о миграциях tenant apps из public
                    for app_label in tenant_app_labels:
                        cursor.execute(f"""
                            INSERT INTO django_migrations (app, name, applied)
                            SELECT app, name, applied
                            FROM public.django_migrations
                            WHERE app = '{app_label}'
                            ON CONFLICT DO NOTHING
                        """)

                success_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Создано таблиц: {created_count} в {store.name}'
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
        self.stdout.write(f'Всего магазинов: {len(stores)}')
        self.stdout.write(self.style.SUCCESS(f'Успешно: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Ошибок: {error_count}'))
        self.stdout.write('='*60)

        if error_count == 0:
            self.stdout.write(self.style.SUCCESS('\n✅ Все таблицы созданы успешно!'))
        else:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Завершено с {error_count} ошибками'))
