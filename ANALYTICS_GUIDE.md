# 📊 Руководство по Analytics App

## 🎯 Обзор

Приложение **Analytics** предоставляет мощную систему аналитики и отчётности для ERP v2 на основе **Django Signals** и **Celery**.

### Ключевые возможности:
- ✅ **Автоматический сбор данных** через Django Signals
- ✅ **Дневные отчёты по продажам** (выручка, платежи, клиенты)
- ✅ **Анализ производительности товаров** (топ продажи, маржинальность)
- ✅ **RFM-анализ клиентов** (сегментация, лояльность)
- ✅ **Снимки остатков** (оборачиваемость, стоп-листы)
- ✅ **Периодические отчёты** через Celery
- ✅ **REST API** для всех отчётов

---

## 🏗️ Архитектура

### Автоматический сбор данных (Signals)

Аналитика обновляется **автоматически** при изменениях в базе:

```python
# При завершении продажи
Sale.save() → signal → обновляет DailySalesReport, ProductPerformance

# При движении товара
StockMovement.save() → signal → обновляет InventorySnapshot

# При изменении клиента
Customer.add_purchase() → signal → обновляет CustomerAnalytics
```

### Модели данных

**4 основные модели аналитики:**

1. **DailySalesReport** - дневной отчёт по продажам
2. **ProductPerformance** - производительность товаров
3. **CustomerAnalytics** - RFM аналитика клиентов
4. **InventorySnapshot** - снимки остатков

---

## 📋 Модели

### 1. DailySalesReport

Агрегированные данные по продажам за день.

**Поля:**
- `date` - дата отчёта
- `total_sales` - общая выручка
- `total_sales_count` - количество продаж
- `avg_sale_amount` - средний чек
- `cash_sales`, `card_sales`, `credit_sales` - по типам оплаты
- `total_discount`, `total_tax` - скидки и налоги
- `total_items_sold` - товаров продано
- `unique_products_sold` - уникальных товаров
- `unique_customers`, `new_customers` - клиенты
- `sessions_opened`, `sessions_closed` - смены

**Обновление:** автоматически при завершении продажи

---

### 2. ProductPerformance

Производительность товара за день.

**Поля:**
- `product` - FK к товару
- `date` - дата
- `quantity_sold` - продано единиц
- `total_revenue` - выручка
- `sales_count` - количество продаж
- `avg_price`, `avg_discount` - средние значения
- `total_cost`, `total_profit` - себестоимость и прибыль
- `profit_margin` - маржинальность (%)

**Обновление:** автоматически при продаже товара

---

### 3. CustomerAnalytics

RFM-анализ клиента за период (90 дней).

**RFM метрики:**
- `recency_days` - дней с последней покупки
- `frequency` - количество покупок
- `monetary` - общая сумма покупок

**Сегментация:**
- `rfm_score` - общий балл (1-5)
- `segment` - сегмент клиента:
  - **Champions** - лучшие клиенты
  - **Loyal Customers** - постоянные
  - **At Risk** - под угрозой ухода
  - **Lost** - потерянные
  - и другие (11 сегментов)

**Обновление:** автоматически при покупке клиента

---

### 4. InventorySnapshot

Снимок остатков товара на дату.

**Поля:**
- `product` - FK к товару
- `date` - дата снимка
- `quantity_on_hand` - остаток
- `available_quantity` - доступно
- `turnover_rate` - оборачиваемость (раз в 30 дней)
- `days_of_stock` - дней до исчерпания
- `is_low_stock`, `is_out_of_stock`, `is_overstock` - флаги

**Обновление:** автоматически при движении товара + ежедневный Celery task

---

## 🔌 API Endpoints

### Daily Sales Reports

```bash
# Все отчёты
GET /api/analytics/daily-sales/

# Отчёт за сегодня
GET /api/analytics/daily-sales/today/

# Отчёты за период
GET /api/analytics/daily-sales/period/?start_date=2025-11-01&end_date=2025-11-16

# График продаж (тренд)
GET /api/analytics/daily-sales/trends/?days=30
```

**Пример ответа:**
```json
{
  "period": {
    "start_date": "2025-11-01",
    "end_date": "2025-11-16",
    "days": 16
  },
  "totals": {
    "total_sales": "1250000.00",
    "total_count": 125,
    "total_discount": "50000.00",
    "total_tax": "187500.00",
    "avg_sale": "10000.00"
  },
  "daily_reports": [...]
}
```

---

### Product Performance

```bash
# Все отчёты
GET /api/analytics/product-performance/

# Топ товары
GET /api/analytics/product-performance/top_products/?start_date=2025-11-01&end_date=2025-11-16&limit=10&order_by=revenue

# Медленно продающиеся
GET /api/analytics/product-performance/slow_movers/?days=30
```

