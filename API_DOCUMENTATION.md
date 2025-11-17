# ERP v2 - API Documentation

## Обзор

Полная документация API для мультитенантной POS системы.

**Base URL:** `http://localhost:8000`

**Swagger UI:** `http://localhost:8000/swagger/`

**ReDoc:** `http://localhost:8000/redoc/`

## Аутентификация

API использует JWT токены. Токен нужно добавлять в заголовок каждого запроса:

```
Authorization: Bearer <your_access_token>
```

---

## 1. Authentication (`/api/users/`)

### 1.1 Регистрация
**POST** `/api/users/auth/register/`

Создаёт нового пользователя и магазин.

**Request:**
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "TestPass123!",
  "password2": "TestPass123!",
  "first_name": "Test",
  "last_name": "User",
  "store_name": "Test Store",
  "phone": "+998901234567"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Пользователь успешно зарегистрирован",
  "data": {
    "user": {...},
    "tokens": {
      "access": "...",
      "refresh": "..."
    }
  }
}
```

### 1.2 Вход
**POST** `/api/users/auth/login/`

**Request:**
```json
{
  "username": "testuser",
  "password": "TestPass123!"
}
```

### 1.3 Профиль
**GET** `/api/users/profile/`

Возвращает информацию о текущем пользователе.

---

## 2. Products (`/api/products/`)

### 2.1 Список товаров
**GET** `/api/products/products/`

**Query Parameters:**
- `search` - поиск по названию, SKU, штрихкоду
- `category` - фильтр по категории
- `is_active` - активные товары (true/false)
- `ordering` - сортировка (-created_at, name, sale_price)

### 2.2 Создать товар
**POST** `/api/products/products/`

**Request:**
```json
{
  "name": "iPhone 14 Pro",
  "sku": "IPHONE-14-PRO",
  "barcode": "1234567890123",
  "description": "Latest iPhone model",
  "cost_price": 50000,
  "sale_price": 75000,
  "wholesale_price": 65000,
  "tax_rate": 12,
  "unit": "pcs"
}
```

### 2.3 Товары с низким остатком
**GET** `/api/products/products/low-stock/`

### 2.4 Категории
**GET** `/api/products/categories/`

**POST** `/api/products/categories/`

---

## 3. Sales / Cashier (`/api/sales/`)

### 3.1 Управление сменой

#### Открыть смену
**POST** `/api/sales/sessions/open/`

```json
{
  "opening_balance": 100000
}
```

#### Получить текущую смену
**GET** `/api/sales/sessions/current/`

#### Закрыть смену
**POST** `/api/sales/sessions/:session_id/close/`

```json
{
  "actual_cash": 250000
}
```

#### Отчёт по смене
**GET** `/api/sales/sessions/:session_id/report/`

### 3.2 Работа с продажами (Касса)

#### Сканировать товар
**POST** `/api/sales/sales/scan-item/`

Автоматически создаёт продажу или добавляет в текущую.

```json
{
  "session": 1,
  "product": 18,
  "quantity": 2,
  "batch": null
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Товар добавлен",
  "data": {
    "id": 123,
    "receipt_number": "CHECK-20250117120530",
    "status": "pending",
    "total_amount": "150000.00",
    "items": [...]
  }
}
```

#### Получить текущую продажу
**GET** `/api/sales/sales/current/?session=1`

Возвращает незавершённую продажу (черновик).

#### Добавить товар
**POST** `/api/sales/sales/:sale_id/add-item/`

```json
{
  "product": 19,
  "quantity": 1,
  "batch": null
}
```

#### Удалить товар
**DELETE** `/api/sales/sales/:sale_id/remove-item/`

```json
{
  "item_id": 1
}
```

#### Завершить продажу (Checkout)
**POST** `/api/sales/sales/:sale_id/checkout/`

```json
{
  "payments": [
    {
      "payment_method": "cash",
      "amount": 150000,
      "received_amount": 200000
    }
  ]
}
```

**Для нескольких способов оплаты:**
```json
{
  "payments": [
    {
      "payment_method": "cash",
      "amount": 100000,
      "received_amount": 100000
    },
    {
      "payment_method": "card",
      "amount": 50000,
      "card_last4": "4242",
      "transaction_id": "TXN123456"
    }
  ]
}
```

#### Отменить продажу
**POST** `/api/sales/sales/:sale_id/cancel/`

#### Возврат
**POST** `/api/sales/sales/:sale_id/refund/`

### 3.3 Список продаж

#### Все продажи
**GET** `/api/sales/sales/`

**Query Parameters:**
- `status` - pending, completed, cancelled, refunded
- `session` - ID смены
- `search` - по номеру чека, имени клиента, телефону

#### Продажи за сегодня
**GET** `/api/sales/sales/today/`

---

## 4. Analytics (`/api/analytics/`)

### 4.1 Дневные отчёты

#### Список отчётов
**GET** `/api/analytics/daily-sales/`

#### Отчёт за сегодня
**GET** `/api/analytics/daily-sales/today/`

**Response:**
```json
{
  "id": 1,
  "date": "2025-01-17",
  "total_sales": "1500000.00",
  "total_sales_count": 45,
  "avg_sale_amount": "33333.33",
  "total_discount": "50000.00",
  "total_tax": "180000.00",
  "total_items_sold": "120.000",
  "unique_customers": 38
}
```

#### Отчёт за период
**GET** `/api/analytics/daily-sales/period/?start_date=2025-01-01&end_date=2025-01-31`

**Response:**
```json
{
  "period": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "days": 31
  },
  "totals": {
    "total_sales": "45000000.00",
    "total_count": 1250,
    "avg_sale": "36000.00"
  },
  "daily_reports": [...]
}
```

#### График продаж (тренды)
**GET** `/api/analytics/daily-sales/trends/?days=30`

### 4.2 Производительность товаров

#### Топ товаров
**GET** `/api/analytics/product-performance/top-products/?limit=10&order_by=revenue`

**Query Parameters:**
- `start_date`, `end_date` - период (по умолчанию последние 30 дней)
- `limit` - количество (по умолчанию 10)
- `order_by` - revenue (выручка), quantity (количество), profit (прибыль)

**Response:**
```json
{
  "period": {
    "start_date": "2024-12-17",
    "end_date": "2025-01-17"
  },
  "top_products": [
    {
      "product_id": 18,
      "product_name": "iPhone 14 Pro",
      "product_code": "IPHONE-14-PRO",
      "total_revenue": "7500000.00",
      "total_quantity": "100.000",
      "total_profit": "2500000.00",
      "sales_count": 85
    }
  ]
}
```

#### Медленно продающиеся товары
**GET** `/api/analytics/product-performance/slow-movers/?days=30`

### 4.3 Аналитика клиентов (RFM)

#### Сегменты клиентов
**GET** `/api/analytics/customer-analytics/segments/`

Разбивка клиентов по сегментам (Champions, Loyal, At Risk и т.д.)

**Response:**
```json
{
  "period": {
    "period_start": "2024-12-17",
    "period_end": "2025-01-17"
  },
  "segments": [
    {
      "segment": "Champions",
      "count": 25,
      "total_spent": "12500000.00",
      "avg_purchase": "50000.00"
    },
    {
      "segment": "Loyal Customers",
      "count": 40,
      "total_spent": "8000000.00",
      "avg_purchase": "40000.00"
    }
  ]
}
```

#### Клиенты в группе риска
**GET** `/api/analytics/customer-analytics/at-risk/`

Клиенты, которые могут уйти (At Risk, Can't Lose Them, Hibernating, Lost).

### 4.4 Остатки на складе

#### Последние остатки
**GET** `/api/analytics/inventory-snapshots/latest/`

#### Алерты по низким остаткам
**GET** `/api/analytics/inventory-snapshots/low-stock-alerts/`

**Response:**
```json
{
  "date": "2025-01-17",
  "count": 12,
  "products": [
    {
      "id": 1,
      "product": {...},
      "quantity_on_hand": "5.000",
      "reserved_quantity": "2.000",
      "available_quantity": "3.000",
      "days_of_stock": 2.5,
      "is_low_stock": true
    }
  ]
}
```

#### Товары с нулевым остатком
**GET** `/api/analytics/inventory-snapshots/out-of-stock/`

---

## 5. Tasks (`/api/tasks/`)

### 5.1 Управление задачами

#### Список задач
**GET** `/api/tasks/tasks/`

**Query Parameters:**
- `status` - pending, in_progress, completed, cancelled
- `priority` - low, medium, high, urgent
- `assigned_to` - ID сотрудника
- `category` - inventory, sales, customer_service и т.д.

#### Создать задачу
**POST** `/api/tasks/tasks/`

```json
{
  "title": "Проверить остатки товара",
  "description": "Провести инвентаризацию склада",
  "priority": "high",
  "category": "inventory",
  "assigned_to": 1,
  "due_date": "2025-01-20T18:00:00Z"
}
```

#### Мои задачи
**GET** `/api/tasks/tasks/my-tasks/`

Задачи, назначенные текущему пользователю.

#### Задачи на сегодня
**GET** `/api/tasks/tasks/today/`

#### Просроченные задачи
**GET** `/api/tasks/tasks/overdue/`

#### Статистика по задачам
**GET** `/api/tasks/tasks/stats/`

**Response:**
```json
{
  "total": 150,
  "by_status": {
    "pending": 45,
    "in_progress": 32,
    "completed": 68,
    "cancelled": 5
  },
  "by_priority": {
    "low": 30,
    "medium": 80,
    "high": 35,
    "urgent": 5
  },
  "overdue": 8
}
```

### 5.2 Действия с задачами

#### Начать задачу
**POST** `/api/tasks/tasks/:task_id/start/`

Меняет статус на `in_progress`.

#### Завершить задачу
**POST** `/api/tasks/tasks/:task_id/complete/`

#### Отправить на проверку
**POST** `/api/tasks/tasks/:task_id/submit-for-review/`

#### Одобрить задачу
**POST** `/api/tasks/tasks/:task_id/approve/`

#### Отклонить задачу
**POST** `/api/tasks/tasks/:task_id/reject/`

```json
{
  "comment": "Не все пункты выполнены"
}
```

### 5.3 Комментарии

#### Добавить комментарий
**POST** `/api/tasks/comments/`

```json
{
  "task": 1,
  "comment": "Работаю над задачей"
}
```

#### Список комментариев
**GET** `/api/tasks/comments/?task=1`

### 5.4 Шаблоны задач

#### Список шаблонов
**GET** `/api/tasks/templates/`

#### Создать задачу из шаблона
**POST** `/api/tasks/templates/:template_id/create-task/`

```json
{
  "assigned_to": 1,
  "due_date": "2025-01-25T18:00:00Z"
}
```

---

## 6. Customers (`/api/customers/`)

### 6.1 Список клиентов
**GET** `/api/customers/customers/`

### 6.2 Создать клиента
**POST** `/api/customers/customers/`

```json
{
  "name": "Test Customer",
  "phone": "+998901234567",
  "email": "customer@example.com",
  "address": "Tashkent, Uzbekistan"
}
```

### 6.3 Получить клиента
**GET** `/api/customers/customers/:customer_id/`

### 6.4 История покупок клиента
**GET** `/api/customers/customers/:customer_id/purchase-history/`

---

## Статусы и коды

### Статусы продаж
- `pending` - В обработке (черновик)
- `completed` - Завершена
- `cancelled` - Отменена
- `refunded` - Возврат

### Способы оплаты
- `cash` - Наличные
- `card` - Банковская карта
- `mobile` - Мобильный платёж (UzCard, Humo)
- `transfer` - Перевод

### Приоритеты задач
- `low` - Низкий
- `medium` - Средний
- `high` - Высокий
- `urgent` - Срочный

### Статусы задач
- `pending` - Ожидает
- `in_progress` - В работе
- `on_review` - На проверке
- `completed` - Завершена
- `cancelled` - Отменена

### Категории задач
- `inventory` - Склад
- `sales` - Продажи
- `customer_service` - Обслуживание клиентов
- `maintenance` - Обслуживание оборудования
- `cleaning` - Уборка
- `other` - Прочее

---

## Сегменты клиентов (RFM)

- **Champions** - лучшие клиенты (покупают часто, недавно, на большие суммы)
- **Loyal Customers** - лояльные клиенты
- **Potential Loyalist** - потенциально лояльные
- **Recent Customers** - недавние клиенты
- **Promising** - перспективные
- **Need Attention** - требуют внимания
- **At Risk** - в группе риска
- **Can't Lose Them** - ценные клиенты, которых нельзя терять
- **Hibernating** - спящие клиенты
- **Lost** - потерянные клиенты

---

## Коды ошибок

- `400` - Неверный запрос (валидация не прошла)
- `401` - Не авторизован (нужен токен)
- `403` - Доступ запрещён (недостаточно прав)
- `404` - Не найдено
- `500` - Внутренняя ошибка сервера

---

## Postman Collection

Импортируйте файл `ERP_v2_Full.postman_collection.json` в Postman для тестирования API.

**Важно:** После успешного логина токен автоматически сохраняется в переменных коллекции.
