# API для управления покупателями

## Что можно делать

✅ **Создавать покупателей** - добавлять новых клиентов (физлица и компании)
✅ **Обновлять данные** - изменять информацию о клиенте
✅ **Просматривать** - получать списки и искать клиентов
✅ **История покупок** - смотреть что покупал клиент и когда
✅ **Статистика** - сумма покупок, количество, бонусные баллы

❌ **Нет работы с балансом** - пополнение/списание баланса не используется

---

## Основные операции

### 1. Создать покупателя (физлицо)

```bash
POST /api/customers/customers/
Headers:
  Authorization: Bearer {token}
  X-Tenant-Key: {tenant_key}

Body:
{
  "first_name": "Иван",
  "last_name": "Петров",
  "phone": "+998901234567",
  "email": "ivan@example.com"
}
```

**Ответ:**
```json
{
  "id": 1,
  "first_name": "Иван",
  "last_name": "Петров",
  "full_name": "Петров Иван",
  "phone": "+998901234567",
  "email": "ivan@example.com",
  "customer_type": "individual",
  "is_active": true,
  "created_at": "2025-11-17T20:00:00+05:00"
}
```

### 2. Создать покупателя (компания)

```bash
POST /api/customers/customers/
Body:
{
  "first_name": "Контактное",
  "last_name": "Лицо",
  "customer_type": "company",
  "company_name": "ООО Рога и Копыта",
  "tax_id": "123456789",
  "phone": "+998901111111",
  "email": "info@company.uz"
}
```

**Важно:** Для `customer_type: "company"` поле `company_name` обязательно!

### 3. Обновить покупателя

```bash
PATCH /api/customers/customers/1/
Body:
{
  "email": "newemail@example.com",
  "notes": "VIP клиент"
}
```

### 4. Получить список покупателей

```bash
# Все покупатели
GET /api/customers/customers/

# Поиск по имени/телефону/email
GET /api/customers/customers/?search=Иван
GET /api/customers/customers/?search=+998901234567

# Только компании
GET /api/customers/customers/?customer_type=company

# Только физлица
GET /api/customers/customers/?customer_type=individual

# Только активные
GET /api/customers/customers/?is_active=true
```

### 5. Поиск по телефону

```bash
GET /api/customers/customers/search_by_phone/?phone=+998901234567
```

**Успешный ответ:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "full_name": "Петров Иван",
    "phone": "+998901234567",
    "email": "ivan@example.com",
    "total_purchases": 500000.00,
    "total_purchases_count": 15,
    "loyalty_points": 5000
  }
}
```

### 6. История покупок

```bash
# Вся история
GET /api/customers/customers/1/purchase-history/

# За период
GET /api/customers/customers/1/purchase-history/?date_from=2025-11-01&date_to=2025-11-30
```

**Ответ:**
```json
{
  "count": 15,
  "results": [
    {
      "id": 123,
      "sale_number": "SALE-2025-00123",
      "created_at": "2025-11-17T18:30:00+05:00",
      "total_amount": 150000.00,
      "items": [
        {
          "product_name": "Молоко 3.2%",
          "quantity": 5,
          "price": 12000.00,
          "total": 60000.00
        },
        {
          "product_name": "Хлеб белый",
          "quantity": 10,
          "price": 9000.00,
          "total": 90000.00
        }
      ]
    }
  ]
}
```

### 7. Статистика по покупателю

```bash
GET /api/customers/customers/1/stats/
```

**Ответ:**
```json
{
  "customer": {
    "id": 1,
    "full_name": "Петров Иван",
    "phone": "+998901234567"
  },
  "purchases": {
    "total_amount": 5000000.00,
    "total_count": 50,
    "last_purchase": "2025-11-17T18:30:00+05:00",
    "loyalty_points": 50000
  }
}
```

### 8. VIP покупатели

```bash
GET /api/customers/customers/vip_customers/
```

Возвращает покупателей со скидкой >= 10%

---

## Поля покупателя

### Обязательные поля:
- `first_name` - Имя
- `phone` - Телефон (формат: `+998XXXXXXXXX`)

### Для компаний дополнительно:
- `company_name` - Название компании (обязательно)

### Опциональные поля:
- `last_name` - Фамилия
- `middle_name` - Отчество
- `customer_type` - Тип: `individual` (по умолчанию) или `company`
- `tax_id` - ИНН
- `phone_2` - Дополнительный телефон
- `email` - Email
- `address` - Адрес
- `city` - Город
- `region` - Регион
- `postal_code` - Индекс
- `group` - ID группы покупателей
- `birthday` - День рождения (YYYY-MM-DD)
- `notes` - Заметки
- `is_active` - Активен (по умолчанию `true`)
- `is_blocked` - Заблокирован (по умолчанию `false`)

### Read-only поля (автоматически):
- `id` - ID покупателя
- `full_name` - Полное имя
- `total_purchases` - Общая сумма покупок
- `total_purchases_count` - Количество покупок
- `loyalty_points` - Бонусные баллы
- `created_at` - Дата создания
- `updated_at` - Дата обновления
- `last_purchase_at` - Последняя покупка

---

## Группы покупателей

### Создать группу

```bash
POST /api/customers/groups/
Body:
{
  "name": "VIP клиенты",
  "description": "Покупатели с большим объемом покупок",
  "discount_percent": 15.00,
  "is_active": true
}
```

### Получить список групп

```bash
GET /api/customers/groups/
```

### Обновить группу

```bash
PATCH /api/customers/groups/1/
Body:
{
  "discount_percent": 20.00
}
```

### Получить членов группы

```bash
GET /api/customers/groups/1/members/
```

---

## Frontend примеры (React + TypeScript)

### Создание покупателя

```typescript
// services/customers.ts
import api from '@/utils/api';

