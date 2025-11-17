"""
Admin interface для управления пользователями, магазинами и сотрудниками.
"""

from django.contrib import admin
from django.utils.html import format_html
from users.models import Store, Employee


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    """Админ интерфейс для Store"""

    list_display = [
        'id', 'name', 'slug', 'owner', 'is_active',
        'employee_count', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'owner__username', 'owner__first_name', 'owner__last_name']
    readonly_fields = ['schema_name', 'created_at', 'updated_at', 'employee_count', 'active_employee_count']
    ordering = ['-created_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description', 'owner', 'is_active')
        }),
        ('Контакты', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Технические поля', {
            'fields': ('schema_name', 'employee_count', 'active_employee_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def employee_count(self, obj):
        """Отображение количества сотрудников"""
        count = obj.employee_count
        if count > 0:
            return format_html('<span style="color: green;">{}</span>', count)
        return count
    employee_count.short_description = 'Сотрудников'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Админ интерфейс для Employee"""

    list_display = [
        'id', 'user', 'store', 'role', 'is_active',
        'phone', 'hired_at'
    ]
    list_filter = ['role', 'is_active', 'hired_at', 'store']
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'store__name', 'phone'
    ]
    readonly_fields = ['hired_at', 'created_at', 'updated_at', 'permissions_list']
    ordering = ['-created_at']
    autocomplete_fields = ['user', 'store']

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'store', 'role', 'is_active')
        }),
        ('Дополнительно', {
            'fields': ('phone', 'photo', 'position')
        }),
        ('Права доступа', {
            'fields': ('permissions_list',),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('hired_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def permissions_list(self, obj):
        """Отображение прав доступа"""
        perms = obj.permissions
        if perms:
            return format_html('<br>'.join([f'✓ {p}' for p in perms]))
        return 'Нет прав'
    permissions_list.short_description = 'Разрешения'

    def save_model(self, request, obj, form, change):
        """Переопределяем сохранение для валидации"""
        obj.full_clean()
        super().save_model(request, obj, form, change)
