# Гайд для фронтенд-разработчика: Регистрация

## Задача

Создать **одну большую форму регистрации** владельца магазина.

---

## Макет формы (React пример)

```jsx
import React, { useState } from 'react';

function RegistrationForm() {
  const [formData, setFormData] = useState({
    // Личные данные
    first_name: '',
    last_name: '',
    middle_name: '',
    owner_phone: '',
    email: '',

    // Логин/пароль
    username: '',
    password: '',
    password_confirm: '',

    // Магазин
    store_name: '',
    store_address: '',
    store_city: '',
    store_region: '',
    store_phone: '',
    store_email: '',
    store_legal_name: '',
    store_tax_id: ''
  });

  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      const response = await fetch('http://localhost:8000/api/users/auth/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      const result = await response.json();

      if (response.ok && result.status === 'success') {
        // УСПЕХ! Сохраняем данные
        localStorage.setItem('access_token', result.data.tokens.access);
        localStorage.setItem('refresh_token', result.data.tokens.refresh);
        localStorage.setItem('tenant_key', result.data.store.tenant_key);
        localStorage.setItem('user', JSON.stringify(result.data.user));
        localStorage.setItem('store', JSON.stringify(result.data.store));

        // Редирект в панель
        window.location.href = '/dashboard';
      } else {
        // Показываем ошибки валидации
        setErrors(result);
      }
    } catch (error) {
      alert('Ошибка сети. Проверьте соединение.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="registration-form">

      {/* СЕКЦИЯ 1: Личные данные */}
      <fieldset>
        <legend>👤 Личные данные владельца</legend>

        <div className="form-group">
          <label>Имя *</label>
          <input
            type="text"
            value={formData.first_name}
            onChange={(e) => setFormData({...formData, first_name: e.target.value})}
            required
          />
          {errors.first_name && <span className="error">{errors.first_name[0]}</span>}
        </div>

        <div className="form-group">
          <label>Фамилия</label>
          <input
            type="text"
            value={formData.last_name}
            onChange={(e) => setFormData({...formData, last_name: e.target.value})}
          />
        </div>

        <div className="form-group">
          <label>Отчество</label>
          <input
            type="text"
            value={formData.middle_name}
            onChange={(e) => setFormData({...formData, middle_name: e.target.value})}
          />
        </div>

        <div className="form-group">
          <label>Телефон *</label>
          <input
            type="tel"
            placeholder="+998901234567"
            value={formData.owner_phone}
            onChange={(e) => setFormData({...formData, owner_phone: e.target.value})}
            required
          />
          {errors.owner_phone && <span className="error">{errors.owner_phone[0]}</span>}
        </div>

        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
          />
        </div>
      </fieldset>

      {/* СЕКЦИЯ 2: Логин и пароль */}
      <fieldset>
        <legend>🔐 Создайте логин и пароль</legend>

        <div className="form-group">
          <label>Логин *</label>
          <input
            type="text"
            value={formData.username}
            onChange={(e) => setFormData({...formData, username: e.target.value})}
            required
          />
          {errors.username && <span className="error">{errors.username[0]}</span>}
        </div>

        <div className="form-group">
          <label>Пароль *</label>
          <input
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            required
            minLength={8}
          />
          {errors.password && <span className="error">{errors.password[0]}</span>}
        </div>

        <div className="form-group">
          <label>Повторите пароль *</label>
          <input
            type="password"
            value={formData.password_confirm}
            onChange={(e) => setFormData({...formData, password_confirm: e.target.value})}
            required
          />
          {errors.password_confirm && <span className="error">{errors.password_confirm[0]}</span>}
        </div>
      </fieldset>

      {/* СЕКЦИЯ 3: Данные магазина */}
      <fieldset>
        <legend>🏪 Данные вашего магазина</legend>

        <div className="form-group">
          <label>Название магазина *</label>
          <input
            type="text"
            placeholder="Супермаркет Азия"
            value={formData.store_name}
            onChange={(e) => setFormData({...formData, store_name: e.target.value})}
            required
          />
        </div>

        <div className="form-group">
          <label>Адрес *</label>
          <input
            type="text"
            placeholder="ул. Навои, д. 45"
            value={formData.store_address}
            onChange={(e) => setFormData({...formData, store_address: e.target.value})}
            required
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Город</label>
            <input
              type="text"
              placeholder="Ташкент"
              value={formData.store_city}
              onChange={(e) => setFormData({...formData, store_city: e.target.value})}
            />
          </div>

          <div className="form-group">
            <label>Область</label>
            <input
              type="text"
              placeholder="Ташкентская область"
              value={formData.store_region}
              onChange={(e) => setFormData({...formData, store_region: e.target.value})}
            />
          </div>
        </div>

        <div className="form-group">
          <label>Телефон магазина *</label>
          <input
            type="tel"
            placeholder="+998712345678"
            value={formData.store_phone}
            onChange={(e) => setFormData({...formData, store_phone: e.target.value})}
            required
          />
        </div>

        <div className="form-group">
          <label>Email магазина</label>
          <input
            type="email"
            placeholder="info@mystore.uz"
            value={formData.store_email}
            onChange={(e) => setFormData({...formData, store_email: e.target.value})}
          />
        </div>

        {/* Юридические данные (скрыто по умолчанию) */}
        <details>
          <summary>📋 Юридические данные (необязательно)</summary>

          <div className="form-group">
            <label>Юридическое название</label>
            <input
              type="text"
              placeholder="ООО Супермаркет Азия"
              value={formData.store_legal_name}
              onChange={(e) => setFormData({...formData, store_legal_name: e.target.value})}
            />
          </div>

          <div className="form-group">
            <label>ИНН</label>
            <input
              type="text"
              placeholder="123456789"
              value={formData.store_tax_id}
              onChange={(e) => setFormData({...formData, store_tax_id: e.target.value})}
            />
          </div>
        </details>
      </fieldset>

      {/* Кнопка отправки */}
      <button type="submit" disabled={loading}>
        {loading ? 'Регистрация...' : 'Зарегистрироваться'}
      </button>

    </form>
  );
}

export default RegistrationForm;
```

