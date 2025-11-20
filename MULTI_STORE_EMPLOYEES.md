# 👥 Работа с сотрудниками в нескольких магазинах

**Дата:** 2025-11-20

---

## 🎯 Сценарий: Владелец с несколькими магазинами

### Архитектура

Система поддерживает **один User → несколько Employee записей**:

```
User (john_doe)
  └─ Employee #1 (Store A, role: manager)
  └─ Employee #2 (Store B, role: cashier)
  └─ Employee #3 (Store C, role: manager)
```

**Важно:**
- `User` хранится в **public** схеме (shared)
- `Employee` хранится в **tenant** схеме каждого магазина
- Один человек может работать в разных магазинах с разными ролями

---

## 📋 Примеры использования

### Сценарий 1: Владелец имеет 2 магазина

```bash
# Владелец: admin
# Магазин A: test_shop (tenant_key: test_shop_4dfa7a5a)
# Магазин B: asdawd (tenant_key: asdawd_8b43a536)
```

### Шаг 1: Создать сотрудника в первом магазине

```bash
TOKEN="<admin_jwt_token>"

# Создаем сотрудника Ивана в магазине test_shop
curl -X POST http://localhost:8000/api/users/employees/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ivan_manager",
    "password": "secure_pass_123",
    "first_name": "Иван",
    "last_name": "Петров",
    "email": "ivan@example.com",
    "role": "manager",
    "phone": "+998901234567",
    "position": "Менеджер зала"
  }'
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Сотрудник успешно создан",
  "data": {
    "employee": {
      "id": 10,
      "full_name": "Иван Петров",
      "username": "ivan_manager",
      "role": "manager",
      "role_display": "Менеджер",
      "phone": "+998901234567",
      "position": "Менеджер зала",
      "is_active": true
    },
    "credentials": {
      "username": "ivan_manager",
      "password": "secure_pass_123"
    }
  }
}
```

**Результат:**
- ✅ Создан User `ivan_manager` в **public** схеме
- ✅ Создан Employee в **tenant_test_shop** схеме
- ✅ Иван может войти с X-Tenant-Key: test_shop_4dfa7a5a

### Шаг 2: Добавить того же сотрудника во второй магазин

```bash
# Добавляем Ивана в магазин asdawd (используем существующий username)
curl -X POST http://localhost:8000/api/users/employees/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: asdawd_8b43a536" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ivan_manager",
    "password": "secure_pass_123",
    "first_name": "Иван",
    "last_name": "Петров",
    "role": "cashier",
    "phone": "+998901234567",
    "position": "Кассир"
  }'
```

**Проблема:** ❌ Получим ошибку "Пользователь с таким логином уже существует"

---

## 🔧 Решение: Добавить существующего User в другой магазин

Нужно создать специальный endpoint для добавления **существующего** сотрудника в другой магазин.

### Новый endpoint: `POST /api/users/employees/add-existing/`

**Логика:**
1. Проверяем что User существует
2. Проверяем что владелец имеет доступ к обоим магазинам
3. Создаем новую запись Employee для текущего магазина (request.tenant)

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/users/employees/add-existing/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: asdawd_8b43a536" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ivan_manager",
    "role": "cashier",
    "position": "Кассир"
  }'
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Сотрудник добавлен в магазин",
  "data": {
    "employee": {
      "id": 15,
      "full_name": "Иван Петров",
      "username": "ivan_manager",
      "role": "cashier",
      "role_display": "Кассир",
      "position": "Кассир",
      "is_active": true
    },
    "stores": [
      {
        "store_name": "test_shop",
        "role": "manager"
      },
      {
        "store_name": "asdawd",
        "role": "cashier"
      }
    ]
  }
}
```

---

## 💡 Альтернативное решение: Автоматическое определение

Можно модифицировать текущий endpoint создания сотрудника:

### Обновленная логика `POST /api/users/employees/`:

1. Проверяем существует ли User с таким username
2. **Если существует:**
   - Проверяем что владелец имеет к нему доступ (есть Employee в другом магазине владельца)
   - Создаем только Employee запись в текущем магазине
   - Не требуем password (используем существующий)
3. **Если не существует:**
   - Создаем User + Employee (текущее поведение)

**Преимущества:**
- ✅ Один endpoint для всех случаев
- ✅ Автоматически определяет что делать
- ✅ Не нужно менять фронтенд

**Пример запроса (username уже существует):**
```bash
curl -X POST http://localhost:8000/api/users/employees/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: asdawd_8b43a536" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ivan_manager",
    "role": "cashier",
    "position": "Кассир"
  }'
