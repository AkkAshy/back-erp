# Поток регистрации владельца - одно окно

## Суть

Владелец заполняет **ОДНУ большую форму** и получает всё сразу:
- ✅ Аккаунт пользователя
- ✅ Магазин с полными данными
- ✅ Роль владельца
- ✅ JWT токены для входа

## Endpoint

```
POST /api/users/auth/register/
```

**Публичный** - без токена!

---

## Форма регистрации - 3 секции

### 1️⃣ Личные данные владельца

```
Имя *                    [          ]
Фамилия                  [          ]
Отчество                 [          ]
Телефон *                [+998      ]
Email                    [          ]
```

### 2️⃣ Создайте логин и пароль

```
Логин *                  [          ]
Пароль *                 [          ]
Повторите пароль *       [          ]
```

### 3️⃣ Данные вашего магазина

```
Название магазина *      [          ]
Адрес *                  [          ]
Город                    [          ]
Область/регион           [          ]
Телефон магазина *       [+998      ]
Email магазина           [          ]

▼ Юридические данные (необязательно)
  Юридическое название   [          ]
  ИНН                    [          ]
```

**[Зарегистрироваться]**

---

## Что происходит после отправки

### Backend делает (в 1 транзакции):

1. **Создаёт User**
   - username, password (хешированный)
   - first_name, last_name
   - email
   - is_staff = True (владелец)

2. **Создаёт Store**
   - name, slug (авто-генерация)
   - address, city, region
   - phone, email
   - legal_name, tax_id
   - Генерирует `tenant_key` (уникальный ключ)
   - Генерирует `schema_name` для PostgreSQL

3. **Создаёт Employee**
   - Связь user ↔ store
   - role = 'owner'
   - phone (личный телефон)

4. **Создаёт PostgreSQL schema**
   - Изолированное хранилище данных для магазина
   - Имя: `tenant_{slug}`

5. **Генерирует JWT токены**
   - access (15 мин)
   - refresh (7 дней)

---

## Ответ при успехе

```json
{
  "status": "success",
  "message": "Регистрация успешна",
  "data": {
    "user": {
      "id": 1,
      "username": "ivan_owner",
      "full_name": "Петров Иван"
    },
    "store": {
      "id": 1,
      "name": "Супермаркет Азия",
      "slug": "asia_market",
      "tenant_key": "asia_market_a3f4b2c1",  ⭐ ВАЖНО!
      "address": "ул. Навои, д. 45",
      "city": "Ташкент",
      "phone": "+998712345678"
    },
    "employee": {
      "id": 1,
      "role": "owner",
      "phone": "+998901234567"
    },
    "tokens": {
      "access": "eyJ0eXAiOi...",
      "refresh": "eyJ0eXAiOi..."
    }
  }
}
```

---

## Что делает фронтенд после успеха

```javascript
const response = await fetch('/api/users/auth/register/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(formData)
});

const result = await response.json();

if (result.status === 'success') {
  // 1. Сохраняем токены
  localStorage.setItem('access_token', result.data.tokens.access);
  localStorage.setItem('refresh_token', result.data.tokens.refresh);

  // 2. Сохраняем tenant_key (ОБЯЗАТЕЛЬНО!)
  localStorage.setItem('tenant_key', result.data.store.tenant_key);

  // 3. Сохраняем инфо о пользователе
  localStorage.setItem('user', JSON.stringify(result.data.user));
  localStorage.setItem('store', JSON.stringify(result.data.store));

  // 4. Перенаправляем в панель управления
  window.location.href = '/dashboard';
}
```

---

## Использование после регистрации

Теперь владелец может делать запросы:

```javascript
fetch('/api/products/', {
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'X-Tenant-Key': 'asia_market_a3f4b2c1'  // ⭐ ОБЯЗАТЕЛЬНО!
  }
})
```

- `Authorization` - JWT токен (кто ты)
- `X-Tenant-Key` - ключ магазина (к какому магазину обращаешься)

---

## Валидация при регистрации

### ❌ Ошибки которые могут быть:

1. **Логин занят**
   ```json
   { "username": ["Пользователь с таким логином уже существует"] }
   ```

2. **Пароли не совпадают**
   ```json
   { "password_confirm": ["Пароли не совпадают"] }
   ```

3. **Слабый пароль**
   ```json
   { "password": ["Пароль слишком короткий. Минимум 8 символов."] }
   ```

4. **Неверный формат телефона**
   ```json
   { "owner_phone": ["Номер должен быть: +998XXXXXXXXX"] }
   ```

### ✅ Фронтенд показывает ошибки рядом с полем:

```jsx
{errors.username && <span className="error">{errors.username[0]}</span>}
```

---

## Что НЕ нужно делать

❌ НЕ разбивать на несколько шагов
❌ НЕ создавать отдельные endpoint для User и Store
❌ НЕ заставлять владельца заходить повторно
❌ НЕ просить заполнять данные после регистрации

✅ Всё в одной форме!
✅ Всё в одном запросе!
✅ Сразу готовый магазин!

---

## Преимущества этого подхода

1. **UX** - пользователь не лазит по интерфейсу
2. **Безопасность** - всё в одной транзакции
3. **Консистентность** - либо создаётся всё, либо ничего
4. **Простота** - один endpoint вместо 3-4

---

## Итого

```
Одна форма → Один POST → Готовый магазин + Токены!
```

Владелец сразу может начинать работу.
