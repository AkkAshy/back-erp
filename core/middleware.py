"""
Tenant Middleware для мультитенантности на основе PostgreSQL схем.
Использует X-Tenant-Key header для идентификации магазина и переключения схем.

Архитектура как в QRMenu:
- public схема: хранит владельцев и список всех магазинов
- tenant_* схемы: отдельные "миры" магазинов (товары, продажи, клиенты)
- X-Tenant-Key: уникальный ключ магазина в заголовке запроса
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.db import connection
from django.conf import settings

logger = logging.getLogger('core.middleware')


class TenantByKeyMiddleware(MiddlewareMixin):
    """
    Middleware для схемной мультитенантности.

    Процесс:
    1. Извлекает X-Tenant-Key из заголовка запроса
    2. Находит магазин по tenant_key в public.users_store
    3. Переключает search_path на схему магазина (tenant_{slug})
    4. Все ORM запросы теперь работают только в этой схеме
    5. После запроса возвращает search_path обратно в public
    """

    HEADER_NAME = 'HTTP_X_TENANT_KEY'  # Django преобразует X-Tenant-Key в HTTP_X_TENANT_KEY

    # Пути, которые не требуют tenant context (работают в public схеме)
    PUBLIC_PATHS = [
        '/api/users/auth/register/',
        '/api/users/auth/login/',
        '/api/users/auth/token/refresh/',
        '/admin/',
        '/swagger/',
        '/redoc/',
        '/static/',
        '/media/',
    ]

    def process_request(self, request):
        """Обрабатывает запрос и переключает схему"""

        # Сбрасываем контекст
        request.tenant = None
        request.tenant_key = None
        request.schema_name = 'public'

        # Проверяем, нужен ли tenant для этого пути
        if self._is_public_path(request.path):
            logger.debug(f"Public path: {request.path} - staying in public schema")
            self._set_schema('public')
            return None

        # Извлекаем tenant_key из заголовка
        tenant_key = request.META.get(self.HEADER_NAME)

        if not tenant_key:
            # Для tenant-specific путей требуется X-Tenant-Key
            logger.warning(f"Missing X-Tenant-Key header for path: {request.path}")
            return JsonResponse({
                'status': 'error',
                'code': 'missing_tenant_key',
                'message': 'Заголовок X-Tenant-Key обязателен для этого запроса'
            }, status=400)

        # Загружаем tenant и переключаем схему
        try:
            tenant = self._get_tenant_by_key(tenant_key)

            if not tenant:
                logger.warning(f"Tenant not found for key: {tenant_key}")
                return JsonResponse({
                    'status': 'error',
                    'code': 'invalid_tenant_key',
                    'message': 'Неверный ключ магазина'
                }, status=403)

            if not tenant.is_active:
                logger.warning(f"Inactive tenant: {tenant_key}")
                return JsonResponse({
                    'status': 'error',
                    'code': 'inactive_tenant',
                    'message': 'Данный магазин неактивен'
                }, status=403)

            # Устанавливаем контекст
            request.tenant = tenant
            request.tenant_key = tenant_key
            request.schema_name = tenant.schema_name

            # Переключаем схему
            self._set_schema(tenant.schema_name)

            logger.debug(f"Switched to schema: {tenant.schema_name} (tenant_key: {tenant_key})")

        except Exception as e:
            logger.error(f"Error processing tenant: {e}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'code': 'tenant_error',
                'message': 'Ошибка при обработке магазина'
            }, status=500)

        return None

    def process_response(self, request, response):
        """Возвращаем search_path обратно в public после запроса"""
        try:
            self._set_schema('public')
            logger.debug("Reset schema to public")
        except Exception as e:
            logger.error(f"Error resetting schema: {e}")

        return response

    def process_exception(self, request, exception):
        """Обрабатываем исключения и сбрасываем схему"""
        try:
            self._set_schema('public')
        except Exception as e:
            logger.error(f"Error resetting schema after exception: {e}")

        return None

    def _is_public_path(self, path):
        """Проверяет, является ли путь публичным"""
        return any(path.startswith(public_path) for public_path in self.PUBLIC_PATHS)

    def _get_tenant_by_key(self, tenant_key):
        """
        Получает tenant из базы по tenant_key.
        ВАЖНО: запрос делается в public схеме!
        """
        from users.models import Store

        # Убеждаемся, что мы в public схеме
        self._set_schema('public')

        try:
            return Store.objects.select_related('owner').get(
                tenant_key=tenant_key,
                is_active=True
            )
        except Store.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error fetching tenant: {e}")
            return None

    def _set_schema(self, schema_name):
        """
        Переключает PostgreSQL search_path на указанную схему.

        Для SQLite (dev режим) - игнорируем.
        """
        # Проверка на SQLite
        if 'sqlite' in settings.DATABASES['default']['ENGINE']:
            return

        try:
            with connection.cursor() as cursor:
                # Переключаем search_path
                # tenant схема + public (для общих таблиц типа auth_user)
                if schema_name == 'public':
                    cursor.execute("SET search_path TO public")
                else:
                    cursor.execute(f"SET search_path TO {schema_name}, public")

        except Exception as e:
            logger.error(f"Error setting search_path to {schema_name}: {e}")
            raise


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware для выполнения JWT аутентификации ДО других middleware.

    DRF выполняет аутентификацию в views, но нам нужно чтобы request.user
    был доступен в LoadEmployeeContextMiddleware.
    """

    def process_request(self, request):
        """Пытается аутентифицировать пользователя по JWT токену"""
        from rest_framework_simplejwt.authentication import JWTAuthentication
        from rest_framework.exceptions import AuthenticationFailed

        # Пропускаем если уже аутентифицирован
        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            return None

        # Пытаемся аутентифицировать по JWT
        jwt_auth = JWTAuthentication()
        try:
            auth_result = jwt_auth.authenticate(request)
            if auth_result is not None:
                user, token = auth_result
                request.user = user
                request.auth = token
                logger.debug(f"JWT auth successful for user: {user.username}")
        except (AuthenticationFailed, Exception) as e:
            # Не удалось аутентифицировать - ничего страшного
            # Django AuthenticationMiddleware установит AnonymousUser
            logger.debug(f"JWT auth failed or not provided: {e}")
            pass

        return None


