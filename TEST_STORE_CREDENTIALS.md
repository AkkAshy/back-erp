# 🔐 Данные для тестового магазина

## 🏪 Магазин: **Тестовый Магазин**

**Tenant Key:** `test_shop_4dfa7a5a`

---

## 👤 Аккаунты

### 1️⃣ Администратор (Владелец)

**Логин:**
- Username: `admin_testshop`
- Password: `admin12345`

**Права:**
- Полный доступ к системе
- Управление сотрудниками
- Просмотр аналитики
- Управление товарами

### 2️⃣ Общий аккаунт сотрудников (Staff)

**Логин:**
- Username: `test_shop_staff`
- Password: `12345678`

💡 **Как администратор может получить эти данные программно:**

```bash
GET /api/users/stores/staff-credentials/
Authorization: Bearer {admin_token}
X-Tenant-Key: test_shop_4dfa7a5a
```

**Магазин определяется автоматически из X-Tenant-Key!**

См. [STAFF_CREDENTIALS_API.md](STAFF_CREDENTIALS_API.md) для деталей.

**Права:**
- Создание продаж
- Просмотр товаров
- Работа с клиентами
- Управление запасами

---

## 👥 Кассиры (для выбора при продаже)

После входа под `test_shop_staff` вы получите список кассиров:

1. **Иванов Антон** (ID: 7)
   - Телефон: +998901234567

2. **Петров Иван** (ID: 8)
   - Телефон: +998901234568

3. **Сидоров Петр** (ID: 9)
   - Телефон: +998901234569

---

## 🚀 Примеры запросов

### Логин администратора

```bash
curl -X POST https://back-erp-gules.vercel.app/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a" \
  -d '{
    "username": "admin_testshop",
    "password": "admin12345"
  }'
```

### Логин общего аккаунта сотрудников

```bash
curl -X POST https://back-erp-gules.vercel.app/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a" \
  -d '{
    "username": "test_shop_staff",
    "password": "12345678"
  }'
```

**Ответ будет содержать список кассиров:**
```json
{
  "status": "success",
  "data": {
    "access": "eyJhbGc...",
    "refresh": "eyJhbGc...",
    "user": {
      "id": 3,
      "username": "test_shop_staff",
      "first_name": "Сотрудники",
      "last_name": "Тестовый Магазин"
    },
    "available_stores": [
      {
        "id": 2,
        "name": "Тестовый Магазин",
        "slug": "test_shop",
        "tenant_key": "test_shop_4dfa7a5a",
        "cashiers": [
          {
            "id": 7,
            "full_name": "Иванов Антон",
            "phone": "+998901234567",
            "role": "cashier"
          },
          {
            "id": 8,
            "full_name": "Петров Иван",
            "phone": "+998901234568",
            "role": "cashier"
          },
          {
            "id": 9,
            "full_name": "Сидоров Петр",
            "phone": "+998901234569",
            "role": "cashier"
          }
        ]
      }
    ]
  }
}
```

---

## 📋 Флоу работы

### Для кассира:

1. **Вход в систему:**
   - Логин: `test_shop_staff` / `12345678`
   - Получаете список кассиров

2. **Выбор себя:**
   - Выбираете свой ID из списка (например, Антон = ID 7)
   - Сохраняете в localStorage

3. **Открытие смены:**
   ```javascript
   POST /api/sales/cashier-sessions/
   {
     "opening_cash": "100000.00"
     // cashier_id НЕ НУЖЕН!
   }
   ```

4. **Создание продаж:**
   ```javascript
   POST /api/sales/sales/
   {
     "session": 1,
     "cashier_id": 7,  // ⭐ Выбранный кассир!
     "items": [...],
     "payments": [...]
   }
   ```

5. **Закрытие смены:**
   ```javascript
   POST /api/sales/cashier-sessions/{id}/close/
   {
     "actual_cash": "122000.00"
   }
   ```

---

## 📱 Для фронтенда

### Axios настройка

```javascript
const api = axios.create({
  baseURL: 'https://back-erp-gules.vercel.app/api',
  headers: {
    'Content-Type': 'application/json',
    'X-Tenant-Key': 'test_shop_4dfa7a5a'
  }
});

// Add token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Полный пример

Смотри [QUICK_START.md](QUICK_START.md) и [CASHIER_FLOW_UPDATE.md](CASHIER_FLOW_UPDATE.md)

---

## 🔄 Дополнительные действия

### Создать еще кассира (через админа)

```bash
curl -X POST https://back-erp-gules.vercel.app/api/users/employees/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Мария",
    "last_name": "Васильева",
    "phone": "+998901234570",
    "role": "cashier"
  }'
```

### Посмотреть список сотрудников

```bash
curl -X GET https://back-erp-gules.vercel.app/api/users/employees/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a"
```

### Получить статистику кассиров

```bash
curl -X GET "https://back-erp-gules.vercel.app/api/sales/cashier-sessions/cashier-stats/?date_from=2025-01-01&date_to=2025-01-31" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a"
```

---

**Дата создания:** 2025-01-19
