# 👥 Управление сотрудниками - API Guide

## 📋 Обзор

Два основных эндпоинта для работы с сотрудниками:
1. **Список кассиров** - для выбора при продаже (простой формат)
2. **Полный список сотрудников** - для управления персоналом (детальный формат)

---

## 1️⃣ Список кассиров (упрощенный)

### Эндпоинт
```
GET /api/users/employees/cashiers/
```

### Назначение
- 🎯 **Для выбора кассира при создании продажи**
- Возвращает только активных кассиров и складчиков
- Упрощенный формат (только нужные поля)
- Исключает сотрудников с user аккаунтами (администраторов)

### Пример запроса

```bash
curl -X GET "http://localhost:8000/api/users/employees/cashiers/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a"
```

### Response

```json
{
  "status": "success",
  "data": [
    {
      "id": 9,
      "full_name": "Сидоров Петр",
      "phone": "+998901234569",
      "role": "cashier"
    },
    {
      "id": 8,
      "full_name": "Петров Иван",
      "phone": "+998901234568",
      "role": "cashier"
    },
    {
      "id": 7,
      "full_name": "Иванов Антон",
      "phone": "+998901234567",
      "role": "cashier"
    }
  ]
}
```

### JavaScript пример

```javascript
// Получить список кассиров для выбора
async function getCashiers() {
  const response = await api.get('/users/employees/cashiers/');
  return response.data.data;
}

// Использование
const cashiers = await getCashiers();

// Отобразить в select/dropdown
cashiers.forEach(cashier => {
  console.log(`${cashier.id}: ${cashier.full_name} (${cashier.phone})`);
});
```

### React компонент - Select кассира

```jsx
import { useState, useEffect } from 'react';

function CashierSelector({ value, onChange }) {
  const [cashiers, setCashiers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadCashiers() {
      try {
        const response = await api.get('/users/employees/cashiers/');
        setCashiers(response.data.data);
      } catch (error) {
        console.error('Error loading cashiers:', error);
      } finally {
        setLoading(false);
      }
    }
    loadCashiers();
  }, []);

  if (loading) return <div>Загрузка...</div>;

  return (
    <select value={value} onChange={(e) => onChange(Number(e.target.value))}>
      <option value="">Выберите кассира</option>
      {cashiers.map((cashier) => (
        <option key={cashier.id} value={cashier.id}>
          {cashier.full_name} ({cashier.phone})
        </option>
      ))}
    </select>
  );
}

// Использование
function SaleForm() {
  const [cashierId, setCashierId] = useState('');

  return (
    <div>
      <label>Кассир:</label>
      <CashierSelector value={cashierId} onChange={setCashierId} />
    </div>
  );
}
```

---

## 2️⃣ Полный список сотрудников

### Эндпоинт
```
GET /api/users/employees/
```

### Назначение
- 📊 **Для управления всеми сотрудниками**
- Возвращает всех сотрудников магазина (включая администраторов, менеджеров)
- Детальная информация (роль, дата найма, фото, и т.д.)
- Поддержка пагинации

### Пример запроса

```bash
curl -X GET "http://localhost:8000/api/users/employees/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a"
```

### Response

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 9,
      "user": null,
      "store": 2,
      "role": "cashier",
      "role_display": "Кассир",
      "phone": "+998901234569",
      "photo": null,
      "position": null,
      "sex": null,
      "sex_display": null,
      "is_active": true,
      "hired_at": "2025-11-19",
      "created_at": "2025-11-19T22:06:14.441178+05:00"
    }
  ]
}
```

### Поля Response

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer | ID сотрудника |
| `user` | integer/null | ID связанного User (null для простых кассиров) |
| `store` | integer | ID магазина |
| `role` | string | Роль: `owner`, `manager`, `cashier`, `stockkeeper`, `staff` |
| `role_display` | string | Роль на русском |
| `phone` | string | Номер телефона |
| `photo` | string/null | URL фото сотрудника |
| `position` | string/null | Должность |
| `sex` | string/null | Пол: `M`, `F` |
| `is_active` | boolean | Активен ли сотрудник |
| `hired_at` | date | Дата найма |
| `created_at` | datetime | Дата создания записи |

---

## 3️⃣ Создание нового сотрудника

### Эндпоинт
```
POST /api/users/employees/
```

### Request Body

```json
{
  "first_name": "Мария",
  "last_name": "Васильева",
  "phone": "+998901234570",
  "role": "cashier",
  "hired_at": "2025-11-20"
}
```

### Пример

```bash
curl -X POST "http://localhost:8000/api/users/employees/" \
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

