from django.contrib import admin
from products.models import Unit, Category, Attribute, AttributeValue, Product

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

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'unit', 'is_active']
    search_fields = ['name', 'sku', 'barcode']
    list_filter = ['category', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
