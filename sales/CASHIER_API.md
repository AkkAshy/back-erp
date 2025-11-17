# API для работы кассы

## Обзор

Новый API для работы кассы в стиле "сканируй и продавай". Кассир сканирует товары, суммы рассчитываются автоматически, и по нажатию кнопки "Продать" продажа завершается.

## Эндпоинты

### 1. Сканировать товар (создать/обновить продажу)

**POST** `/api/sales/scan-item/`

Автоматически создаёт новую продажу (черновик) или добавляет товар в текущую незавершённую продажу.

**Request:**
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
    "session": 1,
    "subtotal": "150000.00",
    "total_amount": "150000.00",
    "items": [
      {
        "id": 1,
        "product": 18,
        "product_name": "iPhone 14 Pro",
        "quantity": "2.000",
        "unit_price": "75000.00",
        "line_total": "150000.00"
      }
    ],
    "payments": []
  }
}
```

### 2. Получить текущую незавершённую продажу

**GET** `/api/sales/current/?session=1`

Возвращает текущую незавершённую продажу (черновик) для указанной смены.

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 123,
    "receipt_number": "CHECK-20250117120530",
    "status": "pending",
    "total_amount": "150000.00",
    "items": [...]
  }
}
```

### 3. Добавить товар в существующую продажу

**POST** `/api/sales/{sale_id}/add-item/`

Добавляет товар в существующую незавершённую продажу.

**Request:**
```json
{
  "product": 19,
  "quantity": 1,
  "batch": null
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Товар добавлен",
  "data": {...}
}
```

### 4. Удалить товар из продажи

**DELETE** `/api/sales/{sale_id}/remove-item/`

Удаляет товар из незавершённой продажи.

**Request:**
```json
{
  "item_id": 1
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Товар удалён",
  "data": {...}
}
```

### 5. Завершить продажу (Checkout)

**POST** `/api/sales/{sale_id}/checkout/`

Оформляет оплату и завершает продажу.

**Request:**
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

**Response:**
```json
{
  "status": "success",
  "message": "Продажа завершена",
  "data": {
    "id": 123,
    "receipt_number": "CHECK-20250117120530",
    "status": "completed",
    "total_amount": "150000.00",
    "completed_at": "2025-01-17T12:05:45Z",
    "items": [...],
    "payments": [
      {
        "id": 1,
        "payment_method": "cash",
        "amount": "150000.00",
        "received_amount": "200000.00",
        "change_amount": "50000.00"
      }
    ]
  }
}
```

## Типичный флоу работы кассы

### Сценарий 1: Простая продажа

1. **Кассир сканирует первый товар**
   ```
   POST /api/sales/scan-item/
   { "session": 1, "product": 18, "quantity": 1 }
   → Создаётся продажа со статусом "pending"
   ```

2. **Кассир сканирует второй товар**
   ```
   POST /api/sales/scan-item/
   { "session": 1, "product": 19, "quantity": 2 }
   → Товар добавляется в ту же продажу
   ```

3. **Кассир нажимает "Продать"**
   ```
   POST /api/sales/{sale_id}/checkout/
   { "payments": [{"payment_method": "cash", "amount": 300000, "received_amount": 300000}] }
   → Продажа завершается (status = "completed")
   ```

### Сценарий 2: Отмена товара

1. **Кассир сканировал не тот товар**
   ```
   DELETE /api/sales/{sale_id}/remove-item/
   { "item_id": 2 }
   → Товар удаляется, суммы пересчитываются
   ```

### Сценарий 3: Проверка текущей продажи

1. **Кассир хочет увидеть текущий чек**
   ```
   GET /api/sales/current/?session=1
   → Возвращает текущую незавершённую продажу или null
   ```

## Поля платежей

### payment_method
- `cash` - Наличные
- `card` - Банковская карта
- `mobile` - Мобильный платёж
- `transfer` - Перевод

### Для наличных
```json
{
  "payment_method": "cash",
  "amount": 150000,
  "received_amount": 200000  // Сумма, которую дал клиент
}
```
Backend автоматически рассчитает сдачу: `change_amount = received_amount - amount`

### Для карты
```json
{
  "payment_method": "card",
  "amount": 150000,
  "card_last4": "4242",  // Последние 4 цифры карты
  "transaction_id": "TXN123456"  // ID транзакции
}
```

## Автоматическое поведение

1. **Автоматический расчёт цен**: При сканировании товара цена берётся из `product.pricing.sale_price`
2. **Автоматический расчёт сумм**: После добавления/удаления товара суммы пересчитываются автоматически
3. **Автоматическая генерация номера чека**: При создании продажи генерируется уникальный номер формата `CHECK-YYYYMMDDHHMMSS`
4. **Автоматический расчёт сдачи**: При оплате наличными сдача рассчитывается автоматически

## Статусы продажи

- `pending` - В обработке (черновик, можно добавлять/удалять товары)
- `completed` - Завершена (оплачена)
- `cancelled` - Отменена
- `refunded` - Возврат

## Ошибки

### Смена закрыта
```json
{
  "error": "Смена не найдена или закрыта"
}
```

### Недостаточно оплачено
```json
{
  "error": "Недостаточно оплачено. Нужно: 150000.00, Оплачено: 100000.00"
}
```

### Товар не найден
```json
{
  "error": "Товар не найден"
}
```

## Примечания

- Все цены и суммы в формате `Decimal` с 2 знаками после запятой
- Для работы с кассой смена должна быть открыта (`status = 'open'`)
- Можно иметь только одну незавершённую продажу на смену
- После завершения продажи (checkout) товары списываются со склада автоматически
