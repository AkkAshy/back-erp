# 🏪 Создание нового магазина - API Guide

## Обзор

Endpoint позволяет существующему пользователю создать новый магазин. Автоматически создаются:
- Store (магазин)
- Employee с ролью OWNER для создателя
- Staff User для общего доступа сотрудников
- PostgreSQL Schema (если используется)
- Tenant Key для API запросов

---

## 🔗 Эндпоинт

```
POST /api/users/stores/
```

---

## 📋 Headers (обязательные)

| Заголовок | Описание | Пример |
|-----------|----------|--------|
| `Authorization` | Bearer токен пользователя | `Bearer eyJhbGc...` |
| `Content-Type` | Тип контента | `application/json` |

**⚠️ Примечание:** X-Tenant-Key НЕ требуется при создании магазина, только Authorization.

---

## 📤 Request Body

### Обязательные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `name` | string | Название магазина |

### Опциональные поля

| Поле | Тип | Описание | Пример |
|------|-----|----------|--------|
| `slug` | string | Уникальный идентификатор (если не указан - создастся автоматически) | `my_shop` |
| `description` | string | Описание магазина | `Продуктовый магазин в центре города` |
| `address` | string | Адрес | `г. Ташкент, ул. Амира Темура, 10` |
| `city` | string | Город | `Ташкент` |
| `region` | string | Область/регион | `Ташкентская область` |
| `phone` | string | Телефон магазина (формат: +998XXXXXXXXX) | `+998901234567` |
| `email` | string | Email магазина | `shop@example.com` |
| `legal_name` | string | Юридическое название | `ООО "Мой Магазин"` |
| `tax_id` | string | ИНН | `123456789` |

---

## 📥 Response Format

### Успешный ответ (201 Created)

```json
{
  "status": "success",
  "message": "Магазин успешно создан",
  "data": {
    "store": {
      "id": 3,
      "name": "Мой Новый Магазин",
      "slug": "moy_novyy_magazin",
      "tenant_key": "moy_novyy_magazin_x7y8z9a0",
      "schema_name": "store_moy_novyy_magazin_x7y8z9a0",
      "address": "г. Ташкент, ул. Амира Темура, 10",
      "city": "Ташкент",
      "phone": "+998901234567",
      "email": "shop@example.com",
      "is_active": true,
      "created_at": "2025-11-20T15:30:00+05:00"
    },
    "staff_credentials": {
      "username": "moy_novyy_magazin_staff",
      "password": "12345678",
      "note": "Общий аккаунт для всех сотрудников магазина"
    }
  }
}
```

### Ошибка: slug уже существует (400 Bad Request)

```json
{
  "slug": [
    "Магазин с таким slug уже существует"
  ]
}
```

---

## 💡 Примеры использования

### 1. Минимальный запрос (только название)

```bash
curl -X POST "https://back-erp-gules.vercel.app/api/users/stores/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Мой Новый Магазин"
  }'
```

**Результат:**
- Slug создастся автоматически: `moy_novyy_magazin`
- Tenant Key будет сгенерирован
- Staff credentials готовы к использованию

### 2. Полный запрос (все поля)

```bash
curl -X POST "https://back-erp-gules.vercel.app/api/users/stores/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Супермаркет Азия",
    "slug": "supermarket_asia",
    "description": "Продуктовый супермаркет в центре города",
    "address": "г. Ташкент, ул. Амира Темура, 10",
    "city": "Ташкент",
    "region": "Ташкентская область",
    "phone": "+998901234567",
    "email": "info@supermarket-asia.uz",
    "legal_name": "ООО Супермаркет Азия",
    "tax_id": "123456789"
  }'
```

### 3. JavaScript пример

```javascript
async function createStore(storeData) {
  try {
    const response = await api.post('/users/stores/', storeData);

    const { store, staff_credentials } = response.data.data;

    console.log('✅ Магазин создан:', store.name);
    console.log('📋 Tenant Key:', store.tenant_key);
    console.log('🔑 Staff Username:', staff_credentials.username);
    console.log('🔑 Staff Password:', staff_credentials.password);

    // Сохраняем tenant_key для дальнейших запросов
    localStorage.setItem('current_tenant_key', store.tenant_key);

    return { store, staff_credentials };
  } catch (error) {
    console.error('❌ Ошибка создания магазина:', error.response?.data);
    throw error;
  }
}

// Использование - минимальный вариант
const result = await createStore({
  name: 'Мой Новый Магазин'
});

// Использование - с дополнительными полями
const result2 = await createStore({
  name: 'Супермаркет Азия',
  slug: 'supermarket_asia',
  address: 'г. Ташкент, ул. Амира Темура, 10',
  city: 'Ташкент',
  phone: '+998901234567',
  email: 'info@supermarket-asia.uz'
});
```

### 4. React компонент - Форма создания магазина

