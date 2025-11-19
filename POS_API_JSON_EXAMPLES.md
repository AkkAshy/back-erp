# POS API - Примеры JSON запросов и ответов

## 🔐 1. Авторизация (Login)

### Запрос
```http
POST /api/users/auth/login/
Content-Type: application/json
```

```json
{
  "username": "testuser",
  "password": "test123456"
}
```

### Ответ (200 OK)
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY4NjI4MjEwLCJpYXQiOjE3NjM0NDQyMTAsImp0aSI6ImNiNDY2ZjI5MjljYzRiZDI5YTEzZTY5NTBhNjkyNzE3IiwidXNlcl9pZCI6MX0.YZUfP1M93jD6q3QbW1qONU-HNN8eU40nwCqxJeypvv0",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 4,
    "username": "testuser",
    "email": "test@test.com",
    "full_name": "Test User"
  },
  "available_stores": [
    {
      "id": 1,
      "name": "admin",
      "slug": "admin",
      "tenant_key": "admin_1a12e47a",
      "role": "owner",
      "role_display": "Владелец",
      "permissions": [
        "view_all",
        "create_all",
        "update_all",
        "delete_all"
      ]
    }
  ],
  "default_store": {
    "tenant_key": "admin_1a12e47a",
    "name": "admin",
    "role": "owner"
  }
}
```

---

## 📅 2. Получить текущую смену

### Запрос
```http
GET /api/sales/sessions/current/
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
```

**Нет body** - это GET запрос

### Ответ (200 OK) - Смена открыта
```json
{
  "id": 2,
  "cash_register": 1,
  "cash_register_name": "Главная касса",
  "cashier": 1,
  "cashier_name": "фывфыв фывфц",
  "status": "open",
  "status_display": "Открыта",
  "opening_balance": "1000000.00",
  "current_balance": "1000000.00",
  "expected_balance": "1000000.00",
  "closing_balance": null,
  "difference": null,
  "opened_at": "2025-11-18T05:34:00.738066+05:00",
  "closed_at": null,
  "notes": ""
}
```

### Ответ (200 OK) - Нет открытой смены
```json
{
  "detail": "Нет активной смены"
}
```

---

## 🏪 3. Открыть смену

### Запрос
```http
POST /api/sales/sessions/
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
Content-Type: application/json
```

```json
{
  "cash_register": 1,
  "opening_balance": 1000000,
  "notes": "Начало рабочего дня"
}
```

### Ответ (201 Created)
```json
{
  "id": 3,
  "cash_register": 1,
  "cash_register_name": "Главная касса",
  "cashier": 4,
  "cashier_name": "Test User",
  "status": "open",
  "status_display": "Открыта",
  "opening_balance": "1000000.00",
  "current_balance": "1000000.00",
  "expected_balance": "1000000.00",
  "closing_balance": null,
  "difference": null,
  "opened_at": "2025-11-18T11:30:00.123456+05:00",
  "closed_at": null,
  "notes": "Начало рабочего дня"
}
```

---

## 🛒 4. Получить текущую продажу

### Запрос
```http
GET /api/sales/sales/current/?session=2
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
```

**Нет body** - это GET запрос

### Ответ (200 OK) - Есть незавершённая продажа
```json
{
  "id": 5,
  "session": 2,
  "session_info": "Главная касса",
  "cashier_name": "Test User",
  "receipt_number": "CHECK-20251118113500",
  "status": "pending",
  "status_display": "В обработке",
  "customer": null,
  "customer_info": null,
  "customer_name": "",
  "customer_phone": "",
  "subtotal": "300000.00",
  "discount_amount": "0.00",
  "discount_percent": "0.00",
  "tax_amount": "0.00",
  "total_amount": "300000.00",
  "items_count": 1,
  "total_quantity": "1.000",
  "notes": "",
  "created_at": "2025-11-18T11:35:00.123456+05:00",
  "completed_at": null,
  "items": [
    {
      "id": 10,
      "sale": 5,
      "product": 19,
      "product_name": "фывфцв",
      "product_sku": "FYVFTSV_20251117_AA21162A",
      "batch": null,
      "batch_number": null,
      "quantity": "1.000",
      "unit_price": "300000.00",
      "discount_amount": "0.00",
      "tax_rate": "0.00",
      "line_total": "300000.00",
      "reservation": null,
      "created_at": "2025-11-18T11:35:00.456789+05:00"
    }
  ],
  "payments": []
}
```

### Ответ (200 OK) - Нет активной продажи
```json
{
  "detail": "Нет активной продажи"
}
```

---

## 🔍 5. Сканировать штрих-код (только поиск товара)

### Запрос
```http
GET /api/products/products/scan_barcode/?barcode=4877667646003
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
```

**Нет body** - это GET запрос, параметры в URL

### Ответ (200 OK) - Товар найден
```json
{
  "status": "success",
  "data": {
    "id": 19,
    "name": "фывфцв",
    "slug": "fyvftsv-3d5a651b",
    "description": "фывфцв",
    "category": 17,
    "category_name": "Дом и сад",
    "category_path": "Дом и сад",
    "sku": "FYVFTSV_20251117_AA21162A",
    "barcode": "4877667646003",
    "unit": 2,
    "unit_name": "Килограмм",
    "unit_short": "кг",
    "main_image": null,
    "weight": "123.000",
    "volume": null,
    "is_active": true,
    "is_featured": false,
    "pricing": {
      "id": 14,
      "product": 19,
      "cost_price": "129999.00",
      "sale_price": "300000.00",
      "wholesale_price": "200000.00",
      "tax_rate": "0.00",
      "margin": "130.77",
      "profit": "170001.00",
      "updated_at": "2025-11-17T19:27:35.286297+05:00"
    },
    "inventory": {
      "id": 14,
      "product": 19,
      "quantity_on_hand": "47.000",
      "quantity_reserved": "0.000",
      "quantity_available": "47.000",
      "reorder_level": "0.000",
      "reorder_quantity": "0.000",
      "last_restock_date": null,
      "last_updated": "2025-11-17T19:30:58.629154+05:00"
    },
    "images": [],
    "attributes": [],
    "tags": [],
    "created_at": "2025-11-17T19:27:35.266815+05:00",
    "updated_at": "2025-11-17T19:27:35.295046+05:00"
  }
}
```

### Ответ (404 Not Found) - Товар не найден
```json
{
  "status": "error",
  "message": "Товар с штрих-кодом \"1234567890\" не найден",
  "code": "product_not_found",
  "barcode": "1234567890"
}
```

---

## ➕ 6. Добавить товар в продажу (scan_item)

### Запрос
```http
POST /api/sales/sales/scan_item/
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
Content-Type: application/json
```

```json
{
  "session": 2,
  "product": 19,
  "quantity": 1
}
```

**Опциональные поля:**
```json
{
  "session": 2,
  "product": 19,
  "quantity": 2.5,
  "batch": 5
}
```

### Ответ (200 OK) - Товар добавлен
```json
{
  "status": "success",
  "message": "Товар добавлен",
  "data": {
    "id": 5,
    "session": 2,
    "session_info": "Главная касса",
    "cashier_name": "Test User",
    "receipt_number": "CHECK-20251118113500",
    "status": "pending",
    "status_display": "В обработке",
    "customer": null,
    "customer_info": null,
    "customer_name": "",
    "customer_phone": "",
    "subtotal": "450000.00",
    "discount_amount": "0.00",
    "discount_percent": "0.00",
    "tax_amount": "0.00",
    "total_amount": "450000.00",
    "items_count": 2,
    "total_quantity": "3.000",
    "notes": "",
    "created_at": "2025-11-18T11:35:00.123456+05:00",
    "completed_at": null,
    "items": [
      {
        "id": 10,
        "sale": 5,
        "product": 19,
        "product_name": "фывфцв",
        "product_sku": "FYVFTSV_20251117_AA21162A",
        "batch": null,
        "batch_number": null,
        "quantity": "1.000",
        "unit_price": "300000.00",
        "discount_amount": "0.00",
        "tax_rate": "0.00",
        "line_total": "300000.00",
        "reservation": null,
        "created_at": "2025-11-18T11:35:00.456789+05:00"
      },
      {
        "id": 11,
        "sale": 5,
        "product": 18,
        "product_name": "Test Futbolka",
        "product_sku": "TEST_FUTBOLKA_20251117_939596D3",
        "batch": null,
        "batch_number": null,
        "quantity": "2.000",
        "unit_price": "75000.00",
        "discount_amount": "0.00",
        "tax_rate": "0.00",
        "line_total": "150000.00",
        "reservation": null,
        "created_at": "2025-11-18T11:36:00.789012+05:00"
      }
    ],
    "payments": []
  }
}
```

### Ответ (400 Bad Request) - Ошибка
```json
{
  "status": "error",
  "message": "Смена закрыта, невозможно создать продажу",
  "code": "session_closed"
}
```

---

## 🗑️ 7. Удалить товар из продажи

### Запрос
```http
DELETE /api/sales/sale-items/{item_id}/
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
```

**Нет body** - это DELETE запрос

**Пример:** `DELETE /api/sales/sale-items/11/`

### Ответ (204 No Content)
Нет body в ответе - просто статус 204

---

## ✏️ 8. Изменить количество товара

### Запрос
```http
PATCH /api/sales/sale-items/{item_id}/
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
Content-Type: application/json
```

```json
{
  "quantity": 5
}
```

**Можно также изменить:**
```json
{
  "quantity": 3,
  "discount_amount": 10000
}
```

### Ответ (200 OK)
```json
{
  "id": 10,
  "sale": 5,
  "product": 19,
  "product_name": "фывфцв",
  "product_sku": "FYVFTSV_20251117_AA21162A",
  "batch": null,
  "batch_number": null,
  "quantity": "5.000",
  "unit_price": "300000.00",
  "discount_amount": "0.00",
  "tax_rate": "0.00",
  "line_total": "1500000.00",
  "reservation": null,
  "created_at": "2025-11-18T11:35:00.456789+05:00"
}
```

---

## 💰 9. Завершить продажу с оплатой

### Запрос - Наличные
```http
POST /api/sales/sales/{sale_id}/complete/
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
Content-Type: application/json
```

```json
{
  "payments": [
    {
      "payment_method": "cash",
      "amount": 450000,
      "received_amount": 500000
    }
  ]
}
```

### Запрос - Карта
```json
{
  "payments": [
    {
      "payment_method": "card",
      "amount": 450000,
      "card_last4": "1234",
      "transaction_id": "TXN-123456789"
    }
  ]
}
```

### Запрос - Смешанная оплата
```json
{
  "payments": [
    {
      "payment_method": "cash",
      "amount": 250000,
      "received_amount": 300000
    },
    {
      "payment_method": "card",
      "amount": 200000,
      "card_last4": "5678",
      "transaction_id": "TXN-987654321"
    }
  ]
}
```

### Запрос - С клиентом
```json
{
  "customer": 3,
  "payments": [
    {
      "payment_method": "cash",
      "amount": 450000,
      "received_amount": 500000
    }
  ],
  "notes": "Постоянный клиент, дал скидку"
}
```

### Ответ (200 OK)
```json
{
  "status": "success",
  "message": "Продажа завершена",
  "data": {
    "id": 5,
    "session": 2,
    "session_info": "Главная касса",
    "cashier_name": "Test User",
    "receipt_number": "CHECK-20251118113500",
    "status": "completed",
    "status_display": "Завершена",
    "customer": null,
    "customer_info": null,
    "customer_name": "",
    "customer_phone": "",
    "subtotal": "450000.00",
    "discount_amount": "0.00",
    "discount_percent": "0.00",
    "tax_amount": "0.00",
    "total_amount": "450000.00",
    "items_count": 2,
    "total_quantity": "3.000",
    "notes": "",
    "created_at": "2025-11-18T11:35:00.123456+05:00",
    "completed_at": "2025-11-18T11:40:00.789012+05:00",
    "items": [
      {
        "id": 10,
        "sale": 5,
        "product": 19,
        "product_name": "фывфцв",
        "product_sku": "FYVFTSV_20251117_AA21162A",
        "batch": null,
        "batch_number": null,
        "quantity": "1.000",
        "unit_price": "300000.00",
        "discount_amount": "0.00",
        "tax_rate": "0.00",
        "line_total": "300000.00",
        "reservation": null,
        "created_at": "2025-11-18T11:35:00.456789+05:00"
      },
      {
        "id": 11,
        "sale": 5,
        "product": 18,
        "product_name": "Test Futbolka",
        "product_sku": "TEST_FUTBOLKA_20251117_939596D3",
        "batch": null,
        "batch_number": null,
        "quantity": "2.000",
        "unit_price": "75000.00",
        "discount_amount": "0.00",
        "tax_rate": "0.00",
        "line_total": "150000.00",
        "reservation": null,
        "created_at": "2025-11-18T11:36:00.789012+05:00"
      }
    ],
    "payments": [
      {
        "id": 12,
        "sale": 5,
        "session": 2,
        "payment_method": "cash",
        "payment_method_display": "Наличные",
        "amount": "450000.00",
        "received_amount": "500000.00",
        "change_amount": "50000.00",
        "card_last4": null,
        "transaction_id": null,
        "status": "completed",
        "status_display": "Завершён",
        "notes": "",
        "created_at": "2025-11-18T11:40:00.123456+05:00"
      }
    ]
  }
}
```

### Ответ (400 Bad Request) - Ошибки
```json
{
  "payments": [
    "Необходимо добавить хотя бы один способ оплаты"
  ]
}
```

```json
{
  "payments": [
    "Сумма оплат (400000.00) не совпадает с суммой продажи (450000.00)"
  ]
}
```

---

## 🚫 10. Отменить продажу

### Запрос
```http
POST /api/sales/sales/{sale_id}/cancel/
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
Content-Type: application/json
```

```json
{
  "reason": "Клиент передумал"
}
```

**`reason` - опциональное поле**

### Ответ (200 OK)
```json
{
  "status": "success",
  "message": "Продажа отменена",
  "data": {
    "id": 5,
    "status": "cancelled",
    "status_display": "Отменена"
  }
}
```

---

## 🔒 11. Закрыть смену

### Запрос
```http
POST /api/sales/sessions/{session_id}/close/
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
Content-Type: application/json
```

```json
{
  "closing_balance": 1450000,
  "notes": "Конец рабочего дня"
}
```

### Ответ (200 OK)
```json
{
  "id": 2,
  "cash_register": 1,
  "cash_register_name": "Главная касса",
  "cashier": 4,
  "cashier_name": "Test User",
  "status": "closed",
  "status_display": "Закрыта",
  "opening_balance": "1000000.00",
  "current_balance": "1450000.00",
  "expected_balance": "1450000.00",
  "closing_balance": "1450000.00",
  "difference": "0.00",
  "opened_at": "2025-11-18T11:30:00.123456+05:00",
  "closed_at": "2025-11-18T18:00:00.789012+05:00",
  "notes": "Конец рабочего дня"
}
```

### Ответ (400 Bad Request)
```json
{
  "detail": "Есть незавершённые продажи. Завершите или отмените их перед закрытием смены."
}
```

---

## 📊 12. Получить список продаж за смену

### Запрос
```http
GET /api/sales/sales/?session=2
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
```

**Нет body** - это GET запрос

### Ответ (200 OK)
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 5,
      "session": 2,
      "receipt_number": "CHECK-20251118113500",
      "status": "completed",
      "total_amount": "450000.00",
      "created_at": "2025-11-18T11:35:00.123456+05:00"
    },
    {
      "id": 4,
      "session": 2,
      "receipt_number": "CHECK-20251118110000",
      "status": "completed",
      "total_amount": "300000.00",
      "created_at": "2025-11-18T11:00:00.123456+05:00"
    }
  ]
}
```

