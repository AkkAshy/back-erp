# Создание продажи (Sale)

## Есть 2 способа создать продажу

### 1. Через scan_item (Рекомендуется для POS)
### 2. Через создание полной продажи

---

## Способ 1: Сканирование товаров (scan_item) 🔥

**Самый простой способ для кассы!**

### Endpoint:
```
POST /api/sales/sales/scan_item/
```

### Как работает:
- Автоматически создаёт новую продажу если её нет
- Добавляет товары в существующую незавершённую продажу
- Автоматически подставляет цену из товара

### Пример 1: Добавить первый товар

```bash
POST /api/sales/sales/scan_item/
Headers:
  Authorization: Bearer {token}
  X-Tenant-Key: admin_1a12e47a

Body:
{
  "session": 2,
  "product": 19,
  "quantity": 1
}
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Товар добавлен",
  "data": {
    "id": 3,
    "receipt_number": "CHECK-20251118055327",
    "status": "pending",
    "total_amount": "300000.00",
    "items": [
      {
        "id": 1,
        "product": 19,
        "product_name": "фывфцв",
        "quantity": "1.000",
        "unit_price": "300000.00",
        "line_total": "300000.00"
      }
    ],
    "payments": []
  }
}
```

### Пример 2: Добавить второй товар

```bash
POST /api/sales/sales/scan_item/
Body:
{
  "session": 2,
  "product": 18,
  "quantity": 2
}
```

**Товар добавится в ТУ ЖЕ продажу!**

### Пример 3: С количеством

```bash
POST /api/sales/sales/scan_item/
Body:
{
  "session": 2,
  "product": 19,
  "quantity": 2.5
}
```

### Frontend пример (React):

```typescript
import { scanItem } from '@/services/sales';

const handleAddProduct = async (productId: number, quantity: number = 1) => {
  try {
    const sale = await scanItem({
      session: currentSession.id,
      product: productId,
      quantity
    });

    setCurrentSale(sale);
    console.log('Товар добавлен:', sale);

  } catch (error) {
    console.error('Ошибка:', error);
  }
};

// Использование
handleAddProduct(19, 1); // Добавить товар с ID 19
```

---

## Способ 2: Полное создание продажи

### Endpoint:
```
POST /api/sales/sales/
```

### Обязательные поля:

```json
{
  "session": 2,
  "items": [
    {
      "product": 19,
      "quantity": 1,
      "price": 300000
    }
  ],
  "payments": [
    {
      "payment_method": "cash",
      "amount": 300000
    }
  ]
}
```

### Полный пример с опциями:

```bash
POST /api/sales/sales/
Headers:
  Authorization: Bearer {token}
  X-Tenant-Key: admin_1a12e47a
  Content-Type: application/json

Body:
{
  "session": 2,
  "status": "completed",
  "customer_name": "Иван Петров",
  "customer_phone": "+998901234567",
  "discount_percent": 10,
  "notes": "Постоянный клиент",
  "items": [
    {
      "product": 19,
      "quantity": 2,
      "price": 300000
    },
    {
      "product": 18,
      "quantity": 1,
      "price": 75000
    }
  ],
  "payments": [
    {
      "payment_method": "cash",
      "amount": 500000,
      "received_amount": 700000
    }
  ]
}
```

### С привязкой к существующему покупателю:

```json
{
  "session": 2,
  "customer_id": 5,
  "items": [
    {
      "product": 19,
      "quantity": 1,
      "price": 300000
    }
  ],
  "payments": [
    {
      "payment_method": "cash",
      "amount": 300000
    }
  ]
}
```

### С созданием нового покупателя:

```json
{
  "session": 2,
  "new_customer": {
    "first_name": "Алексей",
    "last_name": "Смирнов",
    "phone": "+998907654321",
    "email": "alex@example.com"
  },
  "items": [
    {
      "product": 19,
      "quantity": 1,
      "price": 300000
    }
  ],
  "payments": [
    {
      "payment_method": "card",
      "amount": 300000
    }
  ]
}
```

---

## Поля запроса

### Sale (основные):

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `session` | integer | ✅ Да | ID открытой смены |
| `receipt_number` | string | ❌ Нет | Номер чека (генерируется автоматически) |
| `status` | string | ❌ Нет | pending/completed (по умолчанию pending) |
| `customer_id` | integer | ❌ Нет | ID существующего покупателя |
| `new_customer` | object | ❌ Нет | Данные нового покупателя |
| `customer_name` | string | ❌ Нет | Имя покупателя (если не из базы) |
| `customer_phone` | string | ❌ Нет | Телефон покупателя |
| `discount_percent` | number | ❌ Нет | Процент скидки |
| `notes` | string | ❌ Нет | Примечания |
| `items` | array | ✅ Да | Позиции продажи |
| `payments` | array | ❌ Нет | Платежи |

### SaleItem (позиции):

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `product` | integer | ✅ Да | ID товара |
| `quantity` | number | ✅ Да | Количество |
| `price` | number | ✅ Да | Цена за единицу |
| `batch` | integer | ❌ Нет | ID партии товара |

### Payment (платежи):

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `payment_method` | string | ✅ Да | cash/card/transfer |
| `amount` | number | ✅ Да | Сумма платежа |
| `received_amount` | number | ❌ Нет | Получено (для наличных) |
| `card_number` | string | ❌ Нет | Последние 4 цифры карты |

---

## Frontend примеры

### TypeScript сервис:

