"""
Database router for multi-tenant schema-based isolation.

This router directs database operations to the correct PostgreSQL schema:
- SHARED_APPS → public schema
- TENANT_APPS → tenant-specific schema (set by TenantByKeyMiddleware)
"""

from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class TenantDatabaseRouter:
    """
    Router for directing database operations to the correct schema.

    The schema is set by TenantByKeyMiddleware via:
        SET search_path TO "tenant_<schema_name>", public

    This router determines which apps use tenant schemas vs public schema.
    """

    def db_for_read(self, model, **hints):
        """
        Direct read operations to the correct database.
        All reads use 'default' database, but different schemas.
        """
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Direct write operations to the correct database.
        All writes use 'default' database, but different schemas.
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations between objects.

        Rules:
        - Shared models can relate to shared models ✅
        - Tenant models can relate to tenant models ✅
        - Tenant models can relate to shared models ✅ (e.g., Sale → User)
        - Shared models should NOT relate to tenant models ❌
        """
        # Get app labels
        app1 = obj1._meta.app_label
        app2 = obj2._meta.app_label

        # Get tenant apps
        tenant_apps = [app.split('.')[0] for app in settings.TENANT_APPS]

        is_tenant1 = app1 in tenant_apps
        is_tenant2 = app2 in tenant_apps

        # If both are in the same category (both shared or both tenant), allow
        if is_tenant1 == is_tenant2:
            return True

        # Allow tenant models to reference shared models (e.g., Sale → User)
        if is_tenant1 and not is_tenant2:
            return True

        # Disallow shared models referencing tenant models
        if not is_tenant1 and is_tenant2:
            logger.warning(
                f"Disallowing relation from shared model {obj1._meta.label} "
                f"to tenant model {obj2._meta.label}"
            )
            return False

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Determine if a migration should be applied.

        This is called during `python manage.py migrate`.

        Rules:
        - When migrating PUBLIC schema: only apply SHARED_APPS migrations (except Employee)
        - When migrating TENANT schema: only apply TENANT_APPS migrations + Employee from users app

        The current schema is determined by checking the database search_path.
        """
        from django.db import connection

        # Get current schema from database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW search_path")
                search_path = cursor.fetchone()[0]

                # Parse schema from search_path
                # Examples:
                #   "public" → public schema
                #   "tenant_test_shop, public" → tenant schema
                #   '"tenant_test_shop", public' → tenant schema
                current_schema = search_path.split(',')[0].strip().strip('"')

        except Exception as e:
            logger.warning(f"Could not determine current schema: {e}")
            # Default to public if we can't determine
            current_schema = 'public'

        # Get tenant apps (extract app labels only)
        tenant_apps = [app.split('.')[0] for app in settings.TENANT_APPS]

        # Special case: Employee model from users app should be in tenant schemas
        is_employee_model = app_label == 'users' and model_name == 'employee'

        is_tenant_app = app_label in tenant_apps or is_employee_model
        is_public_schema = current_schema == 'public'

        # Logic:
        # - If in PUBLIC schema: only migrate SHARED apps (except Employee)
        # - If in TENANT schema: only migrate TENANT apps + Employee

        if is_public_schema:
            # In public schema, skip Employee but allow other users models
            if is_employee_model:
                should_migrate = False
                logger.debug(
                    f"PUBLIC schema: users.Employee → ❌ SKIP (tenant-specific)"
                )
            else:
                should_migrate = not is_tenant_app
                logger.debug(
                    f"PUBLIC schema: {app_label} → "
                    f"{'✅ MIGRATE' if should_migrate else '❌ SKIP'}"
                )
            return should_migrate
        else:
            # In tenant schema, allow tenant apps + Employee
            should_migrate = is_tenant_app
            logger.debug(
                f"TENANT schema ({current_schema}): {app_label}.{model_name or 'all'} → "
                f"{'✅ MIGRATE' if should_migrate else '❌ SKIP'}"
            )
            return should_migrate