**Сортировка топ товаров:**
- `order_by=revenue` - по выручке (по умолчанию)
- `order_by=quantity` - по количеству
- `order_by=profit` - по прибыли

**Пример ответа:**
```json
{
  "period": {
    "start_date": "2025-11-01",
    "end_date": "2025-11-16"
  },
  "top_products": [
    {
      "product_id": 15,
      "product_name": "Молоко 3.2%",
      "product_code": "MILK001",
      "total_revenue": "250000.00",
      "total_quantity": "500.000",
      "total_profit": "50000.00",
      "sales_count": 125
    }
  ]
}
```

---

### Customer Analytics (RFM)

```bash
# Все клиенты
GET /api/analytics/customer-analytics/

# Статистика по сегментам
GET /api/analytics/customer-analytics/segments/

# Клиенты в группе риска
GET /api/analytics/customer-analytics/at_risk/

# Фильтрация
GET /api/analytics/customer-analytics/?segment=Champions
GET /api/analytics/customer-analytics/?rfm_score=5
```

**Пример ответа (сегменты):**
```json
{
  "period": {
    "period_start": "2025-08-18",
    "period_end": "2025-11-16"
  },
  "segments": [
    {
      "segment": "Champions",
      "count": 15,
      "total_spent": "5000000.00",
      "avg_purchase": "50000.00"
    },
    {
      "segment": "At Risk",
      "count": 8,
      "total_spent": "800000.00",
      "avg_purchase": "40000.00"
    }
  ]
}
```

---

### Inventory Snapshots

```bash
# Все снимки
GET /api/analytics/inventory-snapshots/

# Последние снимки
GET /api/analytics/inventory-snapshots/latest/

# Товары с низким остатком
GET /api/analytics/inventory-snapshots/low_stock_alerts/

# Товары с нулевым остатком
GET /api/analytics/inventory-snapshots/out_of_stock/

# Фильтрация
GET /api/analytics/inventory-snapshots/?is_low_stock=true
GET /api/analytics/inventory-snapshots/?date=2025-11-16
```

**Пример ответа:**
```json
{
  "date": "2025-11-16",
  "count": 5,
  "products": [
    {
      "product_name": "Хлеб белый",
      "quantity_on_hand": "5.000",
      "days_of_stock": 2,
      "is_low_stock": true
    }
  ]
}
```

---

## ⚙️ Celery Tasks

### Периодические задачи

**1. Дневной отчёт по продажам**
```python
@shared_task
def generate_daily_sales_report():
    """Каждый день в 00:30"""
```

**2. Производительность товаров**
```python
@shared_task
def generate_product_performance_reports():
    """Каждый день в 01:00"""
```

**3. RFM аналитика клиентов**
```python
@shared_task
def generate_customer_analytics():
    """Каждое воскресенье в 02:00"""
```

**4. Снимки остатков**
```python
@shared_task
def generate_inventory_snapshots():
    """Каждый день в 23:50"""
```

**5. Очистка старых данных**
```python
@shared_task
def cleanup_old_analytics():
    """1-го числа каждого месяца в 03:00"""
    # Удаляет данные старше 1 года
```

### Настройка в Celery Beat

```python
# config/celery.py
app.conf.beat_schedule = {
    'daily-sales-report': {
        'task': 'analytics.tasks.generate_daily_sales_report',
        'schedule': crontab(hour=0, minute=30),
    },
    'product-performance': {
        'task': 'analytics.tasks.generate_product_performance_reports',
        'schedule': crontab(hour=1, minute=0),
    },
    'customer-analytics': {
        'task': 'analytics.tasks.generate_customer_analytics',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Воскресенье
    },
    'inventory-snapshots': {
        'task': 'analytics.tasks.generate_inventory_snapshots',
        'schedule': crontab(hour=23, minute=50),
    },
    'cleanup-old-analytics': {
        'task': 'analytics.tasks.cleanup_old_analytics',
        'schedule': crontab(hour=3, minute=0, day_of_month=1),
    },
}
```

### Ручной пересчёт

```python
# Пересчитать всю аналитику для конкретной даты
from analytics.tasks import recalculate_analytics_for_date
recalculate_analytics_for_date.delay('2025-11-16')
```

---

## 🚀 Быстрый старт

### 1. Применить миграции

```bash
source venv/bin/activate
python manage.py makemigrations analytics
python manage.py migrate analytics
```

### 2. Запустить Celery

```bash
# Worker
celery -A config worker -l info

# Beat (для периодических задач)
celery -A config beat -l info
```

### 3. Протестировать API

