from django.contrib import admin
from products.models import Unit, Category, Attribute, AttributeValue, CategoryAttribute, Product

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'description', 'is_active']
    search_fields = ['name', 'short_name']
    list_filter = ['is_active']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'is_active']
    search_fields = ['name', 'slug']
    list_filter = ['is_active']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_filterable', 'is_active']
    search_fields = ['name', 'slug']
    list_filter = ['is_filterable', 'is_active']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ['value', 'attribute', 'order', 'is_active']
    search_fields = ['value']
    list_filter = ['attribute', 'is_active']

@admin.register(CategoryAttribute)
class CategoryAttributeAdmin(admin.ModelAdmin):
    """
    Админка для привязки атрибутов к категориям.

    Позволяет:
    - Просматривать все привязки
    - Фильтровать по категории, атрибуту
    - Искать по названиям
    - Управлять порядком отображения
    """
    list_display = ['category', 'attribute', 'is_required', 'is_variant', 'order', 'created_at']
    list_filter = ['category', 'is_required', 'is_variant']
    search_fields = ['category__name', 'attribute__name']
    ordering = ['category', 'order', 'attribute__name']

    # Группировка полей
    fieldsets = (
        ('Основная информация', {
            'fields': ('category', 'attribute')
        }),
        ('Настройки', {
            'fields': ('is_required', 'is_variant', 'order')
        }),
    )

    # Автозаполнение для удобства
    autocomplete_fields = ['category', 'attribute']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'unit', 'is_active']
    search_fields = ['name', 'sku', 'barcode']
    list_filter = ['category', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