```

**Система автоматически:**
1. Находит User "ivan_manager"
2. Проверяет что владелец имеет доступ (есть Employee в другом его магазине)
3. Создает Employee в текущем магазине
4. Возвращает success без credentials (т.к. User уже был)

---

## 🔐 Проверка безопасности

### Важно: Владелец может добавить только своих сотрудников

```python
# Псевдокод проверки
def can_add_existing_user(owner, username, target_store):
    """
    Проверяет может ли владелец добавить существующего пользователя.
    """
    user = User.objects.get(username=username)

    # Проверяем что user уже работает в одном из магазинов владельца
    owner_stores = Store.objects.filter(owner=owner)
    existing_employment = Employee.objects.filter(
        user=user,
        store__in=owner_stores
    ).exists()

    if not existing_employment:
        raise PermissionDenied(
            "Вы можете добавить только сотрудников, "
            "которые уже работают в одном из ваших магазинов"
        )

    # Проверяем что employee еще не добавлен в целевой магазин
    if Employee.objects.filter(user=user, store=target_store).exists():
        raise ValidationError("Этот сотрудник уже работает в данном магазине")

    return True
```

---

## 📊 Примеры использования

### Пример 1: Владелец с 3 магазинами

```
Владелец: John (id=1)
Магазины:
  - Store A (test_shop)
  - Store B (asdawd)
  - Store C (new_store)

Сотрудник: Ivan (username: ivan_manager)
```

**Шаги:**

1. **Создать Ивана в Store A:**
   ```bash
   POST /api/users/employees/
   X-Tenant-Key: test_shop_xxx
   Body: {username: "ivan_manager", password: "pass123", role: "manager"}
   → User создан + Employee в Store A
   ```

2. **Добавить Ивана в Store B:**
   ```bash
   POST /api/users/employees/
   X-Tenant-Key: asdawd_xxx
   Body: {username: "ivan_manager", role: "cashier"}
   → Только Employee в Store B (User уже есть)
   ```

3. **Добавить Ивана в Store C:**
   ```bash
   POST /api/users/employees/
   X-Tenant-Key: new_store_xxx
   Body: {username: "ivan_manager", role: "manager"}
   → Только Employee в Store C
   ```

**Результат:**
```sql
-- public.auth_user
id | username      | ...
1  | john          | (владелец)
5  | ivan_manager  | (сотрудник)

-- tenant_test_shop.users_employee
id | user_id | store_id | role
10 | 5       | 1        | manager

-- tenant_asdawd.users_employee
id | user_id | store_id | role
15 | 5       | 2        | cashier

-- tenant_new_store.users_employee
id | user_id | store_id | role
8  | 5       | 3        | manager
```

### Пример 2: Логин сотрудника в разных магазинах

```bash
# Иван логинится в Store A
curl -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ivan_manager",
    "password": "secure_pass_123"
  }'
```

**Ответ:**
```json
{
  "access": "jwt_token...",
  "available_stores": [
    {
      "store": "test_shop",
      "tenant_key": "test_shop_xxx",
      "role": "manager",
      "permissions": ["view_all", "create_all", ...]
    },
    {
      "store": "asdawd",
      "tenant_key": "asdawd_xxx",
      "role": "cashier",
      "permissions": ["view_sales", "create_sales"]
    },
    {
      "store": "new_store",
      "tenant_key": "new_store_xxx",
      "role": "manager",
      "permissions": ["view_all", "create_all", ...]
    }
  ],
  "default_store": {
    "tenant_key": "test_shop_xxx",
    "role": "manager"
  }
}
```

**Затем Иван выбирает магазин:**
```bash
# Работа в Store A (как менеджер)
curl -X GET http://localhost:8000/api/sales/sales/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: test_shop_xxx"

