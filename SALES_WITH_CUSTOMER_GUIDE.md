# Продажи с привязкой к покупателю

## Возможности

✅ **Выбрать существующего покупателя** - указать ID покупателя при создании продажи
✅ **Создать нового покупателя** - создать покупателя прямо при оформлении продажи
✅ **Автоопределение** - если создаёте покупателя с существующим телефоном, система использует существующего
✅ **Автообновление статистики** - сумма покупок и бонусы автоматически пересчитываются
✅ **История покупок** - все продажи сохраняются в истории покупателя

---

## Основные сценарии

### 1. Продажа с выбором существующего покупателя

```bash
POST /api/services/sales/
Headers:
  Authorization: Bearer {token}
  X-Tenant-Key: {tenant_key}

Body:
{
  "session": 1,
  "customer_id": 5,
  "items": [
    {
      "product": 10,
      "quantity": 2,
      "price": 50000
    }
  ],
  "payments": [
    {
      "payment_method": "cash",
      "amount": 100000
    }
  ]
}
```

**Ответ:**
```json
{
  "id": 123,
  "sale_number": "SALE-2025-00123",
  "customer": 5,
  "customer_info": {
    "id": 5,
    "full_name": "Петров Иван",
    "phone": "+998901234567",
    "email": "ivan@example.com",
    "is_vip": false,
    "default_discount": 0
  },
  "customer_name": "Петров Иван",
  "customer_phone": "+998901234567",
  "subtotal": 100000.00,
  "total_amount": 100000.00,
  "status": "completed",
  "items": [...],
  "payments": [...]
}
```

### 2. Продажа с созданием нового покупателя

```bash
POST /api/services/sales/
Body:
{
  "session": 1,
  "new_customer": {
    "first_name": "Алексей",
    "last_name": "Смирнов",
    "phone": "+998907654321",
    "email": "alex@example.com"
  },
  "items": [
    {
      "product": 15,
      "quantity": 1,
      "price": 150000
    }
  ],
  "payments": [
    {
      "payment_method": "card",
      "amount": 150000
    }
  ]
}
```

**Результат:**
- Создаётся новый покупатель с указанными данными
- Продажа привязывается к этому покупателю
- Статистика покупателя обновляется автоматически

### 3. Продажа без привязки к покупателю (как раньше)

```bash
POST /api/services/sales/
Body:
{
  "session": 1,
  "customer_name": "Разовый покупатель",
  "customer_phone": "+998909999999",
  "items": [
    {
      "product": 20,
      "quantity": 3,
      "price": 25000
    }
  ],
  "payments": [
    {
      "payment_method": "cash",
      "amount": 75000
    }
  ]
}
```

**Важно:** Без `customer_id` или `new_customer` покупатель не сохраняется в базе!

---

## Поля нового покупателя

### Обязательные:
- `first_name` - Имя
- `phone` - Телефон (формат: `+998XXXXXXXXX`)

### Опциональные:
- `last_name` - Фамилия
- `email` - Email
- `customer_type` - Тип: `individual` (по умолчанию) или `company`
- `company_name` - Название компании (обязательно для `customer_type: "company"`)

### Пример для компании:

```json
{
  "session": 1,
  "new_customer": {
    "first_name": "Директор",
    "last_name": "Иванов",
    "phone": "+998901111111",
    "email": "director@company.uz",
    "customer_type": "company",
    "company_name": "ООО Рога и Копыта"
  },
  "items": [...]
}
```

---

## Автоопределение существующего покупателя

Если при создании нового покупателя (`new_customer`) указан телефон, который уже есть в базе:

```json
{
  "new_customer": {
    "first_name": "Другое имя",
    "phone": "+998901234567"  // ← этот телефон уже существует!
  }
}
```

**Система автоматически:**
1. Найдёт существующего покупателя по телефону
2. Использует его для продажи
3. **Не создаст дубликат**
4. Обновит статистику существующего покупателя

---

## Обновление статистики покупателя

При создании продажи с покупателем автоматически обновляется:

- `total_purchases` - общая сумма всех покупок
- `total_purchases_count` - количество покупок
- `last_purchase_at` - дата последней покупки
- `loyalty_points` - бонусные баллы (1% от суммы покупки)

**Пример:**
```json
// До продажи
{
  "total_purchases": 500000.00,
  "total_purchases_count": 10,
  "loyalty_points": 5000
}

// После продажи на 100000 сум
{
  "total_purchases": 600000.00,  // +100000
  "total_purchases_count": 11,    // +1
  "loyalty_points": 6000          // +1000 (1% от 100000)
}
```

---

## Frontend примеры (React + TypeScript)

### Сервис для работы с продажами

