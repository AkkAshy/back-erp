# coding: utf-8
"""
Signals для автоматического обновления аналитики.

Обновляют агрегированные данные при изменениях в продажах, товарах и клиентах.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Avg, Count, F
from django.utils import timezone
from decimal import Decimal


@receiver(post_save, sender='sales.Sale')
def update_analytics_on_sale(sender, instance, created, **kwargs):
    """
    Обновляет аналитику при создании или изменении продажи.
    
    - DailySalesReport: обновляется при завершении продажи
    - ProductPerformance: обновляется для каждого товара в продаже
    - CustomerAnalytics: обновляется если продажа с клиентом
    """
    from analytics.models import DailySalesReport, ProductPerformance
    
    # Обновляем только для завершённых продаж
    if instance.status != 'completed' or not instance.completed_at:
        return
    
    sale_date = instance.completed_at.date()
    
    # Обновляем дневной отчёт
    _update_daily_sales_report(sale_date)
    
    # Обновляем производительность товаров
    for item in instance.items.all():
        _update_product_performance(item.product, sale_date)
    
    # Обновляем аналитику клиента если есть
    if instance.customer:
        _update_customer_analytics(instance.customer)


@receiver(post_delete, sender='sales.Sale')
def recalculate_on_sale_delete(sender, instance, **kwargs):
    """Пересчитывает аналитику при удалении продажи."""
    if instance.status == 'completed' and instance.completed_at:
        sale_date = instance.completed_at.date()
        _update_daily_sales_report(sale_date)

        # Пересчитываем товары
        for item in instance.items.all():
            _update_product_performance(item.product, sale_date)


def _update_daily_sales_report(date):
    """
    Обновляет или создаёт дневной отчёт по продажам.
    
    Агрегирует данные из всех завершённых продаж за день.
    """
    from analytics.models import DailySalesReport
    from sales.models import Sale, Payment, CashSession
    from customers.models import Customer
    
    # Получаем все завершённые продажи за день
    sales = Sale.objects.filter(
        status='completed',
        completed_at__date=date
    )
    
    if not sales.exists():
        # Удаляем отчёт если нет продаж
        DailySalesReport.objects.filter(date=date).delete()
        return
    
    # Агрегируем данные
    sales_stats = sales.aggregate(
        total_sales=Sum('total_amount'),
        total_count=Count('id'),
        total_discount=Sum('discount_amount'),
        total_tax=Sum('tax_amount'),
        total_items=Sum('items__quantity'),
        unique_products=Count('items__product', distinct=True),
    )
    
    # Средний чек
    avg_sale = sales_stats['total_sales'] / sales_stats['total_count'] if sales_stats['total_count'] else Decimal('0.00')
    
    # Платежи по типам
    payments = Payment.objects.filter(
        sale__in=sales,
        status='completed'
    )
    
    payment_stats = {
        'cash': payments.filter(payment_method='cash').aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
        'card': payments.filter(payment_method='card').aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
        'credit': payments.filter(payment_method='credit').aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
    }
    
    # Уникальные клиенты
    unique_customers = sales.filter(customer__isnull=False).values('customer').distinct().count()
    
    # Новые клиенты (первая покупка в этот день)
    new_customers = Customer.objects.filter(
        created_at__date=date,
        sales__in=sales
    ).distinct().count()
    
    # Смены
    sessions = CashSession.objects.filter(opened_at__date=date)
    sessions_opened = sessions.count()
    sessions_closed = sessions.filter(status='closed').count()
    
    # Создаём или обновляем отчёт
    DailySalesReport.objects.update_or_create(
        date=date,
        defaults={
            'total_sales': sales_stats['total_sales'] or Decimal('0.00'),
            'total_sales_count': sales_stats['total_count'] or 0,
            'avg_sale_amount': avg_sale,
            'cash_sales': payment_stats['cash'],
            'card_sales': payment_stats['card'],
            'credit_sales': payment_stats['credit'],
            'total_discount': sales_stats['total_discount'] or Decimal('0.00'),
            'total_tax': sales_stats['total_tax'] or Decimal('0.00'),
            'total_items_sold': int(sales_stats['total_items'] or 0),
            'unique_products_sold': sales_stats['unique_products'] or 0,
            'unique_customers': unique_customers,
            'new_customers': new_customers,
            'sessions_opened': sessions_opened,
            'sessions_closed': sessions_closed,
        }
    )


def _update_product_performance(product, date):
    """
    Обновляет производительность товара за день.
    
    Агрегирует данные из позиций продаж за день.
    """
    from analytics.models import ProductPerformance
    from sales.models import SaleItem
    
    # Получаем все позиции товара за день
    items = SaleItem.objects.filter(
        product=product,
        sale__status='completed',
        sale__completed_at__date=date
    )
    
    if not items.exists():
        # Удаляем запись если нет продаж
        ProductPerformance.objects.filter(product=product, date=date).delete()
        return
    
    # Агрегируем данные
    stats = items.aggregate(
        quantity_sold=Sum('quantity'),
        total_revenue=Sum('total_amount'),
        sales_count=Count('sale', distinct=True),
        avg_price=Avg('price'),
        avg_discount=Avg('discount_percent'),
        total_cost=Sum(F('quantity') * F('cost_price')),
    )
    
    # Считаем прибыль
    total_cost = stats['total_cost'] or Decimal('0.00')
    total_revenue = stats['total_revenue'] or Decimal('0.00')
    total_profit = total_revenue - total_cost
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0.00')
    
    # Создаём или обновляем запись
    ProductPerformance.objects.update_or_create(
        product=product,
        date=date,
        defaults={
            'quantity_sold': stats['quantity_sold'] or Decimal('0.000'),
            'total_revenue': total_revenue,
            'sales_count': stats['sales_count'] or 0,
            'avg_price': stats['avg_price'] or Decimal('0.00'),
            'avg_discount': stats['avg_discount'] or Decimal('0.00'),
            'total_cost': total_cost,
            'total_profit': total_profit,
            'profit_margin': profit_margin,
        }
    )


def _update_customer_analytics(customer):
    """
    Обновляет аналитику клиента.
    
    Пересчитывает RFM метрики и сегментацию.
    """
    from analytics.models import CustomerAnalytics
    from sales.models import Sale
    from django.db.models import Sum, Count, Avg
    from datetime import timedelta
    
    today = timezone.now().date()
    
    # Период - последние 90 дней
    period_start = today - timedelta(days=90)
    period_end = today
    
    # Получаем продажи клиента за период
    sales = Sale.objects.filter(
        customer=customer,
        status='completed',
        completed_at__date__gte=period_start,
        completed_at__date__lte=period_end
    )
    
    if not sales.exists():
        # Удаляем запись если нет активности
        CustomerAnalytics.objects.filter(
            customer=customer,
            period_start=period_start,
            period_end=period_end
        ).delete()
        return
    
    # RFM метрики
    last_purchase = sales.order_by('-completed_at').first()
    recency_days = (today - last_purchase.completed_at.date()).days if last_purchase else 999
    
    stats = sales.aggregate(
        frequency=Count('id'),
        monetary=Sum('total_amount'),
        avg_purchase=Avg('total_amount'),
    )
    
    # Кредитные покупки
    credit_stats = sales.filter(payment_method='credit').aggregate(
        credit_count=Count('id'),
        credit_amount=Sum('total_amount'),
    )
    
    # Средняя задержка платежа (для кредитов)
    avg_payment_delay = 0
    
    # RFM Score (1-5)
    r_score = 5 if recency_days <= 7 else 4 if recency_days <= 30 else 3 if recency_days <= 60 else 2 if recency_days <= 90 else 1
    f_score = 5 if stats['frequency'] >= 20 else 4 if stats['frequency'] >= 10 else 3 if stats['frequency'] >= 5 else 2 if stats['frequency'] >= 2 else 1
    m_score = 5 if stats['monetary'] >= 5000000 else 4 if stats['monetary'] >= 2000000 else 3 if stats['monetary'] >= 1000000 else 2 if stats['monetary'] >= 500000 else 1
    
    rfm_score = (r_score + f_score + m_score) // 3
    
    # Сегментация
    segment = _determine_customer_segment(r_score, f_score, m_score)
    
    # Создаём или обновляем аналитику
    CustomerAnalytics.objects.update_or_create(
        customer=customer,
        period_start=period_start,
        period_end=period_end,
        defaults={
            'recency_days': recency_days,
            'frequency': stats['frequency'] or 0,
            'monetary': stats['monetary'] or Decimal('0.00'),
            'rfm_score': rfm_score,
            'segment': segment,
            'purchases_count': stats['frequency'] or 0,
            'total_spent': stats['monetary'] or Decimal('0.00'),
            'avg_purchase_amount': stats['avg_purchase'] or Decimal('0.00'),
            'credit_purchases': credit_stats['credit_count'] or 0,
            'total_credit_amount': credit_stats['credit_amount'] or Decimal('0.00'),
            'avg_payment_delay_days': avg_payment_delay,
        }
    )


def _update_inventory_snapshot(product, date):
    """
    Обновляет снимок остатков товара.
    
    Считает оборачиваемость и дни до исчерпания запасов.
    """
    from analytics.models import InventorySnapshot
    from products.models import Stock
    from sales.models import SaleItem
    from datetime import timedelta
    
    # Получаем текущие остатки
    stock = Stock.objects.filter(product=product).first()
    
    if not stock:
        return
    
    # Продажи за последние 30 дней
    days_ago_30 = date - timedelta(days=30)
    sales_30d = SaleItem.objects.filter(
        product=product,
        sale__status='completed',
        sale__completed_at__date__gte=days_ago_30,
        sale__completed_at__date__lte=date
    ).aggregate(total_sold=Sum('quantity'))
    
    total_sold_30d = sales_30d['total_sold'] or Decimal('0.000')
    
    # Оборачиваемость (раз в 30 дней)
    turnover_rate = Decimal('0.00')
    if stock.quantity > 0 and total_sold_30d > 0:
        turnover_rate = total_sold_30d / stock.quantity
    
    # Дни до исчерпания запасов
    days_of_stock = 0
    if total_sold_30d > 0:
        daily_sales = total_sold_30d / 30
        if daily_sales > 0:
            days_of_stock = int(stock.quantity / daily_sales)
    
    # Флаги
    is_out_of_stock = stock.quantity <= 0
    is_low_stock = stock.quantity <= (product.min_stock_level or 0)
    is_overstock = stock.quantity >= (product.max_stock_level or 999999) if product.max_stock_level else False
    
    # Создаём или обновляем снимок
    InventorySnapshot.objects.update_or_create(
        product=product,
        date=date,
        defaults={
            'quantity_on_hand': stock.quantity,
            'reserved_quantity': stock.reserved_quantity,
            'available_quantity': stock.available_quantity,
            'total_cost': stock.quantity * (product.cost_price or Decimal('0.00')),
            'total_value': stock.quantity * (product.price or Decimal('0.00')),
            'turnover_rate': turnover_rate,
            'days_of_stock': days_of_stock,
            'is_out_of_stock': is_out_of_stock,
            'is_low_stock': is_low_stock,
            'is_overstock': is_overstock,
        }
    )


def _determine_customer_segment(r_score, f_score, m_score):
    """
    Определяет сегмент клиента на основе RFM scores.
    
    Returns:
        str: Название сегмента
    """
    # Champions: высокие R, F, M
    if r_score >= 4 and f_score >= 4 and m_score >= 4:
        return "Champions"
    
    # Loyal Customers: высокие F и M, средний R
    if f_score >= 4 and m_score >= 4:
        return "Loyal Customers"
    
    # Potential Loyalists: высокий R, средние F и M
    if r_score >= 4 and f_score >= 3 and m_score >= 3:
        return "Potential Loyalists"
    
    # New Customers: высокий R, низкие F и M
    if r_score >= 4 and f_score <= 2 and m_score <= 2:
        return "New Customers"
    
    # Promising: средний R, низкие F и M
    if r_score >= 3 and f_score <= 2:
        return "Promising"
    
    # Need Attention: средние R, F, M
    if r_score >= 3 and f_score >= 3:
        return "Need Attention"
    
    # At Risk: низкий R, высокие F и M
    if r_score <= 2 and f_score >= 4 and m_score >= 4:
        return "At Risk"
    
    # Can't Lose Them: низкий R, очень высокие F и M
    if r_score <= 2 and f_score >= 5 and m_score >= 5:
        return "Can't Lose Them"
    
    # Hibernating: низкий R, средние F и M
    if r_score <= 2 and f_score >= 2:
        return "Hibernating"
    
    # Lost: все низкие
    return "Lost"
