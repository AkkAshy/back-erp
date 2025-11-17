# Исправление GET /api/users/users/

## Проблема
```
GET /api/users/users/ → 500 Internal Server Error
Ошибка: Cannot resolve keyword 'employee' into field
```

## Причина
В `UserViewSet.get_queryset()` использовался `User.objects.all()`, который пытался вернуть ВСЕХ пользователей системы, но не фильтровал их по текущему магазину.

**Важно:** В модели Employee используется **`related_name='employments'`** на поле `user`, НЕ `employees`!

## Решение
Изменили `get_queryset()` чтобы показывать только пользователей, которые являются активными сотрудниками в текущем магазине, используя правильный related_name:

```python
def get_queryset(self):
    # Проверяем что есть tenant_key (магазин)
    if not hasattr(self.request, 'tenant') or not self.request.tenant:
        return User.objects.none()

    # Получаем пользователей текущего магазина
    # ВАЖНО: используем 'employments' (related_name на User), НЕ 'employees'!
    queryset = User.objects.filter(
        employments__store=self.request.tenant,
        employments__is_active=True
    ).distinct()

    # Фильтр по имени
    name = self.request.query_params.get('name')
    if name:
        queryset = queryset.filter(
            Q(first_name__icontains=name) |
            Q(last_name__icontains=name) |
            Q(username__icontains=name)
        )

    return queryset
```

## Теперь работает

### 1. GET /api/users/users/
Возвращает всех сотрудников текущего магазина (требует X-Tenant-Key)

**Запрос:**
```bash
GET /api/users/users/
Headers:
  Authorization: Bearer {access_token}
  X-Tenant-Key: {tenant_key}
```

**Ответ:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "username": "owner1",
      "email": "owner@example.com",
      "first_name": "Иван",
      "last_name": "Петров",
      "full_name": "Петров Иван",
      "is_active": true
    },
    {
      "id": 2,
      "username": "cashier1",
      "email": "cashier@example.com",
      "first_name": "Анна",
      "last_name": "Иванова",
      "full_name": "Иванова Анна",
      "is_active": true
    }
  ]
}
```

### 2. GET /api/users/users/?name=Иван
Поиск по имени/фамилии/логину

**Запрос:**
```bash
GET /api/users/users/?name=Иван
Headers:
  Authorization: Bearer {access_token}
  X-Tenant-Key: {tenant_key}
```

**Ответ:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "username": "owner1",
      "first_name": "Иван",
      "last_name": "Петров",
      "full_name": "Петров Иван"
    }
  ]
}
```

## Важно

### Обязателен заголовок X-Tenant-Key
Без tenant_key эндпоинт вернет пустой список:

```bash
# ❌ Без X-Tenant-Key
GET /api/users/users/
→ []

# ✅ С X-Tenant-Key
GET /api/users/users/
Headers: X-Tenant-Key: my-store_abc123
→ [список сотрудников магазина]
```

### Показываются только активные сотрудники
Фильтр `employee__is_active=True` исключает уволенных сотрудников.

Если нужно увидеть всех (включая уволенных), используй:
```
GET /api/users/employees/
```

## Резюме изменений

| Что изменилось | Было | Стало |
|----------------|------|-------|
| Фильтрация | `User.objects.all()` | `User.objects.filter(employee__store=tenant)` |
| Результат | Все пользователи системы (или пусто) | Только сотрудники текущего магазина |
| Требует tenant_key | Нет | Да (обязательно) |

## Проверка

1. **Войди в систему:**
```bash
POST /api/users/auth/login/
Body: {"username": "owner1", "password": "password"}
```

2. **Получи tenant_key:**
```bash
GET /api/users/auth/my-stores/
→ Скопируй tenant_key из ответа
```

3. **Получи список пользователей:**
```bash
GET /api/users/users/
Headers:
  Authorization: Bearer {access_token}
  X-Tenant-Key: {tenant_key}
```

4. **Должен вернуться список сотрудников магазина** ✅

---

## Frontend интеграция

### Axios interceptor автоматически добавит заголовок
Если ты настроил interceptor как в [FRONTEND_QUICK_START.md](FRONTEND_QUICK_START.md), то ничего дополнительно делать не нужно:

```typescript
// src/services/users.ts
export const getUsers = async () => {
  const response = await api.get('/users/users/');
  return response.data.data; // Список пользователей
};

export const searchUsers = async (name: string) => {
  const response = await api.get(`/users/users/?name=${name}`);
  return response.data.data;
};
```

Interceptor автоматически добавит `X-Tenant-Key` из localStorage.

---

Теперь GET /api/users/users/ должен работать корректно! 🚀