```typescript
// services/sales.ts
import api from '@/utils/api';

interface SaleItem {
  product: number;
  quantity: number;
  price: number;
}

interface Payment {
  payment_method: 'cash' | 'card' | 'transfer';
  amount: number;
}

interface NewCustomer {
  first_name: string;
  last_name?: string;
  phone: string;
  email?: string;
  customer_type?: 'individual' | 'company';
  company_name?: string;
}

interface CreateSaleData {
  session: number;
  customer_id?: number;
  new_customer?: NewCustomer;
  customer_name?: string;
  customer_phone?: string;
  discount_percent?: number;
  notes?: string;
  items: SaleItem[];
  payments: Payment[];
}

export const createSale = async (data: CreateSaleData) => {
  const response = await api.post('/services/sales/', data);
  return response.data;
};
```

### Компонент выбора/создания покупателя

```typescript
import { useState, useEffect } from 'react';
import { searchByPhone, createCustomer } from '@/services/customers';

interface CustomerSelectorProps {
  onSelectCustomer: (customerId: number | null) => void;
  onCreateCustomer: (customer: NewCustomer | null) => void;
}

export const CustomerSelector = ({
  onSelectCustomer,
  onCreateCustomer
}: CustomerSelectorProps) => {
  const [mode, setMode] = useState<'search' | 'create'>('search');
  const [phone, setPhone] = useState('+998');
  const [foundCustomer, setFoundCustomer] = useState(null);
  const [newCustomerData, setNewCustomerData] = useState({
    first_name: '',
    last_name: '',
    phone: '+998',
    email: ''
  });

  // Поиск по телефону
  const handleSearch = async () => {
    try {
      const customer = await searchByPhone(phone);
      setFoundCustomer(customer);
      onSelectCustomer(customer.id);
      onCreateCustomer(null);
    } catch (error) {
      setFoundCustomer(null);
      onSelectCustomer(null);
    }
  };

  // Переключение на создание нового
  const handleSwitchToCreate = () => {
    setMode('create');
    setNewCustomerData(prev => ({ ...prev, phone }));
    onSelectCustomer(null);
    onCreateCustomer({
      first_name: '',
      last_name: '',
      phone: phone,
      email: ''
    });
  };

  // Обновление данных нового покупателя
  const handleNewCustomerChange = (field: string, value: string) => {
    const updated = { ...newCustomerData, [field]: value };
    setNewCustomerData(updated);
    onCreateCustomer(updated);
  };

  return (
    <div className="customer-selector">
      <h3>Покупатель</h3>

      {/* Переключатель режима */}
      <div className="mode-toggle">
        <button
          onClick={() => setMode('search')}
          className={mode === 'search' ? 'active' : ''}
        >
          Найти существующего
        </button>
        <button
          onClick={() => setMode('create')}
          className={mode === 'create' ? 'active' : ''}
        >
          Создать нового
        </button>
      </div>

      {mode === 'search' ? (
        <div className="search-mode">
          <input
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+998901234567"
          />
          <button onClick={handleSearch}>Найти</button>

          {foundCustomer && (
            <div className="customer-info">
              <h4>{foundCustomer.full_name}</h4>
              <p>Телефон: {foundCustomer.phone}</p>
              <p>Покупок: {foundCustomer.total_purchases_count}</p>
              <p>На сумму: {foundCustomer.total_purchases.toLocaleString()} сум</p>
              {foundCustomer.is_vip && (
                <span className="vip-badge">VIP</span>
              )}
            </div>
          )}

          {!foundCustomer && phone.length > 4 && (
            <div className="not-found">
              <p>Покупатель не найден</p>
              <button onClick={handleSwitchToCreate}>
                Создать нового с этим телефоном
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="create-mode">
          <input
            type="text"
            placeholder="Имя *"
            value={newCustomerData.first_name}
            onChange={(e) => handleNewCustomerChange('first_name', e.target.value)}
            required
          />
          <input
            type="text"
            placeholder="Фамилия"
            value={newCustomerData.last_name}
            onChange={(e) => handleNewCustomerChange('last_name', e.target.value)}
          />
          <input
            type="tel"
            placeholder="Телефон *"
            value={newCustomerData.phone}
            onChange={(e) => handleNewCustomerChange('phone', e.target.value)}
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={newCustomerData.email}
            onChange={(e) => handleNewCustomerChange('email', e.target.value)}
          />
        </div>
      )}
    </div>
  );
};
```

### Компонент создания продажи

