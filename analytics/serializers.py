# coding: utf-8
"""
Сериализаторы для аналитики и отчётов.
"""

from rest_framework import serializers
from analytics.models import (
    DailySalesReport, 
    ProductPerformance, 
    CustomerAnalytics, 
    InventorySnapshot
)


class DailySalesReportSerializer(serializers.ModelSerializer):
    """Сериализатор для дневных отчётов по продажам"""
    
    class Meta:
        model = DailySalesReport
        fields = [
            'id', 'date',
            'total_sales', 'total_sales_count', 'avg_sale_amount',
            'cash_sales', 'card_sales', 'credit_sales',
            'total_discount', 'total_tax',
            'total_items_sold', 'unique_products_sold',
            'unique_customers', 'new_customers',
            'sessions_opened', 'sessions_closed',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class ProductPerformanceSerializer(serializers.ModelSerializer):
    """Сериализатор для производительности товаров"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_barcode = serializers.CharField(source='product.barcode', read_only=True)
    
    class Meta:
        model = ProductPerformance
        fields = [
            'id', 'product', 'product_name', 'product_code', 'product_barcode',
            'date',
            'quantity_sold', 'total_revenue', 'sales_count',
            'avg_price', 'avg_discount',
            'total_cost', 'total_profit', 'profit_margin',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class CustomerAnalyticsSerializer(serializers.ModelSerializer):
    """Сериализатор для аналитики покупателей"""
    
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    customer_type = serializers.CharField(source='customer.customer_type', read_only=True)
    
    class Meta:
        model = CustomerAnalytics
        fields = [
            'id', 'customer', 'customer_name', 'customer_phone', 'customer_type',
            'period_start', 'period_end',
            'recency_days', 'frequency', 'monetary',
            'rfm_score', 'segment',
            'purchases_count', 'total_spent', 'avg_purchase_amount',
            'credit_purchases', 'total_credit_amount', 'avg_payment_delay_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class InventorySnapshotSerializer(serializers.ModelSerializer):
    """Сериализатор для снимков остатков"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True)
    
    class Meta:
        model = InventorySnapshot
        fields = [
            'id', 'product', 'product_name', 'product_code',
            'date',
            'quantity_on_hand', 'reserved_quantity', 'available_quantity',
            'total_cost', 'total_value',
            'turnover_rate', 'days_of_stock',
            'is_out_of_stock', 'is_low_stock', 'is_overstock',
            'created_at'
        ]
        read_only_fields = fields


class SalesTrendSerializer(serializers.Serializer):
    """Сериализатор для графиков продаж (тренды)"""
    
    date = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_count = serializers.IntegerField()
    avg_sale = serializers.DecimalField(max_digits=12, decimal_places=2)


class TopProductSerializer(serializers.Serializer):
    """Сериализатор для топ товаров"""
    
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_code = serializers.CharField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    total_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    sales_count = serializers.IntegerField()


class CustomerSegmentSerializer(serializers.Serializer):
    """Сериализатор для сегментации клиентов"""
    
    segment = serializers.CharField()
    count = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_purchase = serializers.DecimalField(max_digits=12, decimal_places=2)
