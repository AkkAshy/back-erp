# coding: utf-8
"""
Модели для аналитики и отчётности.

Используют агрегированные данные для быстрых отчётов.
Обновляются через Django signals автоматически.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class DailySalesReport(models.Model):
    """
    Ежедневный отчёт по продажам.
    Автоматически создаётся/обновляется через signals.
    """

    date = models.DateField(db_index=True, verbose_name="Дата")
    
    # Продажи
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_sales_count = models.IntegerField(default=0)
    avg_sale_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Платежи по типам
    cash_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    card_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Скидки и налоги
    total_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Товары
    total_items_sold = models.IntegerField(default=0)
    unique_products_sold = models.IntegerField(default=0)
    
    # Клиенты
    unique_customers = models.IntegerField(default=0)
    new_customers = models.IntegerField(default=0)
    
    # Смены
    sessions_opened = models.IntegerField(default=0)
    sessions_closed = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_daily_sales'
        ordering = ['-date']
        unique_together = [['date']]
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['date', 'total_sales']),
        ]

    def __str__(self):
        return f"Отчёт за {self.date}: {self.total_sales} сум"


class ProductPerformance(models.Model):
    """
    Производительность товара за период.
    Топ товары, медленно продающиеся и т.д.
    """

    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='performance')
    date = models.DateField(db_index=True)
    
    # Продажи
    quantity_sold = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sales_count = models.IntegerField(default=0)
    
    # Средние значения
    avg_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Прибыль (если есть себестоимость)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_product_performance'
        ordering = ['-date', '-total_revenue']
        unique_together = [['product', 'date']]
        indexes = [
            models.Index(fields=['product', '-date']),
            models.Index(fields=['-date', '-total_revenue']),
            models.Index(fields=['-date', '-quantity_sold']),
        ]

    def __str__(self):
        return f"{self.product.name} за {self.date}"


class CustomerAnalytics(models.Model):
    """
    Аналитика по покупателю за период.
    RFM анализ, lifetime value и т.д.
    """

    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='analytics')
    period_start = models.DateField()
    period_end = models.DateField()
    
    # RFM метрики
    recency_days = models.IntegerField(default=0, help_text="Дней с последней покупки")
    frequency = models.IntegerField(default=0, help_text="Количество покупок")
    monetary = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Общая сумма покупок")
    
    # Сегментация
    rfm_score = models.IntegerField(default=0, help_text="RFM score (1-5)")
    segment = models.CharField(max_length=50, blank=True, help_text="Champions, Loyal, At Risk и т.д.")
    
    # Детальная статистика
    purchases_count = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_purchase_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Платёжная дисциплина
    credit_purchases = models.IntegerField(default=0)
    total_credit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_payment_delay_days = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_customer'
        ordering = ['-monetary']
        unique_together = [['customer', 'period_start', 'period_end']]
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['-monetary']),
            models.Index(fields=['segment']),
            models.Index(fields=['rfm_score']),
        ]

    def __str__(self):
        return f"{self.customer.get_full_name()} ({self.period_start} - {self.period_end})"


class InventorySnapshot(models.Model):
    """
    Снимок остатков на определённую дату.
    Для анализа оборачиваемости, стоп-листов и т.д.
    """

    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='inventory_snapshots')
    date = models.DateField(db_index=True)
    
    # Остатки
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    reserved_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    available_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    
    # Стоимость
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Оборачиваемость (за последние 30 дней)
    turnover_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Количество оборотов")
    days_of_stock = models.IntegerField(default=0, help_text="Дней до исчерпания запасов")
    
    # Флаги
    is_out_of_stock = models.BooleanField(default=False)
    is_low_stock = models.BooleanField(default=False)
    is_overstock = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_inventory_snapshot'
        ordering = ['-date', 'product']
        unique_together = [['product', 'date']]
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['product', '-date']),
            models.Index(fields=['is_low_stock', '-date']),
            models.Index(fields=['is_out_of_stock', '-date']),
        ]

    def __str__(self):
        return f"{self.product.name} на {self.date}: {self.quantity_on_hand}"