export const createCustomer = async (data: {
  first_name: string;
  last_name?: string;
  phone: string;
  email?: string;
  customer_type?: 'individual' | 'company';
  company_name?: string;
}) => {
  const response = await api.post('/customers/customers/', data);
  return response.data;
};

// Использование
const customer = await createCustomer({
  first_name: 'Иван',
  last_name: 'Петров',
  phone: '+998901234567',
  email: 'ivan@example.com'
});
```

### Поиск по телефону

```typescript
export const searchByPhone = async (phone: string) => {
  const response = await api.get('/customers/customers/search_by_phone/', {
    params: { phone }
  });
  return response.data.data;
};

// Использование
try {
  const customer = await searchByPhone('+998901234567');
  console.log('Найден:', customer.full_name);
} catch (error) {
  console.log('Покупатель не найден');
}
```

### История покупок

```typescript
export const getPurchaseHistory = async (
  customerId: number,
  dateFrom?: string,
  dateTo?: string
) => {
  const response = await api.get(
    `/customers/customers/${customerId}/purchase-history/`,
    {
      params: {
        date_from: dateFrom,
        date_to: dateTo
      }
    }
  );
  return response.data;
};

// Использование
const history = await getPurchaseHistory(1, '2025-11-01', '2025-11-30');
```

### Компонент поиска

```typescript
import { useState } from 'react';
import { searchByPhone } from '@/services/customers';

export const CustomerSearch = () => {
  const [phone, setPhone] = useState('+998');
  const [customer, setCustomer] = useState(null);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    try {
      const result = await searchByPhone(phone);
      setCustomer(result);
      setError('');
    } catch (err) {
      setError('Покупатель не найден');
      setCustomer(null);
    }
  };

  return (
    <div>
      <input
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        placeholder="+998901234567"
      />
      <button onClick={handleSearch}>Найти</button>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {customer && (
        <div>
          <h3>{customer.full_name}</h3>
          <p>Телефон: {customer.phone}</p>
          <p>Покупок: {customer.total_purchases_count}</p>
          <p>На сумму: {customer.total_purchases.toLocaleString()} сум</p>
          <p>Бонусы: {customer.loyalty_points}</p>
        </div>
      )}
    </div>
  );
};
```

---

## Формат телефона

Обязательный формат: `+998XXXXXXXXX`

**Примеры:**
- ✅ `+998901234567`
- ✅ `+998909876543`
- ❌ `998901234567` (нет +)
- ❌ `+998 90 123 45 67` (есть пробелы)
- ❌ `901234567` (нет +998)

---

## Типы клиентов

### individual (Физическое лицо)
```json
{
  "customer_type": "individual",
  "first_name": "Иван",
  "last_name": "Петров",
  "phone": "+998901234567"
}
```

### company (Юридическое лицо)
```json
{
  "customer_type": "company",
  "company_name": "ООО Рога и Копыта",
  "tax_id": "123456789",
  "first_name": "Контактное лицо",
  "phone": "+998901111111"
}
```

---

## Ошибки

### 400 Bad Request - Телефон уже существует
```json
{
  "phone": ["Покупатель с таким номером телефона уже существует"]
}
```

### 400 Bad Request - Неверный формат телефона
```json
{
  "phone": ["Введите правильное значение."]
}
```

### 400 Bad Request - Не указано название компании
```json
{
  "company_name": ["Для юридического лица обязательно укажите название компании"]
}
```

### 404 Not Found - Покупатель не найден
```json
{
  "status": "error",
  "message": "Покупатель не найден"
}
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
| `GET` | `/api/customers/customers/{id}/purchase-history/` | История покупок |
| `GET` | `/api/customers/customers/{id}/stats/` | Статистика |
| `GET` | `/api/customers/customers/vip_customers/` | VIP клиенты |

### Обязательные заголовки:
```
Authorization: Bearer {access_token}
X-Tenant-Key: {tenant_key}
```

### Обязательные поля при создании:
- `first_name`
- `phone` (формат: `+998XXXXXXXXX`)
- `company_name` (только для компаний)

Готово! 🎉