```jsx
import { useState } from 'react';
import { api } from './api';

function CreateStoreForm({ onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    address: '',
    city: '',
    phone: '',
    email: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/users/stores/', formData);
      const { store, staff_credentials } = response.data.data;

      // Уведомляем родительский компонент об успехе
      onSuccess({ store, staff_credentials });

      // Очищаем форму
      setFormData({
        name: '',
        slug: '',
        address: '',
        city: '',
        phone: '',
        email: ''
      });
    } catch (err) {
      setError(err.response?.data || 'Ошибка создания магазина');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <form onSubmit={handleSubmit} className="create-store-form">
      <h2>Создать новый магазин</h2>

      {error && (
        <div className="error">
          {JSON.stringify(error)}
        </div>
      )}

      <div className="form-group">
        <label>Название магазина *</label>
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          placeholder="Мой Магазин"
        />
      </div>

      <div className="form-group">
        <label>Slug (опционально)</label>
        <input
          type="text"
          name="slug"
          value={formData.slug}
          onChange={handleChange}
          placeholder="my_shop (создастся автоматически если не указать)"
        />
        <small>Только буквы, цифры и подчеркивание</small>
      </div>

      <div className="form-group">
        <label>Адрес</label>
        <input
          type="text"
          name="address"
          value={formData.address}
          onChange={handleChange}
          placeholder="г. Ташкент, ул. Амира Темура, 10"
        />
      </div>

      <div className="form-group">
        <label>Город</label>
        <input
          type="text"
          name="city"
          value={formData.city}
          onChange={handleChange}
          placeholder="Ташкент"
        />
      </div>

      <div className="form-group">
        <label>Телефон</label>
        <input
          type="tel"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          placeholder="+998901234567"
          pattern="^\+998\d{9}$"
        />
        <small>Формат: +998XXXXXXXXX</small>
      </div>

      <div className="form-group">
        <label>Email</label>
        <input
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="shop@example.com"
        />
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Создание...' : 'Создать магазин'}
      </button>
    </form>
  );
}

// Использование
function App() {
  const handleStoreCreated = ({ store, staff_credentials }) => {
    alert(`Магазин "${store.name}" создан!\n\nStaff логин: ${staff_credentials.username}\nПароль: ${staff_credentials.password}`);

    // Сохраняем tenant_key
    localStorage.setItem('current_tenant_key', store.tenant_key);

    // Перенаправляем на страницу магазина
    window.location.href = `/stores/${store.id}`;
  };

  return (
    <div>
      <CreateStoreForm onSuccess={handleStoreCreated} />
    </div>
  );
}
```

---

## 🔍 Логика работы

1. **Валидация slug:**
   - Если не указан - генерируется автоматически из названия
   - Проверяется уникальность
   - Допустимы только буквы, цифры и подчеркивание
   - Не может начинаться с цифры

2. **Создание Store:**
   - Owner устанавливается автоматически (текущий пользователь)
   - Генерируется уникальный tenant_key
   - Создается schema_name

3. **Автоматически через signal:**
   - Создается Employee с ролью OWNER для создателя
   - Создается Staff User (username: `{slug}_staff`, password: `12345678`)
   - Создается Employee с ролью STAFF для staff user
   - Создается общая касса (CashRegister) для магазина

4. **PostgreSQL Schema:**
   - Создается отдельная schema для изоляции данных магазина
   - Имя: `store_{slug}_{random}`

---

## ⚠️ Важные замечания

1. **Один пользователь - несколько магазинов:**
   - Один пользователь может создать неограниченное количество магазинов
   - Он будет владельцем всех созданных им магазинов
   - Каждый магазин полностью изолирован

2. **Tenant Key:**
   - Автоматически генерируется при создании
   - Используется в заголовке `X-Tenant-Key` для всех последующих запросов
   - **Сохраните его!** Без tenant_key вы не сможете работать с API магазина

3. **Staff Credentials:**
   - Создаются автоматически
   - Username: `{slug}_staff`
   - Password: `12345678` (стандартный)
   - Используются всеми сотрудниками для входа в POS

4. **Slug генерация:**
   - Если не указан - создается из названия (transliteration + slugify)
   - Гарантируется уникальность (добавляется счетчик если нужно)
   - Примеры:
     - "Мой Магазин" → `moy_magazin`
     - "My Shop" → `my_shop`
     - "Shop 123" → `shop_123`

5. **Автоматическое создание Owner Employee:**
   - Создатель магазина автоматически становится Employee с ролью OWNER
   - Это дает ему полные права на управление магазином

---

## 🔐 Требования

- **Аутентификация:** Bearer token (JWT) любого зарегистрированного пользователя
- **НЕ требуется:** X-Tenant-Key (магазин еще не существует)
- **Права:** Любой авторизованный пользователь может создать магазин

---

## 📝 Связанные эндпоинты

- `POST /api/users/auth/register/` - Регистрация нового пользователя (создает первый магазин)
- `GET /api/users/stores/` - Список магазинов пользователя
- `GET /api/users/stores/staff-credentials/` - Получить credentials staff аккаунта существующего магазина
- `POST /api/users/employees/` - Добавить сотрудника в магазин

---

## 🎯 Use Cases

### Для владельца сети магазинов

```javascript
// Создаем несколько магазинов одним пользователем
const stores = [];

// Магазин №1
const store1 = await createStore({
  name: 'Магазин №1 - Центр',
  address: 'г. Ташкент, ул. Амира Темура, 10',
  city: 'Ташкент'
});
stores.push(store1);

// Магазин №2
const store2 = await createStore({
  name: 'Магазин №2 - Чиланзар',
  address: 'г. Ташкент, Чиланзар, 5 квартал',
  city: 'Ташкент'
});
stores.push(store2);

console.log(`Создано магазинов: ${stores.length}`);
stores.forEach((s, i) => {
  console.log(`${i+1}. ${s.store.name} - ${s.store.tenant_key}`);
});
```

### Для франшизы

```javascript
// Каждый франчайзи регистрируется и создает свой магазин
async function setupFranchise(userData, storeData) {
  // 1. Регистрация пользователя
  const regResponse = await api.post('/users/auth/register/', userData);
  const { access } = regResponse.data;

  // 2. Создание магазина
  api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
  const storeResponse = await api.post('/users/stores/', storeData);

  return storeResponse.data.data;
}
```

---

**Дата создания:** 2025-11-20
**Версия API:** 1.0
