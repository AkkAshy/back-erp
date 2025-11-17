# coding: utf-8
"""
Celery tasks для аналитики.

Периодические задачи для генерации отчётов.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from analytics.signals import (
    _update_daily_sales_report,
    _update_product_performance,
    _update_customer_analytics,
    _update_inventory_snapshot
)


@shared_task
def generate_daily_sales_report():
    """
    Генерирует дневной отчёт по продажам за вчера.
    
    Запускается каждый день в 00:30.
    """
    yesterday = (timezone.now() - timedelta(days=1)).date()
    _update_daily_sales_report(yesterday)
    return f"Отчёт за {yesterday} сгенерирован"


@shared_task
def generate_product_performance_reports():
    """
    Генерирует отчёты по производительности товаров за вчера.
    
    Запускается каждый день в 01:00.
    """
    from products.models import Product
    
    yesterday = (timezone.now() - timedelta(days=1)).date()
    products = Product.objects.filter(is_active=True)
    
    count = 0
    for product in products:
        _update_product_performance(product, yesterday)
        count += 1
    
    return f"Обновлено {count} товаров за {yesterday}"


@shared_task
def generate_customer_analytics():
    """
    Обновляет RFM аналитику для всех активных клиентов.
    
    Запускается раз в неделю (воскресенье в 02:00).
    """
    from customers.models import Customer
    
    customers = Customer.objects.filter(is_active=True)
    
    count = 0
    for customer in customers:
        _update_customer_analytics(customer)
        count += 1
    
    return f"Обновлена аналитика для {count} клиентов"


@shared_task
def generate_inventory_snapshots():
    """
    Создаёт снимки остатков для всех товаров.
    
    Запускается каждый день в 23:50.
    """
    from products.models import Product
    
    today = timezone.now().date()
    products = Product.objects.filter(is_active=True)
    
    count = 0
    for product in products:
        _update_inventory_snapshot(product, today)
        count += 1
    
    return f"Создано {count} снимков остатков за {today}"


@shared_task
def cleanup_old_analytics():
    """
    Очистка старых данных аналитики (старше 1 года).
    
    Запускается раз в месяц (1-го числа в 03:00).
    """
    from analytics.models import (
        DailySalesReport,
        ProductPerformance,
        CustomerAnalytics,
        InventorySnapshot
    )
    
    one_year_ago = timezone.now().date() - timedelta(days=365)
    
    # Удаляем старые данные
    sales_deleted = DailySalesReport.objects.filter(date__lt=one_year_ago).delete()[0]
    products_deleted = ProductPerformance.objects.filter(date__lt=one_year_ago).delete()[0]
    customers_deleted = CustomerAnalytics.objects.filter(period_end__lt=one_year_ago).delete()[0]
    inventory_deleted = InventorySnapshot.objects.filter(date__lt=one_year_ago).delete()[0]
    
    return (
        f"Удалено старых записей: "
        f"продажи={sales_deleted}, "
        f"товары={products_deleted}, "
        f"клиенты={customers_deleted}, "
        f"остатки={inventory_deleted}"
    )


@shared_task
def recalculate_analytics_for_date(date_str):
    """
    Пересчитывает всю аналитику для указанной даты.
    
    Args:
        date_str: дата в формате YYYY-MM-DD
    
    Используется для ручного пересчёта или исправления данных.
    """
    from datetime import datetime
    from products.models import Product
    from customers.models import Customer
    
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Пересчитываем дневной отчёт
    _update_daily_sales_report(date)
    
    # Пересчитываем товары
    products = Product.objects.filter(is_active=True)
    for product in products:
        _update_product_performance(product, date)
    
    # Пересчитываем снимки остатков
    for product in products:
        _update_inventory_snapshot(product, date)
    
    # Обновляем клиентов
    customers = Customer.objects.filter(is_active=True)
    for customer in customers:
        _update_customer_analytics(customer)
    
    return f"Аналитика пересчитана для {date}"
