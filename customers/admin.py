"""
Django admin для customers app.
"""

from django.contrib import admin
from customers.models import CustomerGroup, Customer, CustomerTransaction


@admin.register(CustomerGroup)
class CustomerGroupAdmin(admin.ModelAdmin):
    """Admin для групп покупателей"""

    list_display = ['name', 'discount_percent', 'members_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-discount_percent', 'name']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin для покупателей"""

    list_display = [
        'get_full_name', 'phone', 'customer_type', 'group',
        'balance', 'total_purchases', 'is_active', 'created_at'
    ]
    list_filter = ['customer_type', 'group', 'is_active', 'is_blocked', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone', 'email', 'company_name']
    ordering = ['-created_at']
    readonly_fields = [
        'balance', 'loyalty_points', 'total_purchases',
        'total_purchases_count', 'last_purchase_at',
        'created_at', 'updated_at'
    ]

    fieldsets = (
        ('Основная информация', {
            'fields': ('first_name', 'last_name', 'middle_name', 'customer_type')
        }),
        ('Юридическое лицо', {
            'fields': ('company_name', 'tax_id'),
            'classes': ('collapse',)
        }),
        ('Контакты', {
            'fields': ('phone', 'phone_2', 'email', 'address', 'city', 'region', 'postal_code')
        }),
        ('Группа и финансы', {
            'fields': ('group', 'balance', 'credit_limit', 'loyalty_points')
        }),
        ('Статистика', {
            'fields': ('total_purchases', 'total_purchases_count', 'last_purchase_at'),
            'classes': ('collapse',)
        }),
        ('Дополнительно', {
            'fields': ('birthday', 'notes', 'is_active', 'is_blocked')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomerTransaction)
class CustomerTransactionAdmin(admin.ModelAdmin):
    """Admin для транзакций покупателей"""

    list_display = [
        'customer', 'transaction_type', 'amount',
        'balance_before', 'balance_after', 'created_at'
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['customer__first_name', 'customer__last_name', 'customer__phone', 'description']
    ordering = ['-created_at']
    readonly_fields = ['balance_before', 'balance_after', 'created_at']
