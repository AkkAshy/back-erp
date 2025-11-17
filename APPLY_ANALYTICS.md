# 🚀 Применение Analytics App

## ✅ Статус: Всё готово!

Приложение analytics полностью создано и настроено с автоматическим сбором данных через Django Signals.

---

## 📋 Быстрый старт

```bash
# 1. Активируй виртуальное окружение
source venv/bin/activate

# 2. Создай миграции для analytics
python manage.py makemigrations analytics

# 3. Применить миграции
python manage.py migrate

# 4. Запусти сервер
python manage.py runserver

# 5. (Опционально) Запусти Celery для периодических отчётов
# В отдельном терминале:
celery -A config worker -l info

# И Beat для расписания:
celery -A config beat -l info
```

---

## 📁 Созданные файлы:

```
analytics/
├── __init__.py             ✅
├── models.py               ✅ 4 модели (DailySalesReport, ProductPerformance, CustomerAnalytics, InventorySnapshot)
├── signals.py              ✅ Автоматическое обновление через Django Signals
├── serializers.py          ✅ 7 сериализаторов для API
├── views.py                ✅ 4 ViewSet'а с custom actions
├── urls.py                 ✅ REST API routing
├── admin.py                ✅ Django admin
├── apps.py                 ✅ Конфигурация + регистрация signals
├── tasks.py                ✅ 6 Celery tasks
└── migrations/
    └── __init__.py         ✅

config/
├── settings.py             ✅ Добавлено analytics.apps.AnalyticsConfig
└── urls.py                 ✅ Добавлен path('api/analytics/')
```

---

## 🔌 Доступные endpoints:

После миграции будут доступны:

### Daily Sales Reports
```
GET    /api/analytics/daily-sales/              - Все отчёты
GET    /api/analytics/daily-sales/today/        - Отчёт за сегодня
GET    /api/analytics/daily-sales/period/       - За период (start_date, end_date)
GET    /api/analytics/daily-sales/trends/       - График продаж (days=30)
```

### Product Performance
```
GET    /api/analytics/product-performance/          - Все отчёты
GET    /api/analytics/product-performance/top_products/    - Топ товары
GET    /api/analytics/product-performance/slow_movers/     - Медленно продающиеся
```

### Customer Analytics (RFM)
```
GET    /api/analytics/customer-analytics/           - Все клиенты
GET    /api/analytics/customer-analytics/segments/  - Сегментация
GET    /api/analytics/customer-analytics/at_risk/   - В группе риска
```

### Inventory Snapshots
```
GET    /api/analytics/inventory-snapshots/              - Все снимки
GET    /api/analytics/inventory-snapshots/latest/      - Последние
GET    /api/analytics/inventory-snapshots/low_stock_alerts/  - Низкий остаток
GET    /api/analytics/inventory-snapshots/out_of_stock/      - Нулевой остаток
```

---

## 🎯 Как это работает

### 🔄 Автоматический сбор данных (Django Signals)

**Всё работает автоматически!** Не нужно ничего вызывать вручную.

#### 1. При завершении продажи:
```python
sale.status = 'completed'
sale.save()
# → автоматически обновляется DailySalesReport
# → автоматически обновляется ProductPerformance для каждого товара
# → автоматически обновляется CustomerAnalytics (если есть клиент)
```

#### 2. При движении товара:
```python
StockMovement.objects.create(...)
# → автоматически обновляется InventorySnapshot
```

#### 3. При платеже клиента:
```python
customer.add_payment(amount)
# → автоматически обновляется CustomerAnalytics
```

### ⏰ Периодические задачи (Celery)

**Запускаются автоматически по расписанию:**

| Задача | Расписание | Описание |
|--------|-----------|----------|
| `generate_daily_sales_report` | Каждый день 00:30 | Дневной отчёт за вчера |
| `generate_product_performance_reports` | Каждый день 01:00 | Товары за вчера |
| `generate_customer_analytics` | Воскресенье 02:00 | RFM анализ всех клиентов |
| `generate_inventory_snapshots` | Каждый день 23:50 | Снимки остатков |
| `cleanup_old_analytics` | 1-го числа 03:00 | Удаление данных >1 года |