```typescript
// services/sales.ts
import api from '@/utils/api';

export interface CreateSaleRequest {
  session: number;
  customer_id?: number;
  new_customer?: {
    first_name: string;
    last_name?: string;
    phone: string;
    email?: string;
  };
  customer_name?: string;
  customer_phone?: string;
  discount_percent?: number;
  notes?: string;
  items: Array<{
    product: number;
    quantity: number;
    price: number;
    batch?: number;
  }>;
  payments?: Array<{
    payment_method: 'cash' | 'card' | 'transfer';
    amount: number;
    received_amount?: number;
    card_number?: string;
  }>;
}

export const createSale = async (data: CreateSaleRequest) => {
  const response = await api.post('/sales/sales/', data);
  return response.data;
};

export const scanItem = async (data: {
  session: number;
  product: number;
  quantity?: number;
  batch?: number;
}) => {
  const response = await api.post('/sales/sales/scan_item/', data);
  return response.data.data;
};
```

### React компонент для создания продажи:

```typescript
import { useState } from 'react';
import { createSale } from '@/services/sales';

export const CreateSalePage = () => {
  const [items, setItems] = useState([]);
  const [payments, setPayments] = useState([]);
  const [sessionId, setSessionId] = useState(2);

  const handleAddItem = (product, quantity, price) => {
    setItems([...items, { product, quantity, price }]);
  };

  const handleAddPayment = (method, amount, receivedAmount) => {
    setPayments([
      ...payments,
      {
        payment_method: method,
        amount,
        received_amount: receivedAmount
      }
    ]);
  };

  const handleCreateSale = async () => {
    try {
      const sale = await createSale({
        session: sessionId,
        items,
        payments
      });

      alert(`Продажа ${sale.sale_number} создана!`);

      // Очистка
      setItems([]);
      setPayments([]);

    } catch (error) {
      console.error('Ошибка:', error);
      alert('Не удалось создать продажу');
    }
  };

  return (
    <div>
      <h1>Создать продажу</h1>

      {/* Добавление товаров */}
      <div>
        <button onClick={() => handleAddItem(19, 1, 300000)}>
          Добавить товар
        </button>
      </div>

      {/* Список товаров */}
      <table>
        <thead>
          <tr>
            <th>Товар</th>
            <th>Количество</th>
            <th>Цена</th>
            <th>Сумма</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <tr key={index}>
              <td>{item.product}</td>
              <td>{item.quantity}</td>
              <td>{item.price}</td>
              <td>{item.quantity * item.price}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Оплата */}
      <div>
        <button onClick={() => handleAddPayment('cash', 300000, 500000)}>
          Оплата наличными
        </button>
      </div>

      {/* Создать продажу */}
      <button
        onClick={handleCreateSale}
        disabled={items.length === 0}
      >
        Создать продажу
      </button>
    </div>
  );
};
```

### Простой пример использования:

```typescript
// Создание простой продажи
const sale = await createSale({
  session: 2,
  items: [
    { product: 19, quantity: 1, price: 300000 }
  ],
  payments: [
    { payment_method: 'cash', amount: 300000 }
  ]
});

console.log('Продажа создана:', sale);
```

### Использование scan_item:

```typescript
// Добавить первый товар
const sale1 = await scanItem({
  session: 2,
  product: 19,
  quantity: 1
});

// Добавить второй товар (в ту же продажу)
const sale2 = await scanItem({
  session: 2,
  product: 18,
  quantity: 2
});

console.log('Продажа с 2 товарами:', sale2);
```

---

## Полный workflow создания продажи

### Шаг 1: Открыть смену

```bash
POST /api/sales/sessions/open/
Body: { "opening_balance": 100000 }
```

### Шаг 2: Добавить товары через scan_item

```bash
# Товар 1
POST /api/sales/sales/scan_item/
Body: { "session": 2, "product": 19, "quantity": 1 }

# Товар 2
POST /api/sales/sales/scan_item/
Body: { "session": 2, "product": 18, "quantity": 2 }
```

### Шаг 3: Получить текущую продажу

```bash
GET /api/sales/sales/current/?session=2
```

### Шаг 4: Завершить продажу (добавить оплату)

**Вариант A: Обновить существующую продажу**
```bash
PATCH /api/sales/sales/{sale_id}/
Body: {
  "status": "completed",
  "payments": [
    {
      "payment_method": "cash",
      "amount": 450000,
      "received_amount": 500000
    }
  ]
}
```

**Вариант B: Создать сразу завершённую продажу**
```bash
POST /api/sales/sales/
Body: {
  "session": 2,
  "status": "completed",
  "items": [...],
  "payments": [...]
}
```

---

## Ошибки и их решения

### 1. "Укажите session и product"
```json
{
  "error": "Укажите session и product"
}
```
**Решение:** Добавьте обязательные поля `session` и `product`

### 2. "Смена не найдена или закрыта"
```json
{
  "error": "Смена не найдена или закрыта"
}
```
**Решение:** Откройте смену: `POST /api/sales/sessions/open/`

### 3. "Товар не найден"
```json
{
  "error": "Товар не найден"
}
```
**Решение:** Проверьте что товар существует и ID правильный

### 4. "Смена закрыта, невозможно создать продажу"
```json
{
  "session": ["Смена закрыта, невозможно создать продажу"]
}
```
**Решение:** Используйте открытую смену или откройте новую

---

## Резюме

### Для POS кассы (рекомендуется):
```
POST /api/sales/sales/scan_item/
```
- ✅ Автоматически создаёт продажу
- ✅ Автоматически подставляет цену
- ✅ Добавляет товары в текущую продажу
- ✅ Простой API

### Для создания полной продажи:
```
POST /api/sales/sales/
```
- ✅ Полный контроль над продажей
- ✅ Можно указать все параметры
- ✅ Можно создать сразу завершённую продажу
- ✅ Поддержка покупателей

### Параметры:
- **session** - ID открытой смены (обязательно)
- **product** - ID товара (для scan_item)
- **items** - Массив позиций (для создания продажи)
- **payments** - Массив платежей (опционально)

Готово! 🎉