# Работа в Store B (как кассир)
curl -X GET http://localhost:8000/api/sales/sales/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: asdawd_xxx"
```

---

## 🚀 Рекомендация: Обновить существующий endpoint

**Файл:** [users/serializers.py](users/serializers.py#L209-L266)

Добавить логику в `CreateEmployeeSerializer.create()`:

```python
@transaction.atomic
def create(self, validated_data):
    request = self.context.get('request')
    store = request.tenant
    username = validated_data.get('username')
    password = validated_data.get('password')

    user = None
    is_existing_user = False

    # Проверяем существует ли User
    if username:
        try:
            user = User.objects.get(username=username)
            is_existing_user = True

            # Проверка безопасности: владелец может добавить только своих сотрудников
            owner_stores = Store.objects.filter(owner=request.user)
            existing_employment = Employee.objects.filter(
                user=user,
                store__in=owner_stores
            ).exists()

            if not existing_employment:
                raise serializers.ValidationError(
                    "Вы можете добавить только сотрудников, которые уже работают "
                    "в одном из ваших магазинов"
                )

            # Проверяем что не дублируем
            if Employee.objects.filter(user=user, store=store).exists():
                raise serializers.ValidationError(
                    "Этот сотрудник уже работает в данном магазине"
                )

            logger.info(f"Adding existing user {username} to store {store.name}")

        except User.DoesNotExist:
            # User не существует - создаем нового (текущее поведение)
            if not password:
                raise serializers.ValidationError({
                    'password': 'Для нового сотрудника требуется пароль'
                })

            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=validated_data['first_name'],
                last_name=validated_data.get('last_name', ''),
                email=validated_data.get('email', ''),
                is_active=True
            )
            logger.info(f"Created new user: {username}")

    # Создаем Employee запись
    employee = Employee.objects.create(
        user=user,
        store=store,
        first_name=validated_data['first_name'],
        last_name=validated_data.get('last_name', ''),
        role=validated_data['role'],
        phone=validated_data.get('phone', ''),
        position=validated_data.get('position', ''),
        is_active=True
    )

    return {
        'employee': employee,
        'username': username or None,
        'password': password if not is_existing_user else None,
        'is_existing_user': is_existing_user
    }
```

---

## ✅ Итого

### Текущее поведение:
- ✅ Один User может иметь несколько Employee записей
- ✅ Каждая Employee запись в своей tenant схеме
- ❌ Нельзя добавить существующего сотрудника через API

### Рекомендуемое решение:
1. ✅ Обновить `CreateEmployeeSerializer.create()`
2. ✅ Добавить проверку безопасности
3. ✅ Автоматически определять: создавать User или использовать существующий
4. ✅ Возвращать флаг `is_existing_user` в ответе

### Преимущества:
- ✅ Один endpoint для всех случаев
- ✅ Безопасно (только свои сотрудники)
- ✅ Не нужно менять фронтенд
- ✅ Логично для владельца

---

**Статус:** Требуется реализация
**Приоритет:** Medium
**Время:** ~30 минут

---

## ✅ Реализовано!

**Дата реализации:** 2025-11-20

### Что сделано:

1. ✅ Обновлен `CreateEmployeeSerializer.create()` - автоматически определяет новый или существующий User
2. ✅ Добавлена проверка безопасности через search_path - владелец может добавить только своих сотрудников
3. ✅ Обновлена валидация - не требует password для существующих User
4. ✅ Обновлен `EmployeeViewSet.create()` - возвращает флаг `is_existing_user`
5. ✅ Протестировано - работает корректно

### Как использовать:

**Шаг 1: Создать сотрудника в первом магазине**
```bash
POST /api/users/employees/
X-Tenant-Key: store1_xxx
Body: {
  "username": "ivan_manager",
  "password": "secure123",  # Требуется для нового
  "first_name": "Иван",
  "role": "manager"
}

→ Response: {
    "status": "success",
    "message": "Сотрудник успешно создан",
    "data": {
      "is_existing_user": false,
      "credentials": {
        "username": "ivan_manager",
        "password": "secure123"
      }
    }
  }
```

**Шаг 2: Добавить в другой магазин (БЕЗ ПАРОЛЯ)**
```bash
POST /api/users/employees/
X-Tenant-Key: store2_xxx
Body: {
  "username": "ivan_manager",  # Тот же username
  # password НЕ нужен!
  "first_name": "Иван",
  "role": "cashier"  # Может быть другая роль
}

→ Response: {
    "status": "success",
    "message": "Сотрудник добавлен в магазин",
    "data": {
      "is_existing_user": true,
      "credentials": null  # Нет credentials для существующих
    }
  }
```

### Безопасность:

✅ Владелец может добавить только тех сотрудников, которые **уже работают в одном из его магазинов**
❌ Нельзя "украсть" сотрудников других владельцев

---

**Статус:** ✅ РЕАЛИЗОВАНО И ПРОТЕСТИРОВАНО
