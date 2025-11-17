# API для управления покупателями (клиентами)

## Содержание
- [Модели данных](#модели-данных)
- [Создание покупателя](#создание-покупателя)
- [Обновление покупателя](#обновление-покупателя)
- [Получение списка покупателей](#получение-списка-покупателей)
- [Поиск покупателя](#поиск-покупателя)
- [Работа с балансом](#работа-с-балансом)
- [Группы покупателей](#группы-покупателей)
- [История транзакций](#история-транзакций)
- [Frontend примеры](#frontend-примеры)

---

## Модели данных

### Customer (Покупатель)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer | ID покупателя (read-only) |
| `first_name` | string | Имя (обязательно) |
| `last_name` | string | Фамилия |
| `middle_name` | string | Отчество |
| `full_name` | string | Полное имя (read-only) |
| `customer_type` | string | Тип: `individual` или `company` |
| `company_name` | string | Название компании (обязательно для `company`) |
| `tax_id` | string | ИНН |
| `phone` | string | Телефон (обязательно, уникальный) |
| `phone_2` | string | Дополнительный телефон |
| `email` | string | Email |
| `address` | string | Адрес |
| `city` | string | Город |
| `region` | string | Регион |
| `postal_code` | string | Почтовый индекс |
| `group` | integer | ID группы покупателей |
| `balance` | decimal | Баланс (read-only) |
| `credit_limit` | decimal | Кредитный лимит |
| `available_credit` | decimal | Доступный кредит (read-only) |
| `loyalty_points` | integer | Бонусные баллы (read-only) |
| `total_purchases` | decimal | Сумма всех покупок (read-only) |
| `total_purchases_count` | integer | Количество покупок (read-only) |
| `default_discount` | decimal | Скидка по умолчанию (read-only) |
| `is_vip` | boolean | VIP статус (read-only) |
| `birthday` | date | День рождения |
| `notes` | string | Заметки |
| `is_active` | boolean | Активен |
| `is_blocked` | boolean | Заблокирован |
| `created_at` | datetime | Дата создания (read-only) |
| `updated_at` | datetime | Дата обновления (read-only) |
| `last_purchase_at` | datetime | Последняя покупка (read-only) |

### CustomerGroup (Группа покупателей)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer | ID группы |
| `name` | string | Название группы |
| `description` | string | Описание |
| `discount_percent` | decimal | Процент скидки (0-100) |
| `min_purchase_amount` | decimal | Минимальная сумма покупки |
| `is_active` | boolean | Активна |
| `members_count` | integer | Количество участников (read-only) |

---

## Создание покупателя

### Эндпоинт
```
POST /api/customers/customers/
```

### Обязательные заголовки
```
Authorization: Bearer {access_token}
X-Tenant-Key: {tenant_key}
Content-Type: application/json
```

### Создать физическое лицо

**Запрос:**
```json
POST /api/customers/customers/
{
  "first_name": "Иван",
  "last_name": "Петров",
  "middle_name": "Сергеевич",
  "customer_type": "individual",
  "phone": "+998901234567",
  "phone_2": "+998909876543",
  "email": "ivan@example.com",
  "address": "ул. Пушкина, д. 10",
  "city": "Ташкент",
  "birthday": "1990-05-15",
  "credit_limit": 1000000,
  "notes": "Постоянный клиент"
}
```

**Успешный ответ (201 Created):**
```json
{
  "id": 1,
  "first_name": "Иван",
  "last_name": "Петров",
  "middle_name": "Сергеевич",
  "full_name": "Петров Иван Сергеевич",
  "customer_type": "individual",
  "customer_type_display": "Физическое лицо",
  "company_name": "",
  "tax_id": "",
  "phone": "+998901234567",
  "phone_2": "+998909876543",
  "email": "ivan@example.com",
  "address": "ул. Пушкина, д. 10",
  "city": "Ташкент",
  "region": "",
  "postal_code": "",
  "group": null,
  "group_name": null,
  "balance": 0.00,
  "credit_limit": 1000000.00,
  "available_credit": 1000000.00,
  "loyalty_points": 0,
  "total_purchases": 0.00,
  "total_purchases_count": 0,
  "default_discount": 0.00,
  "is_vip": false,
  "birthday": "1990-05-15",
  "notes": "Постоянный клиент",
  "is_active": true,
  "is_blocked": false,
  "created_at": "2025-11-17T20:00:00+05:00",
  "updated_at": "2025-11-17T20:00:00+05:00",
  "last_purchase_at": null
}
```

### Создать юридическое лицо

**Запрос:**
```json
POST /api/customers/customers/
{
  "first_name": "Контактное лицо",
  "last_name": "Компании",
  "customer_type": "company",
  "company_name": "ООО \"Рога и Копыта\"",
  "tax_id": "123456789",
  "phone": "+998901111111",
  "email": "info@company.uz",
  "address": "ул. Ленина, д. 50",
  "city": "Ташкент",
  "credit_limit": 5000000
}
```

**Важно:** Для `customer_type: "company"` поле `company_name` обязательно!

### Ошибки

#### 400 Bad Request - Телефон уже существует
```json
{
  "phone": ["Покупатель с таким номером телефона уже существует"]
}
```

#### 400 Bad Request - Неверный формат телефона
```json
{
  "phone": ["Введите правильное значение."]
}
```

Формат телефона: `+998XXXXXXXXX` (должен начинаться с +998 и содержать 9 цифр)

#### 400 Bad Request - Не указано название компании
```json
{
  "company_name": ["Для юридического лица обязательно укажите название компании"]
}
```

---

## Обновление покупателя

### Полное обновление (PUT)
```
PUT /api/customers/customers/{id}/
```

### Частичное обновление (PATCH)
```
PATCH /api/customers/customers/{id}/
```

**Запрос:**
```json
PATCH /api/customers/customers/1/
{
  "phone_2": "+998905555555",
  "email": "newemail@example.com",
  "credit_limit": 2000000,
  "notes": "Увеличен кредитный лимит"
}
```

**Ответ:**
```json
{
  "id": 1,
  "first_name": "Иван",
  "last_name": "Петров",
  "phone": "+998901234567",
  "phone_2": "+998905555555",
  "email": "newemail@example.com",
  "credit_limit": 2000000.00,
  "notes": "Увеличен кредитный лимит",
  ...
}
```

### Заблокировать покупателя

```json
PATCH /api/customers/customers/1/
{
  "is_blocked": true
}
```

### Деактивировать покупателя

```json
PATCH /api/customers/customers/1/
{
  "is_active": false
}
```

---

## Получение списка покупателей

### Все покупатели
```
GET /api/customers/customers/
```

**Ответ:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/customers/customers/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "first_name": "Иван",
      "last_name": "Петров",
      "full_name": "Петров Иван Сергеевич",
      "phone": "+998901234567",
      "email": "ivan@example.com",
      "balance": 150000.00,
      "total_purchases": 5000000.00,
      "loyalty_points": 500,
      "is_vip": true,
      ...
    },
    ...
  ]
}
```

### Фильтрация

#### По группе
```
GET /api/customers/customers/?group=1
```

#### По типу клиента
```
GET /api/customers/customers/?customer_type=company
```

#### Только активные
```
GET /api/customers/customers/?is_active=true
```

#### Только заблокированные
```
GET /api/customers/customers/?is_blocked=true
```

### Поиск

Поиск по имени, фамилии, телефону, email, названию компании:

```
GET /api/customers/customers/?search=Иван
GET /api/customers/customers/?search=+998901234567
GET /api/customers/customers/?search=ivan@example.com
```

### Сортировка

```
GET /api/customers/customers/?ordering=-total_purchases
GET /api/customers/customers/?ordering=-last_purchase_at
GET /api/customers/customers/?ordering=loyalty_points
```

Доступные поля для сортировки:
- `created_at` - по дате создания
- `last_purchase_at` - по последней покупке
- `total_purchases` - по сумме покупок
- `loyalty_points` - по бонусным баллам

Добавьте `-` для обратной сортировки.

---

## Поиск покупателя

### Получить одного покупателя
```
GET /api/customers/customers/{id}/
```

**Ответ:**
```json
{
  "id": 1,
  "first_name": "Иван",
  "last_name": "Петров",
  "full_name": "Петров Иван Сергеевич",
  "phone": "+998901234567",
  "balance": 150000.00,
  "transactions": [...],
  "recent_transactions": [
    {
      "id": 10,
      "transaction_type": "payment",
      "transaction_type_display": "Платёж",
      "amount": 100000.00,
      "balance_before": 50000.00,
      "balance_after": 150000.00,
      "created_at": "2025-11-17T19:00:00+05:00"
    },
    ...
  ],
  ...
}
```

### Быстрый поиск по телефону
```
GET /api/customers/customers/search_by_phone/?phone=+998901234567
```

**Успешный ответ:**
```json
{
  "id": 1,
  "first_name": "Иван",
  "full_name": "Петров Иван Сергеевич",
  "phone": "+998901234567",
  "balance": 150000.00,
  "credit_limit": 1000000.00,
  "available_credit": 1000000.00,
  "default_discount": 5.00,
  ...
}
```

**Ошибка (404 Not Found):**
```json
{
  "error": "Покупатель не найден"
}
```

### VIP покупатели
```
GET /api/customers/customers/vip_customers/
```

Возвращает покупателей со скидкой >= 10%

### Должники
```
GET /api/customers/customers/debtors/
```

Возвращает покупателей с отрицательным балансом (sorted by balance).

---

## Работа с балансом

### Добавить платёж
```
POST /api/customers/customers/{id}/add_payment/
```

**Запрос:**
```json
{
  "amount": 100000.00,
  "description": "Пополнение баланса"
}
```

**Ответ:**
```json
{
  "message": "Платёж успешно добавлен",
  "transaction": {
    "id": 15,
    "customer": 1,
    "customer_name": "Петров Иван Сергеевич",
    "transaction_type": "payment",
    "transaction_type_display": "Платёж",
    "amount": 100000.00,
    "balance_before": 50000.00,
    "balance_after": 150000.00,
    "description": "Пополнение баланса",
    "created_at": "2025-11-17T20:30:00+05:00"
  },
  "new_balance": 150000.00
}
```

### Списать с баланса
```
POST /api/customers/customers/{id}/charge/
```

**Запрос:**
```json
{
  "amount": 50000.00,
  "description": "Оплата за товар"
}
```

**Ответ:**
```json
{
  "message": "Списание выполнено успешно",
  "transaction": {
    "id": 16,
    "transaction_type": "charge",
    "transaction_type_display": "Списание",
    "amount": 50000.00,
    "balance_before": 150000.00,
    "balance_after": 100000.00,
    ...
  },
  "new_balance": 100000.00
}
```

**Ошибка - недостаточно средств:**
```json
{
  "error": "Недостаточно средств. Доступно: 150000.00"
}
```

---

## История транзакций

### Получить историю транзакций покупателя
```
GET /api/customers/customers/{id}/transactions_history/
```

**Ответ:**
```json
{
  "count": 25,
  "results": [
    {
      "id": 16,
      "customer": 1,
      "customer_name": "Петров Иван Сергеевич",
      "transaction_type": "charge",
      "transaction_type_display": "Списание",
      "amount": 50000.00,
      "balance_before": 150000.00,
      "balance_after": 100000.00,
      "sale": 123,
      "description": "Оплата за товар",
      "performed_by": "admin",
      "created_at": "2025-11-17T20:35:00+05:00"
    },
    ...
  ]
}
```

### Фильтрация по типу транзакции
```
GET /api/customers/customers/{id}/transactions_history/?type=payment
GET /api/customers/customers/{id}/transactions_history/?type=charge
```

Типы транзакций:
- `payment` - Платёж
- `charge` - Списание
- `bonus_accrual` - Начисление бонусов
- `bonus_redemption` - Списание бонусов
- `correction` - Корректировка

### Фильтрация по датам
```
GET /api/customers/customers/{id}/transactions_history/?date_from=2025-11-01&date_to=2025-11-30
```

---

## Статистика по покупателю

```
GET /api/customers/customers/{id}/stats/
```

**Ответ:**
```json
{
  "customer": {
    "id": 1,
    "full_name": "Петров Иван Сергеевич",
    "phone": "+998901234567",
    ...
  },
  "transactions": {
    "total_count": 25,
    "total_payments": 500000.00,
    "total_charges": 350000.00
  },
  "financial": {
    "current_balance": 150000.00,
    "credit_limit": 1000000.00,
    "available_credit": 1000000.00,
    "loyalty_points": 500
  },
  "purchases": {
    "total_amount": 5000000.00,
    "total_count": 50,
    "last_purchase": "2025-11-17T18:00:00+05:00"
  }
}
```

---

## Группы покупателей

### Создать группу
```
POST /api/customers/groups/
```

**Запрос:**
```json
{
  "name": "VIP клиенты",
  "description": "Покупатели с большим объемом покупок",
  "discount_percent": 15.00,
  "min_purchase_amount": 1000000.00,
  "is_active": true
}
```

### Получить список групп
```
GET /api/customers/groups/
```

### Обновить группу
```
PATCH /api/customers/groups/{id}/
{
  "discount_percent": 20.00
}
```

### Получить членов группы
```
GET /api/customers/groups/{id}/members/
```

---

## Frontend примеры

### React + TypeScript

#### Создание покупателя

```typescript
// services/customers.ts
import api from '@/utils/api';

export interface CreateCustomerData {
  first_name: string;
  last_name?: string;
  middle_name?: string;
  customer_type: 'individual' | 'company';
  company_name?: string;
  tax_id?: string;
  phone: string;
  phone_2?: string;
  email?: string;
  address?: string;
  city?: string;
  region?: string;
  postal_code?: string;
  group?: number;
  credit_limit?: number;
  birthday?: string;
  notes?: string;
}

export const createCustomer = async (data: CreateCustomerData) => {
  const response = await api.post('/customers/customers/', data);
  return response.data;
};

export const updateCustomer = async (id: number, data: Partial<CreateCustomerData>) => {
  const response = await api.patch(`/customers/customers/${id}/`, data);
  return response.data;
};

export const getCustomers = async (params?: {
  search?: string;
  group?: number;
  customer_type?: 'individual' | 'company';
  is_active?: boolean;
  ordering?: string;
  page?: number;
}) => {
  const response = await api.get('/customers/customers/', { params });
  return response.data;
};

export const getCustomerById = async (id: number) => {
  const response = await api.get(`/customers/customers/${id}/`);
  return response.data;
};

export const searchCustomerByPhone = async (phone: string) => {
  const response = await api.get('/customers/customers/search_by_phone/', {
    params: { phone }
  });
  return response.data;
};

export const addPayment = async (customerId: number, amount: number, description?: string) => {
  const response = await api.post(`/customers/customers/${customerId}/add_payment/`, {
    amount,
    description
  });
  return response.data;
};

export const chargeBalance = async (customerId: number, amount: number, description?: string) => {
  const response = await api.post(`/customers/customers/${customerId}/charge/`, {
    amount,
    description
  });
  return response.data;
};
```

#### Компонент формы создания покупателя

```typescript
// components/CustomerForm.tsx
import { useState } from 'react';
import { createCustomer, CreateCustomerData } from '@/services/customers';

export const CustomerForm = ({ onSuccess }: { onSuccess?: () => void }) => {
  const [formData, setFormData] = useState<CreateCustomerData>({
    first_name: '',
    last_name: '',
    middle_name: '',
    customer_type: 'individual',
    phone: '+998',
    email: '',
    address: '',
    city: '',
    credit_limit: 0,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await createCustomer(formData);
      alert('Покупатель успешно создан!');
      if (onSuccess) onSuccess();
    } catch (err: any) {
      console.error('Ошибка создания покупателя:', err);
      setError(err.response?.data?.phone?.[0] || 'Ошибка создания покупателя');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Тип клиента:</label>
        <select
          value={formData.customer_type}
          onChange={(e) => setFormData({
            ...formData,
            customer_type: e.target.value as 'individual' | 'company'
          })}
        >
          <option value="individual">Физическое лицо</option>
          <option value="company">Юридическое лицо</option>
        </select>
      </div>

      {formData.customer_type === 'company' && (
        <div>
          <label>Название компании: *</label>
          <input
            type="text"
            value={formData.company_name || ''}
            onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
            required
          />
        </div>
      )}

      <div>
        <label>Имя: *</label>
        <input
          type="text"
          value={formData.first_name}
          onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
          required
        />
      </div>

      <div>
        <label>Фамилия:</label>
        <input
          type="text"
          value={formData.last_name}
          onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
        />
      </div>

      <div>
        <label>Телефон: *</label>
        <input
          type="tel"
          value={formData.phone}
          onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
          placeholder="+998901234567"
          required
        />
        <small>Формат: +998XXXXXXXXX</small>
      </div>

      <div>
        <label>Email:</label>
        <input
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        />
      </div>

      <div>
        <label>Кредитный лимит:</label>
        <input
          type="number"
          value={formData.credit_limit}
          onChange={(e) => setFormData({
            ...formData,
            credit_limit: parseFloat(e.target.value) || 0
          })}
        />
      </div>

      {error && <div style={{ color: 'red' }}>{error}</div>}

      <button type="submit" disabled={loading}>
        {loading ? 'Создание...' : 'Создать покупателя'}
      </button>
    </form>
  );
};
```

#### Компонент поиска по телефону

```typescript
// components/CustomerSearch.tsx
import { useState } from 'react';
import { searchCustomerByPhone } from '@/services/customers';

export const CustomerSearch = () => {
  const [phone, setPhone] = useState('+998');
  const [customer, setCustomer] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (phone.length < 13) {
      setError('Введите полный номер телефона');
      return;
    }

    setLoading(true);
    setError('');
    setCustomer(null);

    try {
      const result = await searchCustomerByPhone(phone);
      setCustomer(result);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Покупатель не найден');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h3>Поиск покупателя</h3>

      <div style={{ display: 'flex', gap: '10px' }}>
        <input
          type="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="+998901234567"
          style={{ flex: 1 }}
        />
        <button onClick={handleSearch} disabled={loading}>
          {loading ? 'Поиск...' : 'Найти'}
        </button>
      </div>

      {error && <div style={{ color: 'red', marginTop: '10px' }}>{error}</div>}

      {customer && (
        <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ccc' }}>
          <h4>{customer.full_name}</h4>
          <p><strong>Телефон:</strong> {customer.phone}</p>
          <p><strong>Email:</strong> {customer.email}</p>
          <p><strong>Баланс:</strong> {customer.balance.toLocaleString()} сум</p>
          <p><strong>Кредитный лимит:</strong> {customer.credit_limit.toLocaleString()} сум</p>
          <p><strong>Доступно:</strong> {customer.available_credit.toLocaleString()} сум</p>
          {customer.default_discount > 0 && (
            <p><strong>Скидка:</strong> {customer.default_discount}%</p>
          )}
          {customer.is_vip && <span style={{ color: 'gold' }}>⭐ VIP</span>}
        </div>
      )}
    </div>
  );
};
```

#### Работа с балансом

```typescript
// components/CustomerBalance.tsx
import { useState } from 'react';
import { addPayment, chargeBalance } from '@/services/customers';

export const CustomerBalance = ({
  customerId,
  currentBalance,
  onUpdate
}: {
  customerId: number;
  currentBalance: number;
  onUpdate?: () => void;
}) => {
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);

  const handlePayment = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      alert('Введите сумму');
      return;
    }

    setLoading(true);
    try {
      const result = await addPayment(
        customerId,
        parseFloat(amount),
        description
      );

      alert(`Платёж добавлен! Новый баланс: ${result.new_balance}`);
      setAmount('');
      setDescription('');
      if (onUpdate) onUpdate();
    } catch (error) {
      console.error('Ошибка:', error);
      alert('Ошибка добавления платежа');
    } finally {
      setLoading(false);
    }
  };

  const handleCharge = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      alert('Введите сумму');
      return;
    }

    setLoading(true);
    try {
      const result = await chargeBalance(
        customerId,
        parseFloat(amount),
        description
      );

      alert(`Списание выполнено! Новый баланс: ${result.new_balance}`);
      setAmount('');
      setDescription('');
      if (onUpdate) onUpdate();
    } catch (error: any) {
      console.error('Ошибка:', error);
      alert(error.response?.data?.error || 'Ошибка списания');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h3>Текущий баланс: {currentBalance.toLocaleString()} сум</h3>

      <div style={{ marginTop: '20px' }}>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="Сумма"
          style={{ marginRight: '10px' }}
        />

        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Описание (необязательно)"
          style={{ marginRight: '10px' }}
        />

        <button onClick={handlePayment} disabled={loading}>
          Пополнить
        </button>

        <button onClick={handleCharge} disabled={loading} style={{ marginLeft: '10px' }}>
          Списать
        </button>
      </div>
    </div>
  );
};
```

---

## Postman примеры

### 1. Создать покупателя (физлицо)
```
POST http://localhost:8000/api/customers/customers/
Headers:
  Authorization: Bearer {{access_token}}
  X-Tenant-Key: {{tenant_key}}
  Content-Type: application/json

Body:
{
  "first_name": "Иван",
  "last_name": "Петров",
  "phone": "+998901234567",
  "email": "ivan@example.com",
  "credit_limit": 1000000
}
```

### 2. Поиск по телефону
```
GET http://localhost:8000/api/customers/customers/search_by_phone/?phone=+998901234567
Headers:
  Authorization: Bearer {{access_token}}
  X-Tenant-Key: {{tenant_key}}
```

### 3. Добавить платёж
```
POST http://localhost:8000/api/customers/customers/1/add_payment/
Headers:
  Authorization: Bearer {{access_token}}
  X-Tenant-Key: {{tenant_key}}
  Content-Type: application/json

Body:
{
  "amount": 100000,
  "description": "Пополнение баланса"
}
```

### 4. Получить VIP клиентов
```
GET http://localhost:8000/api/customers/customers/vip_customers/
Headers:
  Authorization: Bearer {{access_token}}
  X-Tenant-Key: {{tenant_key}}
```

---

## Резюме

### Основные endpoints:

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/api/customers/customers/` | Создать покупателя |
| `GET` | `/api/customers/customers/` | Список покупателей |
| `GET` | `/api/customers/customers/{id}/` | Один покупатель |
| `PATCH` | `/api/customers/customers/{id}/` | Обновить покупателя |
| `GET` | `/api/customers/customers/search_by_phone/` | Поиск по телефону |
| `POST` | `/api/customers/customers/{id}/add_payment/` | Пополнить баланс |
| `POST` | `/api/customers/customers/{id}/charge/` | Списать с баланса |
| `GET` | `/api/customers/customers/{id}/transactions_history/` | История транзакций |
| `GET` | `/api/customers/customers/{id}/stats/` | Статистика |
| `GET` | `/api/customers/customers/vip_customers/` | VIP клиенты |
| `GET` | `/api/customers/customers/debtors/` | Должники |

### Обязательные заголовки:
```
Authorization: Bearer {access_token}
X-Tenant-Key: {tenant_key}
```

### Формат телефона:
```
+998XXXXXXXXX
```

Готово! 🎉