---

## 🎫 13. Печать чека

### Запрос
```http
GET /api/sales/sales/{sale_id}/receipt/
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
```

**Нет body** - это GET запрос

### Ответ (200 OK)
```json
{
  "receipt": {
    "store_name": "admin",
    "store_address": "",
    "store_phone": "",
    "receipt_number": "CHECK-20251118113500",
    "cashier": "Test User",
    "date": "2025-11-18T11:40:00.789012+05:00",
    "items": [
      {
        "name": "фывфцв",
        "quantity": "1.000",
        "unit_price": "300000.00",
        "total": "300000.00"
      },
      {
        "name": "Test Futbolka",
        "quantity": "2.000",
        "unit_price": "75000.00",
        "total": "150000.00"
      }
    ],
    "subtotal": "450000.00",
    "discount": "0.00",
    "tax": "0.00",
    "total": "450000.00",
    "payments": [
      {
        "method": "Наличные",
        "amount": "450000.00",
        "received": "500000.00",
        "change": "50000.00"
      }
    ]
  }
}
```

---

## 👥 14. Список клиентов (для выбора)

### Запрос
```http
GET /api/customers/customers/?search=иван
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
```

**Нет body** - это GET запрос

### Ответ (200 OK)
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 3,
      "full_name": "Иван Иванов",
      "phone": "+998901234567",
      "email": "ivan@example.com",
      "total_purchases": "1500000.00",
      "last_purchase_date": "2025-11-15T10:30:00+05:00"
    }
  ]
}
```

---

## 📦 Типичный сценарий работы POS

### 1️⃣ Начало смены
```
POST /api/sales/sessions/
{ "cash_register": 1, "opening_balance": 1000000 }
```

### 2️⃣ Клиент приносит товар
```
GET /api/products/products/scan_barcode/?barcode=4877667646003
→ Получаем информацию о товаре
```

### 3️⃣ Добавляем товар в продажу
```
POST /api/sales/sales/scan_item/
{ "session": 2, "product": 19, "quantity": 1 }
→ Создаётся новая продажа или добавляется к существующей
```

### 4️⃣ Сканируем ещё товары
```
POST /api/sales/sales/scan_item/
{ "session": 2, "product": 18, "quantity": 2 }
```

### 5️⃣ Проверяем текущую продажу
```
GET /api/sales/sales/current/?session=2
→ Видим все товары и итоговую сумму
```

### 6️⃣ Завершаем продажу с оплатой
```
POST /api/sales/sales/5/complete/
{
  "payments": [{
    "payment_method": "cash",
    "amount": 450000,
    "received_amount": 500000
  }]
}
```

### 7️⃣ Печатаем чек
```
GET /api/sales/sales/5/receipt/
```

### 8️⃣ Конец смены
```
POST /api/sales/sessions/2/close/
{ "closing_balance": 1450000 }
```

---

## 🔑 Важные заголовки для всех запросов

```http
Authorization: Bearer {access_token}
X-Tenant-Key: admin_1a12e47a
Content-Type: application/json
```

## ⚠️ Типичные ошибки

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```
→ Не указан токен в заголовке `Authorization`

### 403 Forbidden
```json
{
  "detail": "У вас нет доступа к этому магазину"
}
```
→ Неправильный `X-Tenant-Key`

### 400 Bad Request
```json
{
  "field_name": [
    "Это поле обязательно."
  ]
}
```
→ Не все обязательные поля заполнены

---

Готово! 🎉