```bash
# Получить отчёт за сегодня
curl -H "Authorization: Bearer <token>" \
     -H "X-Tenant-Key: <key>" \
     http://localhost:8000/api/analytics/daily-sales/today/

# Топ 10 товаров
curl -H "Authorization: Bearer <token>" \
     -H "X-Tenant-Key: <key>" \
     "http://localhost:8000/api/analytics/product-performance/top_products/?limit=10"
```

---

## 📈 Примеры использования

### 1. Дашборд для владельца магазина

```bash
# Продажи за последние 30 дней
GET /api/analytics/daily-sales/trends/?days=30

# Топ 10 товаров по выручке
GET /api/analytics/product-performance/top_products/?days=30&limit=10

# Клиенты в группе риска
GET /api/analytics/customer-analytics/at_risk/

# Товары с низким остатком
GET /api/analytics/inventory-snapshots/low_stock_alerts/
```

### 2. Анализ прибыльности

```bash
# Топ товары по марже
GET /api/analytics/product-performance/top_products/?order_by=profit&limit=20

# Медленно продающиеся (для скидок)
GET /api/analytics/product-performance/slow_movers/?days=60
```

### 3. CRM и маркетинг

```bash
# Сегментация клиентов
GET /api/analytics/customer-analytics/segments/

# VIP клиенты (Champions + Loyal)
GET /api/analytics/customer-analytics/?segment=Champions

# Потенциальные лояльные
GET /api/analytics/customer-analytics/?segment=Potential Loyalists
```

---

## 🔧 Настройка

### Периоды хранения данных

По умолчанию данные хранятся **1 год**. Чтобы изменить:

```python
# analytics/tasks.py
def cleanup_old_analytics():
    # Изменить на 2 года
    two_years_ago = timezone.now().date() - timedelta(days=730)
```

### Период RFM анализа

По умолчанию **90 дней**. Чтобы изменить:

```python
# analytics/signals.py
def _update_customer_analytics(customer):
    # Изменить на 180 дней
    period_start = today - timedelta(days=180)
```

---

## 📊 RFM Сегментация

### 11 сегментов клиентов

| Сегмент | R | F | M | Описание |
|---------|---|---|---|----------|
| **Champions** | 4-5 | 4-5 | 4-5 | Лучшие клиенты |
| **Loyal Customers** | 2-5 | 4-5 | 4-5 | Постоянные |
| **Potential Loyalists** | 4-5 | 3-4 | 3-4 | Потенциально лояльные |
| **New Customers** | 4-5 | 1-2 | 1-2 | Новички |
| **Promising** | 3-4 | 1-2 | 1-3 | Перспективные |
| **Need Attention** | 3-4 | 3-4 | 3-4 | Нужно внимание |
| **At Risk** | 1-2 | 4-5 | 4-5 | Под угрозой ухода |
| **Can't Lose Them** | 1-2 | 5 | 5 | Нельзя потерять |
| **Hibernating** | 1-2 | 2-3 | 2-3 | Неактивные |
| **Lost** | 1 | 1 | 1 | Потерянные |

**Scores (1-5):**
- **R (Recency)**: 5 = ≤7 дней, 4 = ≤30, 3 = ≤60, 2 = ≤90, 1 = >90
- **F (Frequency)**: 5 = ≥20, 4 = ≥10, 3 = ≥5, 2 = ≥2, 1 = <2
- **M (Monetary)**: 5 = ≥5M, 4 = ≥2M, 3 = ≥1M, 2 = ≥500K, 1 = <500K

---

## 🎯 Рекомендации

### 1. Производительность

- Celery tasks запускаются **в нерабочее время** (ночью)
- Signals обновляют только **изменённые данные**
- Используйте **фильтры** для больших выборок
- Данные **кэшируются** на уровне БД (индексы)

### 2. Мониторинг

Следите за задачами Celery:
```bash
# Статус задач
celery -A config inspect active

# История выполнения
celery -A config events
```

### 3. Резервное копирование

Важные таблицы для бэкапа:
- `analytics_daily_sales`
- `analytics_product_performance`
- `analytics_customer`

---

## ✅ Всё готово!

Analytics app полностью интегрирован в проект и работает **автоматически**!

**Что происходит автоматически:**
1. ✅ При продаже → обновляются отчёты
2. ✅ При движении товара → обновляются остатки
3. ✅ Каждую ночь → генерируются дневные отчёты
4. ✅ Каждое воскресенье → обновляется RFM
5. ✅ Раз в месяц → очистка старых данных

**Проверьте работу:**
```bash
# Swagger
http://localhost:8000/swagger/

# Админка
http://localhost:8000/admin/analytics/
```

🎉 **Готово к использованию!**
