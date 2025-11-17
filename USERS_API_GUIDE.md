# Users API - Создание пользователей/сотрудников

## Обзор

Есть **два способа** создать сотрудника:

1. **`POST /api/users/users/`** - основной эндпоинт (для совместимости с фронтендом)
2. **`POST /api/users/employees/`** - альтернативный эндпоинт

Оба эндпоинта работают одинаково и используют один и тот же `CreateEmployeeSerializer`.

---

## Создание сотрудника

### Эндпоинт
**POST** `/api/users/users/` или **POST** `/api/users/employees/`

### Права доступа
Только **owner** (владелец) или **manager** (менеджер) могут создавать сотрудников.

### Request Body

```json
{
  "username": "cashier1",
  "password": "SecurePass123!",
  "first_name": "Иван",
  "last_name": "Петров",
  "email": "ivan@example.com",
  "role": "cashier",
  "phone": "+998901234567",
  "position": "Кассир",
  "is_active": true
}
```

### Обязательные поля
- `username` - логин (уникальный)
- `password` - пароль (минимум 8 символов)
- `first_name` - имя
- `role` - роль сотрудника

### Опциональные поля
- `last_name` - фамилия
- `email` - email
- `phone` - телефон в формате `+998XXXXXXXXX`
- `position` - должность (например: "Кассир", "Продавец")
- `is_active` - активен ли сотрудник (по умолчанию `true`)

### Роли (role)
- `owner` - Владелец (нельзя создать через API)
- `manager` - Менеджер
- `cashier` - Кассир
- `stockkeeper` - Складчик

---

## Примеры

### 1. Создать кассира

**Request:**
```bash
POST /api/users/users/
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "username": "cashier1",
  "password": "Pass1234!",
  "first_name": "Иван",
  "last_name": "Петров",
  "role": "cashier",
  "phone": "+998901234567",
  "position": "Кассир"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Сотрудник создан",
  "data": {
    "id": 2,
    "user": {
      "id": 5,
      "username": "cashier1",
      "first_name": "Иван",
      "last_name": "Петров",
      "email": ""
    },
    "full_name": "Иван Петров",
    "role": "cashier",
    "role_display": "Кассир",
    "phone": "+998901234567",
    "position": "Кассир",
    "is_active": true,
    "hire_date": "2025-01-17",
    "created_at": "2025-01-17T12:00:00Z"
  }
}
```

### 2. Создать менеджера

**Request:**
```json
{
  "username": "manager1",
  "password": "Manager123!",
  "first_name": "Алексей",
  "last_name": "Смирнов",
  "email": "aleksey@store.com",
  "role": "manager",
  "phone": "+998901234568",
  "position": "Менеджер зала"
}
```

### 3. Создать складчика

**Request:**
```json
{
  "username": "warehouse1",
  "password": "Stock123!",
  "first_name": "Дмитрий",
  "role": "stockkeeper",
  "position": "Кладовщик"
}
```

---

## Ошибки

### 403 Forbidden - Нет прав
```json
{
  "status": "error",
  "code": "forbidden",
  "message": "Только владелец или менеджер может создавать сотрудников",
  "errors": {}
}
```

**Решение:** Убедитесь что вы вошли как owner или manager.

### 400 Bad Request - Логин занят
```json
{
  "status": "error",
  "code": "validation_error",
  "message": "Ошибка валидации",
  "errors": {
    "username": ["Пользователь с таким username уже существует."]
  }
}
```

**Решение:** Выберите другой username.

### 400 Bad Request - Слабый пароль
```json
{
  "status": "error",
  "code": "validation_error",
  "message": "Ошибка валидации",
  "errors": {
    "password": ["Пароль должен содержать минимум 8 символов"]
  }
}
```

**Решение:** Используйте более сложный пароль.

### 400 Bad Request - Неверный телефон
```json
{
  "status": "error",
  "code": "validation_error",
  "message": "Ошибка валидации",
  "errors": {
    "phone": ["Телефон должен быть в формате +998XXXXXXXXX"]
  }
}
```

**Решение:** Используйте формат `+998901234567` (Узбекистан).

---

## Список сотрудников

### GET `/api/users/users/`

Получить список всех пользователей (для выбора в UI).

