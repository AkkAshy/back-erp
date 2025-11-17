# Фронтенд: Как обновлять сотрудников

## ❌ Неправильно (что делает сейчас фронтенд)

```typescript
// Это НЕ РАБОТАЕТ!
await api.patch(`/users/users/${userId}/`, {
  role: 'manager',
  phone: '+998901234567'
});
```

**Ошибка:** `405 Method Not Allowed`

## ✅ Правильно

```typescript
// Используйте /update-employee/ endpoint
await api.patch(`/users/users/${userId}/update-employee/`, {
  role: 'manager',
  phone: '+998901234567',
  position: 'Менеджер',
  is_active: true
});
```

---

## Исправление в коде фронтенда

### Найди файл: `usersApi.ts` или `users.service.ts`

#### Было:
```typescript
export const updateUser = async (userId: number, data: any) => {
  const response = await api.patch(`/users/users/${userId}/`, data);
  return response.data;
};
```

#### Стало:
```typescript
export const updateUser = async (userId: number, data: any) => {
  // Изменили URL - добавили /update-employee/
  const response = await api.patch(`/users/users/${userId}/update-employee/`, data);
  return response.data;
};
```

---

## Полный пример API методов

```typescript
// src/services/users.ts
import api from '@/utils/api';

// Получить список всех сотрудников
export const getUsers = async () => {
  const response = await api.get('/users/users/');
  return response.data;
};

// Поиск по имени
export const searchUsers = async (name: string) => {
  const response = await api.get(`/users/users/?name=${name}`);
  return response.data;
};

// Создать сотрудника
export const createUser = async (data: {
  username: string;
  password: string;
  first_name: string;
  last_name?: string;
  email?: string;
  role: string;
  phone?: string;
  position?: string;
}) => {
  const response = await api.post('/users/users/', data);
  return response.data;
};

// ✅ Обновить сотрудника - ИСПОЛЬЗУЙ ЭТОТ ENDPOINT!
export const updateUser = async (
  userId: number,
  data: {
    role?: string;
    phone?: string;
    position?: string;
    is_active?: boolean;
  }
) => {
  const response = await api.patch(
    `/users/users/${userId}/update-employee/`,
    data
  );
  return response.data;
};

// Деактивировать сотрудника
export const deactivateUser = async (userId: number) => {
  return updateUser(userId, { is_active: false });
};

// Активировать сотрудника
export const activateUser = async (userId: number) => {
  return updateUser(userId, { is_active: true });
};

// Изменить роль
export const changeUserRole = async (userId: number, role: string) => {
  return updateUser(userId, { role });
};
```

---

## Пример использования в компоненте

```typescript
// components/UsersList.tsx
import { updateUser } from '@/services/users';

const UsersList = () => {
  const [users, setUsers] = useState([]);

  const handleRoleChange = async (userId: number, newRole: string) => {
    try {
      // ✅ Правильный вызов
      const result = await updateUser(userId, { role: newRole });

      console.log('✅ Успех:', result);
      // result.data.employee содержит обновленные данные

      // Перезагрузить список
      loadUsers();
    } catch (error) {
      console.error('❌ Ошибка:', error);
      alert('Не удалось обновить роль');
    }
  };

  const handleToggleActive = async (userId: number, currentStatus: boolean) => {
    try {
      await updateUser(userId, { is_active: !currentStatus });
      alert('Статус обновлен');
      loadUsers();
    } catch (error) {
      console.error('Ошибка:', error);
    }
  };

  return (
    <div>
      {users.map(user => (
        <div key={user.id}>
          <span>{user.full_name}</span>
          <span>{user.employee_info?.role_display}</span>

          <button onClick={() => handleRoleChange(user.id, 'manager')}>
            Сделать менеджером
          </button>

          <button onClick={() => handleToggleActive(
            user.id,
            user.employee_info?.is_active
          )}>
            {user.employee_info?.is_active ? 'Деактивировать' : 'Активировать'}
          </button>
        </div>
      ))}
    </div>
  );
};
```

---

## Проверка

### 1. Проверь URL в Network tab
Открой DevTools → Network → найди запрос PATCH

**Должно быть:**
```
PATCH http://localhost:8000/api/users/users/2/update-employee/
```

**НЕ должно быть:**
```
PATCH http://localhost:8000/api/users/users/2/  ❌
```

### 2. Проверь ответ от сервера

**Успех (200 OK):**
```json
{
  "status": "success",
  "message": "Информация о сотруднике обновлена",
  "data": {
    "employee": {
      "id": 2,
      "role": "manager",
      "role_display": "Менеджер",
      "phone": "+998909999999",
      "position": "Старший менеджер",
      "is_active": true
    }
  }
}
```

**Ошибка (405):**
```json
{
  "status": "error",
  "code": "method_not_allowed",
  "message": "Для обновления сотрудника используйте PATCH /api/users/users/{id}/update-employee/",
  "hint": "Попробуйте: PATCH /api/users/users/2/update-employee/"
}
```

---

## Быстрый чеклист

- [ ] Изменил URL в `updateUser()` на `/users/users/${id}/update-employee/`
- [ ] Проверил что передаю правильные поля: `role`, `phone`, `position`, `is_active`
- [ ] Убедился что `X-Tenant-Key` добавляется автоматически через interceptor
- [ ] Протестировал в браузере - запрос идет на правильный URL
- [ ] Ответ возвращает 200 OK и обновленные данные

---

## Резюме

Меняй только **одну строку** в коде:

```diff
- const response = await api.patch(`/users/users/${userId}/`, data);
+ const response = await api.patch(`/users/users/${userId}/update-employee/`, data);
```

Готово! 🚀