---

## 💡 Примеры использования API

### 1. Получить отчёт за сегодня

```bash
GET /api/analytics/daily-sales/today/
Authorization: Bearer <token>
X-Tenant-Key: <tenant_key>
```

**Ответ:**
```json
{
  "id": 15,
  "date": "2025-11-16",
  "total_sales": "125000.00",
  "total_sales_count": 25,
  "avg_sale_amount": "5000.00",
  "cash_sales": "75000.00",
  "card_sales": "50000.00",
  "total_items_sold": 120,
  "unique_customers": 18
}
```

### 2. Топ 10 товаров по выручке

```bash
GET /api/analytics/product-performance/top_products/?limit=10&order_by=revenue
```

**Ответ:**
```json
{
  "period": {
    "start_date": "2025-10-17",
    "end_date": "2025-11-16"
  },
  "top_products": [
    {
      "product_id": 5,
      "product_name": "Молоко 3.2%",
      "total_revenue": "250000.00",
      "total_quantity": "500.000",
      "total_profit": "50000.00",
      "sales_count": 125
    }
  ]
}
```

### 3. Сегментация клиентов (RFM)

```bash
GET /api/analytics/customer-analytics/segments/
```

**Ответ:**
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
      "segment": "Loyal Customers",
      "count": 25,
      "total_spent": "3500000.00",
      "avg_purchase": "35000.00"
    }
  ]
}
```

### 4. Товары с низким остатком

```bash
GET /api/analytics/inventory-snapshots/low_stock_alerts/
```

**Ответ:**
```json
{
  "date": "2025-11-16",
  "count": 5,
  "products": [
    {
      "product_name": "Хлеб белый",
      "quantity_on_hand": "3.000",
      "days_of_stock": 1,
      "is_low_stock": true
    }
  ]
}
```

---

## 🔥 Преимущества системы

### ✅ Полная автоматизация
- Не нужно вручную создавать отчёты
- Signals обновляют данные в реальном времени
- Celery генерирует сводные отчёты ночью

### ✅ Высокая производительность
- Агрегированные данные (не пересчитываются каждый раз)
- Индексы для быстрых запросов
- Периодические задачи в нерабочее время

### ✅ Мощная аналитика
- **Продажи**: выручка, платежи, средний чек
- **Товары**: топ продажи, маржинальность, медленные
- **Клиенты**: RFM сегментация (11 сегментов)
- **Остатки**: оборачиваемость, стоп-листы

### ✅ REST API
- Все отчёты доступны через API
- Фильтрация и сортировка
- Swagger документация

---

## ⚙️ Настройка Celery (опционально)

Для работы периодических задач нужно настроить Celery Beat.

### 1. Установить Redis (если не установлен)

```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt install redis-server
sudo systemctl start redis
```

### 2. Добавить в config/celery.py

```python
# config/celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

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
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
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

### 3. Запустить Celery

```bash
# Worker
celery -A config worker -l info

# Beat (в отдельном терминале)
celery -A config beat -l info
```

---

## ⚠️ Важно:

1. **Все запросы требуют**:
   - `Authorization: Bearer <access_token>`
   - `X-Tenant-Key: <tenant_key>`

2. **Данные обновляются автоматически** через Signals

3. **Celery опционален** - Signals работают и без него (но периодические отчёты не запустятся)

4. **Read-only API** - все ViewSet только для чтения (данные обновляются автоматически)

---

## 📚 Документация:

Полное руководство: [ANALYTICS_GUIDE.md](ANALYTICS_GUIDE.md)

---

**Всё готово к работе! 🎉**

Просто выполни миграции и аналитика начнёт работать автоматически!