---

## CSS для формы

```css
.registration-form {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

fieldset {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

legend {
  font-size: 18px;
  font-weight: bold;
  padding: 0 10px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.error {
  color: red;
  font-size: 12px;
  display: block;
  margin-top: 5px;
}

details {
  margin-top: 15px;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 4px;
}

details summary {
  cursor: pointer;
  font-weight: 500;
}

button[type="submit"] {
  width: 100%;
  padding: 15px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
}

button[type="submit"]:hover {
  background: #0056b3;
}

button[type="submit"]:disabled {
  background: #ccc;
  cursor: not-allowed;
}
```

---

## API Endpoint

```
POST http://localhost:8000/api/users/auth/register/
```

---

## Request Body (JSON)

```json
{
  "first_name": "Иван",
  "last_name": "Петров",
  "middle_name": "Сергеевич",
  "owner_phone": "+998901234567",
  "email": "ivan@example.com",
  "username": "ivan_owner",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "store_name": "Супермаркет Азия",
  "store_address": "ул. Навои, д. 45",
  "store_city": "Ташкент",
  "store_region": "Ташкентская область",
  "store_phone": "+998712345678",
  "store_email": "info@asiamarket.uz",
  "store_legal_name": "ООО Супермаркет Азия",
  "store_tax_id": "123456789"
}
```

---

## Response при успехе

```json
{
  "status": "success",
  "message": "Регистрация успешна",
  "data": {
    "user": {...},
    "store": {
      "tenant_key": "asia_market_a3f4b2c1"  // ⭐ ВАЖНО!
    },
    "tokens": {
      "access": "...",
      "refresh": "..."
    }
  }
}
```

---

## Response при ошибках валидации

```json
{
  "username": ["Пользователь с таким логином уже существует"],
  "password_confirm": ["Пароли не совпадают"],
  "owner_phone": ["Номер телефона должен быть в формате: +998XXXXXXXXX"]
}
```

---

## Что сохранять после успеха

```javascript
// 1. Токены
localStorage.setItem('access_token', result.data.tokens.access);
localStorage.setItem('refresh_token', result.data.tokens.refresh);

// 2. Tenant Key (ОБЯЗАТЕЛЬНО!)
localStorage.setItem('tenant_key', result.data.store.tenant_key);

// 3. Данные пользователя и магазина
localStorage.setItem('user', JSON.stringify(result.data.user));
localStorage.setItem('store', JSON.stringify(result.data.store));
```

---

## Использование в дальнейших запросах

```javascript
const access_token = localStorage.getItem('access_token');
const tenant_key = localStorage.getItem('tenant_key');

fetch('http://localhost:8000/api/products/', {
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'X-Tenant-Key': tenant_key  // ⭐ ОБЯЗАТЕЛЬНО!
  }
})
```

---

## Валидация на фронтенде (опционально)

```javascript
// Проверка формата телефона
const validatePhone = (phone) => {
  return /^\+998\d{9}$/.test(phone);
};

// Проверка совпадения паролей
const validatePasswords = (password, confirm) => {
  return password === confirm;
};

// Проверка длины пароля
const validatePasswordLength = (password) => {
  return password.length >= 8;
};
```

---

## Минимальные обязательные поля

Если хочешь упростить форму:

```javascript
// Обязательные:
first_name
owner_phone
username
password
password_confirm
store_name
store_address
store_phone

// Всё остальное - опционально
```

---

## Итого

1. Создай **одну форму** с 3 секциями
2. Отправь POST запрос на `/api/users/auth/register/`
3. Сохрани токены и `tenant_key`
4. Редирект в `/dashboard`

**Никаких дополнительных шагов!**