**Response:**
```json
[
  {
    "id": 1,
    "username": "owner",
    "first_name": "Иван",
    "last_name": "Иванов",
    "email": "owner@store.com",
    "is_active": true,
    "date_joined": "2025-01-01T00:00:00Z"
  },
  {
    "id": 2,
    "username": "cashier1",
    "first_name": "Петр",
    "last_name": "Петров",
    "email": "",
    "is_active": true,
    "date_joined": "2025-01-10T00:00:00Z"
  }
]
```

### GET `/api/users/employees/`

Получить список сотрудников с деталями (роль, должность, телефон).

**Response:**
```json
[
  {
    "id": 1,
    "full_name": "Иван Иванов",
    "username": "owner",
    "role": "owner",
    "role_display": "Владелец",
    "position": "Директор",
    "phone": "+998901234567",
    "is_active": true,
    "hire_date": "2025-01-01"
  },
  {
    "id": 2,
    "full_name": "Петр Петров",
    "username": "cashier1",
    "role": "cashier",
    "role_display": "Кассир",
    "position": "Кассир",
    "phone": "+998901234568",
    "is_active": true,
    "hire_date": "2025-01-10"
  }
]
```

---

## Поиск пользователей

### GET `/api/users/users/?name=Иван`

Поиск по имени, фамилии или логину.

**Query Parameters:**
- `name` - строка для поиска
- `search` - альтернативный параметр поиска

---

## Обновление и удаление

### Обновить сотрудника
**PUT/PATCH** `/api/users/employees/{id}/`

### Удалить сотрудника
**DELETE** `/api/users/employees/{id}/`

**Важно:** Обновление и удаление через `/api/users/users/{id}/` **запрещено**. Используйте `/api/users/employees/{id}/`.

---

## Сброс пароля сотрудника

### POST `/api/users/employees/{id}/reset-password/`

Владелец или менеджер может сбросить пароль любого сотрудника.

**Request:**
```json
{
  "new_password": "NewPass123!"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Пароль успешно сброшен"
}
```

---

## Postman примеры

### Создание кассира
```
POST {{base_url}}/api/users/users/
Authorization: Bearer {{access_token}}

{
  "username": "cashier1",
  "password": "Pass1234!",
  "first_name": "Иван",
  "last_name": "Петров",
  "role": "cashier",
  "phone": "+998901234567",
  "position": "Кассир"
}
```

### Список пользователей
```
GET {{base_url}}/api/users/users/
Authorization: Bearer {{access_token}}
```

### Поиск по имени
```
GET {{base_url}}/api/users/users/?name=Иван
Authorization: Bearer {{access_token}}
```

---

## Типичные сценарии

### 1. Добавить нового кассира
1. Owner открывает страницу "Сотрудники"
2. Нажимает "Добавить сотрудника"
3. Заполняет форму:
   - Username: `cashier2`
   - Password: `Cashier123!`
   - Имя: `Анна`
   - Роль: `cashier`
   - Телефон: `+998901234569`
4. Нажимает "Создать"
5. Frontend отправляет `POST /api/users/users/`
6. Кассир создан и может войти в систему

### 2. Поиск сотрудника для назначения задачи
1. Manager создает задачу
2. В поле "Назначить" начинает вводить имя
3. Frontend отправляет `GET /api/users/users/?name=Ива`
4. Показывает список: Иван Иванов, Иван Петров
5. Manager выбирает нужного сотрудника

---

## FAQ

**Q: Почему два эндпоинта для создания сотрудников?**
A: `/api/users/users/` - для совместимости с фронтендом, который привык работать с `/users/`. `/api/users/employees/` - более явный эндпоинт.

**Q: Можно ли создать owner через API?**
A: Нет. Owner создается только при регистрации магазина через `/api/users/auth/register/`.

**Q: Какой минимальный пароль?**
A: Минимум 8 символов. Рекомендуем использовать буквы, цифры и спецсимволы.

**Q: Как узнать, кто может создавать сотрудников?**
A: Только owner и manager. Проверьте `request.user.employee.role`.

**Q: Можно ли создать сотрудника без телефона?**
A: Да, телефон опциональный. Но если указываете, используйте формат `+998XXXXXXXXX`.

---

## Совместимость с фронтендом

Фронтенд может использовать любой из эндпоинтов:

```typescript
// Вариант 1 (рекомендуется)
POST /api/users/users/

// Вариант 2
POST /api/users/employees/
```

Оба работают идентично и возвращают один и тот же формат ответа.
