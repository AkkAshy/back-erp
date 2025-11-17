# coding: utf-8
"""
Django Admin для аналитики.
"""

from django.contrib import admin
from analytics.models import (
    DailySalesReport,
    ProductPerformance,
    CustomerAnalytics,
    InventorySnapshot
)


@admin.register(DailySalesReport)
class DailySalesReportAdmin(admin.ModelAdmin):
    """Admin для дневных отчётов"""
    
    list_display = [
        'date', 'total_sales', 'total_sales_count', 'avg_sale_amount',
        'cash_sales', 'card_sales', 'unique_customers'
    ]
    list_filter = ['date']
    search_fields = ['date']
    ordering = ['-date']
    readonly_fields = [
        'date', 'total_sales', 'total_sales_count', 'avg_sale_amount',
        'cash_sales', 'card_sales', 'credit_sales',
        'total_discount', 'total_tax',
        'total_items_sold', 'unique_products_sold',
        'unique_customers', 'new_customers',
        'sessions_opened', 'sessions_closed',
        'created_at', 'updated_at'
    ]


@admin.register(ProductPerformance)
class ProductPerformanceAdmin(admin.ModelAdmin):
    """Admin для производительности товаров"""
    
    list_display = [
        'product', 'date', 'quantity_sold', 'total_revenue',
        'total_profit', 'profit_margin'
    ]
    list_filter = ['date']
    search_fields = ['product__name', 'product__code']
    ordering = ['-date', '-total_revenue']
    readonly_fields = [
        'product', 'date',
        'quantity_sold', 'total_revenue', 'sales_count',
        'avg_price', 'avg_discount',
        'total_cost', 'total_profit', 'profit_margin',
        'created_at', 'updated_at'
    ]


@admin.register(CustomerAnalytics)
class CustomerAnalyticsAdmin(admin.ModelAdmin):
    """Admin для аналитики клиентов"""
    
    list_display = [
        'customer', 'segment', 'rfm_score',
        'recency_days', 'frequency', 'monetary'
    ]
    list_filter = ['segment', 'rfm_score']
    search_fields = ['customer__first_name', 'customer__last_name', 'customer__phone']
    ordering = ['-monetary']
    readonly_fields = [
        'customer', 'period_start', 'period_end',
        'recency_days', 'frequency', 'monetary',
        'rfm_score', 'segment',
        'purchases_count', 'total_spent', 'avg_purchase_amount',
        'credit_purchases', 'total_credit_amount', 'avg_payment_delay_days',
        'created_at', 'updated_at'
    ]


@admin.register(InventorySnapshot)
class InventorySnapshotAdmin(admin.ModelAdmin):
    """Admin для снимков остатков"""
    
    list_display = [
        'product', 'date', 'quantity_on_hand', 'available_quantity',
        'turnover_rate', 'days_of_stock',
        'is_low_stock', 'is_out_of_stock'
    ]
    list_filter = ['date', 'is_low_stock', 'is_out_of_stock', 'is_overstock']
    search_fields = ['product__name', 'product__code']
    ordering = ['-date', 'product']
    readonly_fields = [
        'product', 'date',
        'quantity_on_hand', 'reserved_quantity', 'available_quantity',
        'total_cost', 'total_value',
        'turnover_rate', 'days_of_stock',
        'is_out_of_stock', 'is_low_stock', 'is_overstock',
        'created_at'
    ]
