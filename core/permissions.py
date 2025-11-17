"""
Custom permissions для RBAC системы.
"""

from rest_framework import permissions
from core.exceptions import TenantRequiredException, InactiveTenantException
import logging

logger = logging.getLogger(__name__)


class IsTenantUser(permissions.BasePermission):
    """
    Проверяет, что пользователь имеет доступ к tenant (магазину).
    Используется как базовый permission для всех tenant-specific endpoints.

    ВАЖНО: В новой архитектуре используется request.tenant (установлен middleware).
    """

    message = 'Вы не имеете доступа к данному магазину.'

    def has_permission(self, request, view):
        # Проверяем аутентификацию
        if not request.user or not request.user.is_authenticated:
            return False

        # Проверяем наличие tenant (установлен TenantByKeyMiddleware)
        if not hasattr(request, 'tenant') or not request.tenant:
            raise TenantRequiredException()

        # Проверяем активность магазина
        if not request.tenant.is_active:
            raise InactiveTenantException()

        # Проверяем, что есть employee запись
        if not hasattr(request, 'employee') or not request.employee:
            return False

        return True


class HasStorePermission(permissions.BasePermission):
    """
    Проверяет наличие конкретного разрешения у пользователя.
    Использует систему permissions из Employee.permissions.

    Использование:
        permission_classes = [HasStorePermission]
        required_permissions = ['manage_products']  # в view
    """

    def has_permission(self, request, view):
        # Сначала проверяем базовые требования
        tenant_permission = IsTenantUser()
        if not tenant_permission.has_permission(request, view):
            return False

        # Получаем требуемые permissions из view
        required_permissions = getattr(view, 'required_permissions', [])

        if not required_permissions:
            # Если permissions не указаны, разрешаем доступ
            return True

        # Проверяем каждое требуемое разрешение
        user_permissions = getattr(request, 'user_permissions', [])

        for perm in required_permissions:
            if perm not in user_permissions:
                logger.warning(
                    f"Permission denied: {request.user.username} lacks '{perm}'"
                )
                return False

        return True


class IsOwnerOrManager(permissions.BasePermission):
    """
    Разрешает доступ только владельцам и менеджерам магазина.
    """

    message = 'Только владельцы и менеджеры могут выполнять это действие.'

    def has_permission(self, request, view):
        from users.models import Employee

        # Проверяем базовые требования
        tenant_permission = IsTenantUser()
        if not tenant_permission.has_permission(request, view):
            return False

        # Проверяем роль
        user_role = getattr(request, 'user_role', None)

        return user_role in [Employee.Role.OWNER, Employee.Role.MANAGER]


class IsOwner(permissions.BasePermission):
    """
    Разрешает доступ только владельцу магазина.
    """

    message = 'Только владелец магазина может выполнять это действие.'

    def has_permission(self, request, view):
        from users.models import Employee

        # Проверяем базовые требования
        tenant_permission = IsTenantUser()
        if not tenant_permission.has_permission(request, view):
            return False

        # Проверяем роль
        user_role = getattr(request, 'user_role', None)

        return user_role == Employee.Role.OWNER


class IsStoreOwner(permissions.BasePermission):
    """
    Проверяет, что пользователь является владельцем конкретного магазина.
    Используется для object-level permissions.
    """

    def has_object_permission(self, request, view, obj):
        # Если объект - это магазин
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        # Если объект имеет связь с магазином
        if hasattr(obj, 'store'):
            return obj.store.owner == request.user

        return False


class CanManageEmployees(permissions.BasePermission):
    """
    Разрешает управление сотрудниками только владельцам и менеджерам.
    """

    message = 'Вы не можете управлять сотрудниками.'

    def has_permission(self, request, view):
        user_permissions = getattr(request, 'user_permissions', [])
        return 'manage_employees' in user_permissions


class ReadOnly(permissions.BasePermission):
    """
    Разрешает только безопасные методы (GET, HEAD, OPTIONS).
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
