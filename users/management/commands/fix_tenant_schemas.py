"""
Management command для исправления несоответствий между Store.schema_name и реальными схемами в БД.

Проблемы которые исправляет:
1. Создает отсутствующие схемы для магазинов
2. Переименовывает схемы с дефисами (tenant_store-name) в схемы с подчеркиваниями (tenant_store_name)

Usage:
    python manage.py fix_tenant_schemas
    python manage.py fix_tenant_schemas --dry-run  # Показать что будет сделано без выполнения
"""

from django.core.management.base import BaseCommand
from django.db import connection
from users.models import Store
from core.schema_utils import SchemaManager


class Command(BaseCommand):
    help = 'Исправляет несоответствия между Store.schema_name и реальными схемами в БД'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет сделано без выполнения изменений',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN MODE - изменения не будут применены\n'))

        # Получаем все схемы из БД
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name LIKE 'tenant_%'
                ORDER BY schema_name
            """)
            db_schemas = {row[0] for row in cursor.fetchall()}

        self.stdout.write(f'\n📊 Схем в БД: {len(db_schemas)}')
        for schema in sorted(db_schemas):
            self.stdout.write(f'  - {schema}')

        # Получаем все магазины
        stores = Store.objects.filter(is_active=True).order_by('created_at')
        self.stdout.write(f'\n📦 Магазинов в Django: {stores.count()}\n')

        actions_needed = []
        actions_taken = []

        for store in stores:
            expected_schema = store.schema_name

            # Проверяем существует ли ожидаемая схема
            if expected_schema in db_schemas:
                self.stdout.write(f'✅ {store.name}: {expected_schema} - OK')
                continue

            # Ищем схему с тем же префиксом но с дефисами
            potential_old_schema = f"tenant_{store.slug}"  # Может содержать дефисы

            if potential_old_schema in db_schemas and potential_old_schema != expected_schema:
                # Нужно переименовать схему
                action = {
                    'type': 'rename',
                    'store': store,
                    'old_schema': potential_old_schema,
                    'new_schema': expected_schema
                }
                actions_needed.append(action)
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  {store.name}: Схема "{potential_old_schema}" → "{expected_schema}"'
                    )
                )
            else:
                # Схемы вообще нет, нужно создать
                action = {
                    'type': 'create',
                    'store': store,
                    'schema': expected_schema
                }
                actions_needed.append(action)
                self.stdout.write(
                    self.style.WARNING(
                        f'❌ {store.name}: Схема "{expected_schema}" отсутствует'
                    )
                )

        # Выполняем действия
        if not actions_needed:
            self.stdout.write(self.style.SUCCESS('\n✅ Все схемы в порядке, исправления не требуются'))
            return

        self.stdout.write(f'\n📋 Требуется действий: {len(actions_needed)}\n')

        if dry_run:
            self.stdout.write(self.style.WARNING('Для применения изменений запустите без --dry-run'))
            return

        # Применяем изменения
        for action in actions_needed:
            if action['type'] == 'rename':
                self.stdout.write(f'\n🔄 Переименование схемы для {action["store"].name}...')
                success = self._rename_schema(action['old_schema'], action['new_schema'])

                if success:
                    actions_taken.append(action)
                    self.stdout.write(self.style.SUCCESS(f'  ✅ {action["old_schema"]} → {action["new_schema"]}'))
                else:
                    self.stdout.write(self.style.ERROR(f'  ❌ Ошибка переименования'))

            elif action['type'] == 'create':
                self.stdout.write(f'\n➕ Создание схемы для {action["store"].name}...')
                success = SchemaManager.create_schema(action['schema'])

                if success:
                    actions_taken.append(action)
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Создана схема {action["schema"]}'))
                else:
                    self.stdout.write(self.style.ERROR(f'  ❌ Ошибка создания схемы'))

        # Итоги
        self.stdout.write('\n' + '='*60)
        self.stdout.write(f'Запланировано действий: {len(actions_needed)}')
        self.stdout.write(self.style.SUCCESS(f'Выполнено: {len(actions_taken)}'))

        if len(actions_taken) < len(actions_needed):
            failed = len(actions_needed) - len(actions_taken)
            self.stdout.write(self.style.ERROR(f'Ошибок: {failed}'))

        self.stdout.write('='*60)

        if len(actions_taken) == len(actions_needed):
            self.stdout.write(self.style.SUCCESS('\n✅ Все схемы исправлены успешно!'))
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  Некоторые действия не выполнены'))

    def _rename_schema(self, old_name, new_name):
        """Переименовывает PostgreSQL схему"""
        try:
            with connection.cursor() as cursor:
                # Проверяем что старая схема существует
                cursor.execute(f"""
                    SELECT schema_name FROM information_schema.schemata
                    WHERE schema_name = '{old_name}'
                """)
                if not cursor.fetchone():
                    self.stdout.write(self.style.ERROR(f'    Схема {old_name} не найдена'))
                    return False

                # Проверяем что новая схема не существует
                cursor.execute(f"""
                    SELECT schema_name FROM information_schema.schemata
                    WHERE schema_name = '{new_name}'
                """)
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING(f'    Схема {new_name} уже существует'))
                    return False

                # Переименовываем схему
                cursor.execute(f'ALTER SCHEMA "{old_name}" RENAME TO "{new_name}"')

                return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Ошибка: {e}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            return False
