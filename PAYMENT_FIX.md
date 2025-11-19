# Исправление: NOT NULL constraint для полей Payment

## Проблема

При создании платежа наличными возникала ошибка:

```
null value in column "card_last4" of relation "sales_payment" violates not-null constraint
```

### Причина:

Поля `card_last4` и `transaction_id` в модели `Payment` имели `blank=True`, но **не имели** `null=True`.

В базе данных эти колонки были созданы как **NOT NULL**, что вызывало ошибку при попытке создать платёж наличными (где эти поля не нужны).

## Решение

### 1. Изменена модель Payment

**Файл:** [sales/models.py:604-617](sales/models.py#L604-L617)

**Было:**
```python
card_last4 = models.CharField(
    max_length=4,
    blank=True,  # ← Только blank, но БЕЗ null
    verbose_name=_('Последние 4 цифры карты')
)

transaction_id = models.CharField(
    max_length=100,
    blank=True,  # ← Только blank, но БЕЗ null
    verbose_name=_('ID транзакции'),
    help_text=_('Номер транзакции для безналичных')
)
```

**Стало:**
```python
card_last4 = models.CharField(
    max_length=4,
    blank=True,
    null=True,  # ← Добавлено!
    verbose_name=_('Последние 4 цифры карты')
)

transaction_id = models.CharField(
    max_length=100,
    blank=True,
    null=True,  # ← Добавлено!
    verbose_name=_('ID транзакции'),
    help_text=_('Номер транзакции для безналичных')
)
```

### 2. Создана миграция

**Файл:** `sales/migrations/0005_fix_payment_nullable_fields.py`

**Команды:**
```bash
python manage.py makemigrations sales --name fix_payment_nullable_fields
python manage.py migrate sales
```

**Результат:**
```
Migrations for 'sales':
  sales/migrations/0005_fix_payment_nullable_fields.py
    ~ Alter field card_last4 on payment
    ~ Alter field transaction_id on payment

Operations to perform:
  Apply all migrations: sales
Running migrations:
  Applying sales.0005_fix_payment_nullable_fields... OK
```

## Разница между blank и null

### `blank=True`
- Валидация на уровне **Django форм**
- Поле может быть **пустым в форме**
- Значение в БД = пустая строка `""`

### `null=True`
- Валидация на уровне **базы данных**
- Колонка может содержать **NULL**
- Значение в БД = `NULL`

### Правильное использование:

| Тип поля | blank | null | Причина |
|----------|-------|------|---------|
| CharField | ✅ | ❌ | Используйте пустую строку `""` |
| CharField (опционально) | ✅ | ✅ | Если NULL имеет смысл |
| TextField | ✅ | ❌ | Используйте пустую строку `""` |
| IntegerField | ✅ | ✅ | Числа не могут быть пустыми строками |
| DecimalField | ✅ | ✅ | Числа не могут быть пустыми строками |
| DateField | ✅ | ✅ | Даты не могут быть пустыми строками |
| ForeignKey | ✅ | ✅ | Связи требуют NULL для опциональности |

**Для CharField обычно:**
- Если поле обязательное: `blank=False` (по умолчанию)
- Если поле опциональное: `blank=True` (пустая строка)
- **Редко:** `blank=True, null=True` (если NULL имеет особое значение)

**В нашем случае:**
```python
card_last4 = models.CharField(blank=True, null=True)
```
- `blank=True` - можно не заполнять в форме
- `null=True` - можно сохранить NULL в БД (для наличных платежей)

## Тестирование

### Тест 1: Платёж наличными

```python
payment = Payment.objects.create(
    sale=sale,
    session=session,
    payment_method='cash',
    amount=Decimal('1500000.00'),
    received_amount=Decimal('2000000.00')
    # card_last4 не указан → будет NULL ✅
    # transaction_id не указан → будет NULL ✅
)

print(payment.card_last4)  # None
print(payment.transaction_id)  # None
```

**Результат:** ✅ Успешно создано

### Тест 2: Платёж картой

```python
payment = Payment.objects.create(
    sale=sale,
    session=session,
    payment_method='card',
    amount=Decimal('1500000.00'),
    card_last4='1234',
    transaction_id='TXN123456789'
)

print(payment.card_last4)  # '1234'
print(payment.transaction_id)  # 'TXN123456789'
```

**Результат:** ✅ Успешно создано

### Тест 3: API - создание продажи с платежом

```bash
POST /api/sales/sales/
Headers:
  Authorization: Bearer {token}
  X-Tenant-Key: admin_1a12e47a

Body:
{
  "session": 2,
  "receipt_number": "TEST-001",
  "items": [
    {
      "product": 19,
      "quantity": 1,
      "unit_price": 300000
    }
  ],
  "payments": [
    {
      "payment_method": "cash",
      "amount": 300000,
      "received_amount": 500000
    }
  ]
}
```

**Результат:** ✅ Успешно создано

## Примеры использования

### 1. Наличные (cash)

```json
{
  "payment_method": "cash",
  "amount": 300000,
  "received_amount": 500000
}
```

**Поля:**
- `card_last4` → `null` ✅
- `transaction_id` → `null` ✅
- `change_amount` → автоматически `200000` (500000 - 300000)

### 2. Карта (card)

```json
{
  "payment_method": "card",
  "amount": 300000,
  "card_last4": "1234",
  "transaction_id": "TXN123456789"
}
```

**Поля:**
- `card_last4` → `"1234"` ✅
- `transaction_id` → `"TXN123456789"` ✅
- `received_amount` → `null` ✅
- `change_amount` → `0` ✅

### 3. Перевод (transfer)

```json
{
  "payment_method": "transfer",
  "amount": 300000,
  "transaction_id": "TRANSFER-123"
}
```

**Поля:**
- `card_last4` → `null` ✅
- `transaction_id` → `"TRANSFER-123"` ✅

## Frontend примеры

### TypeScript интерфейс:

```typescript
export interface Payment {
  payment_method: 'cash' | 'card' | 'transfer' | 'online' | 'credit' | 'other';
  amount: number;
  received_amount?: number;  // Только для cash
  card_last4?: string;       // Только для card
  transaction_id?: string;   // Для card/transfer/online
  notes?: string;
}

// Пример: наличные
const cashPayment: Payment = {
  payment_method: 'cash',
  amount: 300000,
  received_amount: 500000
  // card_last4 не нужен
  // transaction_id не нужен
};

// Пример: карта
const cardPayment: Payment = {
  payment_method: 'card',
  amount: 300000,
  card_last4: '1234',
  transaction_id: 'TXN123'
  // received_amount не нужен
};
```

### React компонент:

```typescript
import { useState } from 'react';

export const PaymentForm = ({ amount, onSubmit }) => {
  const [method, setMethod] = useState('cash');
  const [receivedAmount, setReceivedAmount] = useState('');
  const [cardLast4, setCardLast4] = useState('');
  const [transactionId, setTransactionId] = useState('');

  const handleSubmit = () => {
    const payment: any = {
      payment_method: method,
      amount: amount
    };

    // Добавляем поля в зависимости от метода оплаты
    if (method === 'cash') {
      payment.received_amount = parseFloat(receivedAmount);
    } else if (method === 'card') {
      if (cardLast4) payment.card_last4 = cardLast4;
      if (transactionId) payment.transaction_id = transactionId;
    } else if (method === 'transfer' || method === 'online') {
      if (transactionId) payment.transaction_id = transactionId;
    }

    onSubmit(payment);
  };

  return (
    <div>
      <select value={method} onChange={(e) => setMethod(e.target.value)}>
        <option value="cash">Наличные</option>
        <option value="card">Карта</option>
        <option value="transfer">Перевод</option>
      </select>

      {method === 'cash' && (
        <input
          type="number"
          placeholder="Получено от клиента"
          value={receivedAmount}
          onChange={(e) => setReceivedAmount(e.target.value)}
        />
      )}

      {method === 'card' && (
        <>
          <input
            type="text"
            placeholder="Последние 4 цифры карты"
            maxLength={4}
            value={cardLast4}
            onChange={(e) => setCardLast4(e.target.value)}
          />
          <input
            type="text"
            placeholder="ID транзакции"
            value={transactionId}
            onChange={(e) => setTransactionId(e.target.value)}
          />
        </>
      )}

      <button onClick={handleSubmit}>Оплатить</button>
    </div>
  );
};
```

## Резюме

### Что было исправлено:
- ✅ Добавлено `null=True` к полям `card_last4` и `transaction_id`
- ✅ Создана и применена миграция
- ✅ Теперь можно создавать платежи наличными без ошибок

### Затронутые поля:
- `card_last4` - Последние 4 цифры карты (опционально)
- `transaction_id` - ID транзакции (опционально)

### Методы оплаты:
| Метод | card_last4 | transaction_id | received_amount |
|-------|------------|----------------|-----------------|
| cash | null | null | ✅ Обязательно |
| card | ✅ Опционально | ✅ Опционально | null |
| transfer | null | ✅ Опционально | null |
| online | null | ✅ Опционально | null |
| credit | null | null | null |

Готово! 🎉