class LoadEmployeeContextMiddleware(MiddlewareMixin):
    """
    Дополнительный middleware для загрузки информации о сотруднике.
    Работает после TenantByKeyMiddleware и JWT аутентификации.
    """

    def process_request(self, request):
        """Загружает employee контекст для аутентифицированного пользователя"""

        # Инициализируем
        request.employee = None
        request.user_role = None
        request.user_permissions = []

        # Если пользователь не аутентифицирован или нет tenant - пропускаем
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None

        if not hasattr(request, 'tenant') or not request.tenant:
            return None

        # Загружаем employee запись (из public схемы!)
        try:
            from users.models import Employee

            # ВАЖНО: Для PostgreSQL переключаемся в public для запроса Employee
            # так как Employee находится в public схеме, а не в tenant схеме
            # Для SQLite ничего не делаем (все таблицы в одной БД)
            if 'sqlite' not in settings.DATABASES['default']['ENGINE']:
                with connection.cursor() as cursor:
                    cursor.execute("SET search_path TO public")

            employee = Employee.objects.select_related('user', 'store').filter(
                user=request.user,
                store=request.tenant,
                is_active=True
            ).first()

            # Возвращаемся обратно в tenant схему (только для PostgreSQL)
            if 'sqlite' not in settings.DATABASES['default']['ENGINE']:
                if hasattr(request, 'schema_name') and request.schema_name:
                    with connection.cursor() as cursor:
                        if request.schema_name == 'public':
                            cursor.execute("SET search_path TO public")
                        else:
                            cursor.execute(f"SET search_path TO {request.schema_name}, public")

            if employee:
                request.employee = employee
                request.user_role = employee.role
                request.user_permissions = employee.permissions

                logger.debug(
                    f"Loaded employee: {employee.full_name} "
                    f"({employee.role}) for tenant: {request.tenant.name}"
                )
            else:
                logger.warning(
                    f"No employee record found for user {request.user.username} "
                    f"in tenant {request.tenant.name}"
                )

        except Exception as e:
            logger.error(f"Error loading employee context: {e}", exc_info=True)

        return None