### JavaScript пример

```javascript
async function createCashier(firstName, lastName, phone) {
  const response = await api.post('/users/employees/', {
    first_name: firstName,
    last_name: lastName,
    phone: phone,
    role: 'cashier'
  });

  return response.data;
}

// Использование
const newCashier = await createCashier('Мария', 'Васильева', '+998901234570');
console.log('Создан кассир:', newCashier);
```

---

## 4️⃣ Обновление сотрудника

### Эндпоинт
```
PATCH /api/users/employees/{id}/
```

### Пример

```bash
curl -X PATCH "http://localhost:8000/api/users/employees/9/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+998901234599",
    "is_active": true
  }'
```

---

## 5️⃣ Удаление сотрудника

### Эндпоинт
```
DELETE /api/users/employees/{id}/
```

### Пример

```bash
curl -X DELETE "http://localhost:8000/api/users/employees/9/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a"
```

**⚠️ Внимание:** Удаление безвозвратно!

---

## 📊 Сравнение эндпоинтов

| Характеристика | `/cashiers/` | `/employees/` |
|----------------|--------------|---------------|
| **Формат** | Упрощенный | Полный |
| **Поля** | id, full_name, phone, role | Все поля Employee |
| **Фильтр** | Только cashier/stockkeeper | Все роли |
| **Назначение** | Выбор при продаже | Управление персоналом |
| **Права** | Любой сотрудник | Owner/Manager |
| **User аккаунты** | Исключены | Включены |

---

## 🎯 Use Cases

### Для POS системы (кассы)

```javascript
// При создании продажи
const cashiers = await api.get('/users/employees/cashiers/');
// Показать select/dropdown с кассирами
```

### Для админ панели

```javascript
// Список всех сотрудников
const employees = await api.get('/users/employees/');

// Создать нового кассира
await api.post('/users/employees/', {
  first_name: 'Иван',
  last_name: 'Петров',
  phone: '+998901234567',
  role: 'cashier'
});

// Деактивировать сотрудника
await api.patch(`/users/employees/${employeeId}/`, {
  is_active: false
});
```

---

## ⚠️ Важные замечания

1. **Кассиры без User аккаунта:**
   - Создаются через `/employees/` endpoint
   - Не имеют логина/пароля
   - Выбираются из списка при продаже
   - Логинятся через общий staff аккаунт

2. **Администраторы:**
   - Имеют связь с User (`user` поле не null)
   - Не отображаются в `/cashiers/` endpoint
   - Отображаются в `/employees/` endpoint

3. **Права доступа:**
   - `/cashiers/` - доступен всем авторизованным (включая staff)
   - `/employees/` CRUD - только Owner/Manager

4. **Автоматическая фильтрация:**
   - Оба эндпоинта автоматически фильтруют по `request.tenant`
   - Не нужно указывать store_id

---

## 🔐 Требования

- **Аутентификация:** Bearer token (JWT)
- **Заголовок:** `X-Tenant-Key` с ключом магазина
- **Права для `/cashiers/`:** Любой авторизованный пользователь
- **Права для `/employees/`:** Owner или Manager

---

**Дата создания:** 2025-11-19
**Версия API:** 1.0