```typescript
import { useState } from 'react';
import { createSale } from '@/services/sales';
import { CustomerSelector } from './CustomerSelector';

export const CreateSalePage = () => {
  const [sessionId, setSessionId] = useState(1);
  const [customerId, setCustomerId] = useState<number | null>(null);
  const [newCustomer, setNewCustomer] = useState<NewCustomer | null>(null);
  const [items, setItems] = useState<SaleItem[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);

  const handleCreateSale = async () => {
    try {
      const saleData: CreateSaleData = {
        session: sessionId,
        items,
        payments
      };

      // Добавляем покупателя если выбран
      if (customerId) {
        saleData.customer_id = customerId;
      } else if (newCustomer && newCustomer.first_name && newCustomer.phone) {
        saleData.new_customer = newCustomer;
      }

      const sale = await createSale(saleData);

      console.log('Продажа создана:', sale);
      alert(`Продажа ${sale.sale_number} успешно создана!`);

      // Сброс формы
      setCustomerId(null);
      setNewCustomer(null);
      setItems([]);
      setPayments([]);

    } catch (error) {
      console.error('Ошибка при создании продажи:', error);
      alert('Ошибка при создании продажи');
    }
  };

  return (
    <div className="create-sale-page">
      <h1>Создать продажу</h1>

      {/* Выбор/создание покупателя */}
      <CustomerSelector
        onSelectCustomer={setCustomerId}
        onCreateCustomer={setNewCustomer}
      />

      {/* Товары */}
      <div className="items-section">
        <h3>Товары</h3>
        {/* ... форма добавления товаров ... */}
      </div>

      {/* Оплата */}
      <div className="payments-section">
        <h3>Оплата</h3>
        {/* ... форма добавления платежей ... */}
      </div>

      {/* Кнопка создания */}
      <button
        onClick={handleCreateSale}
        disabled={items.length === 0 || payments.length === 0}
      >
        Создать продажу
      </button>
    </div>
  );
};
```

### Простой пример использования

```typescript
// Продажа с существующим покупателем
const sale1 = await createSale({
  session: 1,
  customer_id: 5,
  items: [
    { product: 10, quantity: 2, price: 50000 }
  ],
  payments: [
    { payment_method: 'cash', amount: 100000 }
  ]
});

// Продажа с новым покупателем
const sale2 = await createSale({
  session: 1,
  new_customer: {
    first_name: 'Иван',
    last_name: 'Петров',
    phone: '+998901234567',
    email: 'ivan@example.com'
  },
  items: [
    { product: 15, quantity: 1, price: 150000 }
  ],
  payments: [
    { payment_method: 'card', amount: 150000 }
  ]
});

// Продажа без покупателя (разовая)
const sale3 = await createSale({
  session: 1,
  customer_name: 'Разовый покупатель',
  customer_phone: '+998909999999',
  items: [
    { product: 20, quantity: 3, price: 25000 }
  ],
  payments: [
    { payment_method: 'cash', amount: 75000 }
  ]
});
```

---

## Просмотр истории покупок

После создания продажи с покупателем, она появится в его истории:

```bash
GET /api/customers/customers/5/purchase-history/
```

**Ответ:**
```json
{
  "count": 15,
  "results": [
    {
      "id": 123,
      "sale_number": "SALE-2025-00123",
      "created_at": "2025-11-17T20:00:00+05:00",
      "total_amount": 100000.00,
      "status": "completed",
      "items": [
        {
          "product_name": "Молоко 3.2%",
          "quantity": 2,
          "price": 50000.00,
          "total": 100000.00
        }
      ]
    }
  ]
}
```

---

## Ошибки

### 400 Bad Request - Покупатель не найден

```json
{
  "customer_id": ["Покупатель с таким ID не найден"]
}
```

**Решение:** Проверьте, что покупатель существует и активен (`is_active=true`)

### 400 Bad Request - Неверный формат телефона

```json
{
  "new_customer": {
    "phone": ["Введите правильное значение."]
  }
}
```

**Решение:** Используйте формат `+998XXXXXXXXX`

### 400 Bad Request - Не указано название компании

```json
{
  "new_customer": {
    "company_name": ["Для юридического лица обязательно укажите название компании"]
  }
}
```

**Решение:** Для `customer_type: "company"` обязательно укажите `company_name`

---

## Резюме

### Способы привязки покупателя к продаже:

| Способ | Поле | Описание |
|--------|------|----------|
| Существующий | `customer_id` | ID покупателя из базы |
| Новый | `new_customer` | Создать покупателя при продаже |
| Разовый | `customer_name` + `customer_phone` | Не сохраняется в базе |

### Обязательные поля для нового покупателя:
- `first_name`
- `phone` (формат: `+998XXXXXXXXX`)

### Автоматические действия:
- ✅ Обновление статистики покупателя
- ✅ Начисление бонусных баллов
- ✅ Сохранение в истории покупок
- ✅ Автоопределение существующего по телефону

### Endpoints:
- `POST /api/services/sales/` - Создать продажу
- `GET /api/customers/customers/{id}/purchase-history/` - История покупок
- `GET /api/customers/customers/{id}/stats/` - Статистика покупателя

Готово! 🎉
