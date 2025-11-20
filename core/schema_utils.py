"""
Утилиты для управления PostgreSQL схемами (schemas) для мультитенантности.
"""

from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SchemaManager:
    """
    Менеджер для работы с PostgreSQL схемами.
    Каждый магазин получает свою схему: store_{slug}
    """

    @staticmethod
    def create_schema(schema_name):
        """
        Создает новую схему в PostgreSQL.

        Args:
            schema_name (str): Имя схемы (например: store_myshop)

        Returns:
            bool: True если успешно создана, False в случае ошибки
        """
        # Проверка на SQLite (в dev режиме)
        if 'sqlite' in settings.DATABASES['default']['ENGINE']:
            logger.info("SQLite detected - skipping schema creation")
            return True

        try:
            with connection.cursor() as cursor:
                # Проверяем, существует ли схема
                cursor.execute(
                    """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name = %s
                    """,
                    [schema_name]
                )

                if cursor.fetchone():
                    logger.info(f"Schema {schema_name} already exists")
                    return True

                # Создаем схему
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')

                logger.info(f"Created schema: {schema_name}")

                # Создаем таблицы в новой схеме
                SchemaManager._create_schema_tables(schema_name)

                return True

        except Exception as e:
            logger.error(f"Error creating schema {schema_name}: {e}", exc_info=True)
            return False

    @staticmethod
    def _create_schema_tables(schema_name):
        """
        Создает таблицы в новой схеме напрямую из моделей.

        Args:
            schema_name (str): Имя схемы
        """
        try:
            from django.apps import apps
            from django.conf import settings

            # Переключаемся на tenant схему
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{schema_name}", public')

            # Получаем tenant apps
            tenant_app_labels = [app.split('.')[0] for app in settings.TENANT_APPS]

            # Собираем все модели из tenant apps
            tenant_models = []
            for app_label in tenant_app_labels:
                try:
                    app_config = apps.get_app_config(app_label)
                    models = list(app_config.get_models())
                    tenant_models.extend(models)
                except LookupError:
                    logger.warning(f"App {app_label} not found")

            # Добавляем Employee model из users app (tenant-specific)
            try:
                from users.models import Employee
                tenant_models.append(Employee)
                logger.debug("Added Employee model to tenant models")
            except ImportError:
                logger.warning("Could not import Employee model")

            logger.info(f"Creating {len(tenant_models)} tables in {schema_name}")

            # Создаем таблицы используя SchemaEditor
            with connection.schema_editor() as schema_editor:
                for model in tenant_models:
                    try:
                        schema_editor.create_model(model)
                        logger.debug(f"Created table for {model._meta.label}")
                    except Exception as e:
                        logger.warning(f"Error creating table for {model._meta.label}: {e}")

            # Создаем таблицу django_migrations
            with connection.cursor() as cursor:
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

            # Возвращаем search_path обратно
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO public')

            logger.info(f"Successfully created tables in schema: {schema_name}")

        except Exception as e:
            logger.error(f"Error creating tables in schema {schema_name}: {e}")
            # Возвращаем search_path в любом случае
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SET search_path TO public')
            except:
                pass
            # НЕ raise - позволяем магазину создаться даже если таблицы не создались
            # Таблицы можно создать потом через create_tenant_tables
            logger.warning(f"Store created but tables not initialized for {schema_name}")

    @staticmethod
    def drop_schema(schema_name, cascade=False):
        """
        Удаляет схему из PostgreSQL.

        Args:
            schema_name (str): Имя схемы
            cascade (bool): Удалять со всеми зависимостями

        Returns:
            bool: True если успешно удалена
        """
        # Проверка на SQLite
        if 'sqlite' in settings.DATABASES['default']['ENGINE']:
            logger.info("SQLite detected - skipping schema deletion")
            return True

        try:
            with connection.cursor() as cursor:
                cascade_sql = "CASCADE" if cascade else "RESTRICT"
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" {cascade_sql}')

                logger.info(f"Dropped schema: {schema_name}")
                return True

        except Exception as e:
            logger.error(f"Error dropping schema {schema_name}: {e}")
            return False

    @staticmethod
    def schema_exists(schema_name):
        """
        Проверяет существование схемы.

        Args:
            schema_name (str): Имя схемы

        Returns:
            bool: True если схема существует
        """
        # Проверка на SQLite
        if 'sqlite' in settings.DATABASES['default']['ENGINE']:
            return True

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name = %s
                    """,
                    [schema_name]
                )

                return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"Error checking schema existence: {e}")
            return False

    @staticmethod
    def set_search_path(schema_name):
        """
        Устанавливает search_path для текущего соединения.

        Args:
            schema_name (str): Имя схемы
        """
        if 'sqlite' in settings.DATABASES['default']['ENGINE']:
            return

        try:
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{schema_name}", public')

        except Exception as e:
            logger.error(f"Error setting search_path: {e}")

    @staticmethod
    def reset_search_path():
        """
        Сбрасывает search_path обратно к public.
        """
        if 'sqlite' in settings.DATABASES['default']['ENGINE']:
            return

        try:
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO public')

        except Exception as e:
            logger.error(f"Error resetting search_path: {e}")

    @staticmethod
    def list_schemas():
        """
        Получает список всех пользовательских схем.

        Returns:
            list: Список имен схем
        """
        if 'sqlite' in settings.DATABASES['default']['ENGINE']:
            return []

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'public')
                    AND schema_name NOT LIKE 'pg_%'
                    ORDER BY schema_name
                    """
                )

                return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error listing schemas: {e}")
            return []

    @staticmethod
    def clone_schema(source_schema, target_schema):
        """
        Клонирует структуру схемы (без данных).

        Args:
            source_schema (str): Исходная схема
            target_schema (str): Целевая схема
        """
        if 'sqlite' in settings.DATABASES['default']['ENGINE']:
            return True

        try:
            # Создаем новую схему
            SchemaManager.create_schema(target_schema)

            # Копируем структуру таблиц
            with connection.cursor() as cursor:
                # Получаем список таблиц в исходной схеме
                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = %s
                    """,
                    [source_schema]
                )

                tables = [row[0] for row in cursor.fetchall()]

                # Копируем структуру каждой таблицы
                for table in tables:
                    cursor.execute(
                        f"""
                        CREATE TABLE "{target_schema}"."{table}"
                        (LIKE "{source_schema}"."{table}" INCLUDING ALL)
                        """
                    )

                logger.info(f"Cloned schema from {source_schema} to {target_schema}")
                return True

        except Exception as e:
            logger.error(f"Error cloning schema: {e}")
            return False


# Context manager для работы со схемами

class schema_context:
    """
    Context manager для временной работы в конкретной схеме.

    Использование:
        with schema_context('store_myshop'):
            Product.objects.all()  # Работает в схеме store_myshop
    """

    def __init__(self, schema_name):
        self.schema_name = schema_name
        self.original_path = None

    def __enter__(self):
        """Устанавливаем схему при входе в контекст"""
        if 'sqlite' not in settings.DATABASES['default']['ENGINE']:
            with connection.cursor() as cursor:
                # Сохраняем текущий search_path
                cursor.execute('SHOW search_path')
                self.original_path = cursor.fetchone()[0]

                # Устанавливаем новый search_path
                cursor.execute(f'SET search_path TO "{self.schema_name}", public')

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Восстанавливаем исходный search_path при выходе"""
        if 'sqlite' not in settings.DATABASES['default']['ENGINE']:
            with connection.cursor() as cursor:
                if self.original_path:
                    cursor.execute(f'SET search_path TO {self.original_path}')
                else:
                    cursor.execute('SET search_path TO public')
