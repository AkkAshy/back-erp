# 🚀 Применение Customers App

## ✅ Статус: Всё готово!

Приложение customers полностью создано и настроено.

---

## 📋 Быстрый старт

```bash
# 1. Активируй виртуальное окружение
source venv/bin/activate

# 2. Создай миграции для customers
python manage.py makemigrations customers

# 3. Применить миграции
python manage.py migrate

# 4. (Опционально) Создай суперпользователя если ещё не создан
python manage.py createsuperuser

# 5. Запусти сервер
python manage.py runserver

# 6. Открой Swagger для тестирования
# http://localhost:8000/swagger/
```

---

## 📁 Созданные файлы:

```
customers/
├── __init__.py             ✅
├── models.py               ✅ 3 модели (CustomerGroup, Customer, CustomerTransaction)
├── serializers.py          ✅ 5 сериализаторов
├── views.py                ✅ 3 ViewSet'а
├── urls.py                 ✅ REST API routing
├── admin.py                ✅ Django admin
├── apps.py                 ✅ Конфигурация
└── migrations/
    └── __init__.py         ✅

config/
├── settings.py             ✅ Добавлено customers.apps.CustomersConfig
└── urls.py                 ✅ Добавлен path('api/customers/')
```

---

## 🔌 Доступные endpoints:

После миграции будут доступны:

```
# Группы покупателей
GET    /api/customers/groups/
POST   /api/customers/groups/
GET    /api/customers/groups/{id}/
PUT    /api/customers/groups/{id}/
DELETE /api/customers/groups/{id}/
GET    /api/customers/groups/{id}/members/

# Покупатели
GET    /api/customers/customers/
POST   /api/customers/customers/
GET    /api/customers/customers/{id}/
PUT    /api/customers/customers/{id}/
DELETE /api/customers/customers/{id}/

# Операции с балансом
POST   /api/customers/customers/{id}/add_payment/
POST   /api/customers/customers/{id}/charge/

# История и аналитика
GET    /api/customers/customers/{id}/transactions_history/
GET    /api/customers/customers/{id}/stats/

# Специальные фильтры
GET    /api/customers/customers/search_by_phone/?phone=+998901234567
GET    /api/customers/customers/vip_customers/
GET    /api/customers/customers/debtors/

# Транзакции (read-only)
GET    /api/customers/transactions/
GET    /api/customers/transactions/{id}/
```

---

## 🎯 Первые шаги после миграции:

### 1. Создай базовые группы покупателей

```bash
POST /api/customers/groups/
Authorization: Bearer <token>
X-Tenant-Key: <tenant_key>

# Розница
{
  "name": "Розница",
  "description": "Розничные покупатели",
  "discount_percent": 0,
  "is_active": true
}

# Постоянные клиенты
{
  "name": "Постоянные клиенты",
  "description": "Покупки от 500,000 сум",
  "discount_percent": 5,
  "min_purchase_amount": 500000,
  "is_active": true
}

# VIP
{
  "name": "VIP",
  "description": "Покупки от 2,000,000 сум",
  "discount_percent": 10,
  "min_purchase_amount": 2000000,
  "is_active": true
}

# Оптовики
{
  "name": "Оптовики",
  "description": "Оптовые покупатели",
  "discount_percent": 15,
  "min_purchase_amount": 5000000,
  "is_active": true
}
```

### 2. Создай тестового покупателя

```bash
POST /api/customers/customers/
Authorization: Bearer <token>
X-Tenant-Key: <tenant_key>

{
  "first_name": "Иван",
  "last_name": "Иванов",
  "middle_name": "Иванович",
  "customer_type": "individual",
  "phone": "+998901234567",
  "email": "ivan@example.com",
  "credit_limit": 500000,
  "group": 1
}
```

### 3. Протестируй поиск

```bash
GET /api/customers/customers/search_by_phone/?phone=+998901234567
```

---

## 🔍 Примеры использования:

### Добавить платёж покупателю

```bash
POST /api/customers/customers/1/add_payment/

{
  "amount": 100000,
  "description": "Оплата долга"
}
```

### Продажа в кредит

```bash
POST /api/customers/customers/1/charge/

{
  "amount": 75000,
  "description": "Покупка в кредит"
}
```

### Получить статистику

```bash
GET /api/customers/customers/1/stats/
```

---

## ⚠️ Важно:

1. **Все запросы требуют**:
   - `Authorization: Bearer <access_token>`
   - `X-Tenant-Key: <tenant_key>`

2. **Телефон должен быть уникальным** в формате `+998XXXXXXXXX`

3. **Для юр. лиц обязательно** указывать `company_name`

4. **Транзакции автоматически обновляют баланс** покупателя

---

## 📚 Документация:

Полное руководство: [CUSTOMERS_APP_GUIDE.md](CUSTOMERS_APP_GUIDE.md)

---

**Всё готово к работе! 🎉**

Просто выполни миграции и начинай использовать!