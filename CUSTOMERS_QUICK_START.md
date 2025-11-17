# Покупатели - Быстрый старт

## Создать покупателя

```bash
POST /api/customers/customers/
{
  "first_name": "Иван",
  "last_name": "Петров",
  "phone": "+998901234567",
  "email": "ivan@example.com"
}
```

## Найти по телефону

```bash
GET /api/customers/customers/search_by_phone/?phone=+998901234567
```

## Получить список

```bash
# Все покупатели
GET /api/customers/customers/

# Поиск
GET /api/customers/customers/?search=Иван

# Только компании
GET /api/customers/customers/?customer_type=company

# VIP клиенты
GET /api/customers/customers/vip_customers/
```

## Обновить

```bash
PATCH /api/customers/customers/1/
{
  "email": "newemail@example.com",
  "credit_limit": 2000000
}
```

## Работа с балансом

```bash
# Пополнить баланс
POST /api/customers/customers/1/add_payment/
{
  "amount": 100000,
  "description": "Пополнение"
}

# Списать
POST /api/customers/customers/1/charge/
{
  "amount": 50000,
  "description": "Оплата товара"
}
```

## История транзакций

```bash
GET /api/customers/customers/1/transactions_history/
```

## Статистика

```bash
GET /api/customers/customers/1/stats/
```

---

## Frontend (React)

```typescript
import api from '@/utils/api';

// Создать
const customer = await api.post('/customers/customers/', {
  first_name: 'Иван',
  phone: '+998901234567'
});

// Найти по телефону
const found = await api.get('/customers/customers/search_by_phone/', {
  params: { phone: '+998901234567' }
});

// Пополнить баланс
const payment = await api.post('/customers/customers/1/add_payment/', {
  amount: 100000,
  description: 'Пополнение'
});
```

---

## Формат телефона

```
+998XXXXXXXXX
```

Примеры:
- ✅ `+998901234567`
- ❌ `998901234567`
- ❌ `+998 90 123 45 67`

---

## Типы клиентов

- `individual` - Физическое лицо
- `company` - Юридическое лицо (требует `company_name`)
