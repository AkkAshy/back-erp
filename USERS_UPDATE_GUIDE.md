# Обновление информации о сотрудниках

## GET /api/users/users/ - Список сотрудников с employee_info

### Описание
Возвращает список всех активных сотрудников текущего магазина с полной информацией, включая роль, телефон и позицию.

### Запрос
```bash
GET /api/users/users/
Headers:
  Authorization: Bearer {access_token}
  X-Tenant-Key: {tenant_key}
```

### Ответ
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "first_name": "Иван",
      "last_name": "Петров",
      "full_name": "Иван Петров",
      "is_active": true,
      "date_joined": "2025-11-17T11:38:28.234407+05:00",
      "employee_info": {
        "id": 1,
        "role": "owner",
        "role_display": "Владелец",
        "phone": "+998901234567",
        "position": "Генеральный директор",
        "is_active": true,
        "hired_at": "2025-11-17T11:38:28.234407+05:00",
        "photo": null
      }
    },
    {
      "id": 2,
      "username": "cashier1",
      "email": "cashier@example.com",
      "first_name": "Анна",
      "last_name": "Смирнова",
      "full_name": "Анна Смирнова",
      "is_active": true,
      "date_joined": "2025-11-17T15:56:04.236550+05:00",
      "employee_info": {
        "id": 2,
        "role": "cashier",
        "role_display": "Кассир",
        "phone": "+998901234568",
        "position": "Кассир",
        "is_active": true,
        "hired_at": "2025-11-17T15:56:04.236550+05:00",
        "photo": null
      }
    }
  ]
}
```

### Фильтрация по имени
```bash
GET /api/users/users/?name=Иван
```

Ищет по `first_name`, `last_name` и `username`.

---

## PATCH /api/users/users/{user_id}/update-employee/ - Обновление сотрудника

### Описание
Обновляет информацию о сотруднике (роль, телефон, позиция, статус).
Доступно только для владельца (owner) и менеджера (manager).

### Запрос
```bash
PATCH /api/users/users/2/update-employee/
Headers:
  Authorization: Bearer {access_token}
  X-Tenant-Key: {tenant_key}
  Content-Type: application/json

Body:
{
  "role": "manager",
  "phone": "+998909999999",
  "position": "Старший кассир",
  "is_active": true
}
```

### Параметры
Все поля опциональны - обновляются только те, которые указаны:

| Поле | Тип | Описание | Возможные значения |
|------|-----|----------|-------------------|
| `role` | string | Роль сотрудника | `owner`, `manager`, `cashier`, `stockkeeper` |
| `phone` | string | Телефон | Формат: `+998XXXXXXXXX` |
| `position` | string | Должность | Любая строка |
| `is_active` | boolean | Активен ли сотрудник | `true` / `false` |

### Успешный ответ (200 OK)
```json
{
  "status": "success",
  "message": "Информация о сотруднике обновлена",
  "data": {
    "employee": {
      "id": 2,
      "user": 2,
      "full_name": "Анна Смирнова",
      "username": "cashier1",
      "email": "cashier@example.com",
      "store": 1,
      "role": "manager",
      "role_display": "Менеджер",
      "phone": "+998909999999",
      "photo": null,
      "position": "Старший кассир",
      "is_active": true,
      "hired_at": "2025-11-17T15:56:04.236550+05:00",
      "created_at": "2025-11-17T15:56:04.236550+05:00"
    }
  }
}
```

### Ошибки

#### 403 Forbidden - Нет прав
```json
{
  "status": "error",
  "code": "forbidden",
  "message": "Только владелец или менеджер может обновлять сотрудников"
}
```

#### 404 Not Found - Сотрудник не найден
```json
{
  "status": "error",
  "code": "not_found",
  "message": "Сотрудник не найден в этом магазине"
}
```

#### 403 Forbidden - Нет tenant_key
```json
{
  "status": "error",
  "code": "forbidden",
  "message": "Не указан магазин. Добавьте заголовок X-Tenant-Key"
}
```

---

## Frontend примеры

### React + Axios

#### Получить список сотрудников
```typescript
// src/services/users.ts
import api from '@/utils/api';

export const getUsers = async () => {
  const response = await api.get('/users/users/');
  return response.data;
};

export const searchUsers = async (name: string) => {
  const response = await api.get(`/users/users/?name=${name}`);
  return response.data;
};
```

#### Обновить сотрудника
```typescript
export const updateEmployee = async (userId: number, data: {
  role?: string;
  phone?: string;
  position?: string;
  is_active?: boolean;
}) => {
  const response = await api.patch(`/users/users/${userId}/update-employee/`, data);
  return response.data;
};
```

#### Использование в компоненте
```typescript
// components/EmployeeList.tsx
import { useState, useEffect } from 'react';
import { getUsers, updateEmployee } from '@/services/users';

export const EmployeeList = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadEmployees();
  }, []);

  const loadEmployees = async () => {
    try {
      setLoading(true);
      const data = await getUsers();
      setEmployees(data.results);
    } catch (error) {
      console.error('Error loading employees:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRole = async (userId: number, newRole: string) => {
    try {
      await updateEmployee(userId, { role: newRole });
      alert('Роль обновлена');
      loadEmployees(); // Перезагрузить список
    } catch (error) {
      console.error('Error updating role:', error);
      alert('Ошибка при обновлении');
    }
  };

  const handleToggleActive = async (userId: number, isActive: boolean) => {
    try {
      await updateEmployee(userId, { is_active: !isActive });
      alert(isActive ? 'Сотрудник деактивирован' : 'Сотрудник активирован');
      loadEmployees();
    } catch (error) {
      console.error('Error toggling active:', error);
    }
  };

  return (
    <div>
      <h2>Список сотрудников</h2>
      {loading && <p>Загрузка...</p>}

      <table>
        <thead>
          <tr>
            <th>Имя</th>
            <th>Email</th>
            <th>Роль</th>
            <th>Телефон</th>
            <th>Должность</th>
            <th>Статус</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {employees.map((employee) => (
            <tr key={employee.id}>
              <td>{employee.full_name}</td>
              <td>{employee.email}</td>
              <td>{employee.employee_info?.role_display}</td>
              <td>{employee.employee_info?.phone}</td>
              <td>{employee.employee_info?.position}</td>
              <td>
                {employee.employee_info?.is_active ? 'Активен' : 'Неактивен'}
              </td>
              <td>
                <button onClick={() => handleUpdateRole(employee.id, 'manager')}>
                  Сделать менеджером
                </button>
                <button
                  onClick={() => handleToggleActive(
                    employee.id,
                    employee.employee_info?.is_active
                  )}
                >
                  {employee.employee_info?.is_active ? 'Деактивировать' : 'Активировать'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

---

## Postman примеры

### 1. Получить список сотрудников
```
GET http://localhost:8000/api/users/users/
Headers:
  Authorization: Bearer {{access_token}}
  X-Tenant-Key: {{tenant_key}}
```

### 2. Поиск по имени
```
GET http://localhost:8000/api/users/users/?name=Иван
Headers:
  Authorization: Bearer {{access_token}}
  X-Tenant-Key: {{tenant_key}}
```

### 3. Изменить роль сотрудника
```
PATCH http://localhost:8000/api/users/users/2/update-employee/
Headers:
  Authorization: Bearer {{access_token}}
  X-Tenant-Key: {{tenant_key}}
  Content-Type: application/json

Body:
{
  "role": "manager"
}
```

### 4. Обновить телефон и должность
```
PATCH http://localhost:8000/api/users/users/2/update-employee/
Headers:
  Authorization: Bearer {{access_token}}
  X-Tenant-Key: {{tenant_key}}
  Content-Type: application/json

Body:
{
  "phone": "+998901234567",
  "position": "Старший менеджер"
}
```

### 5. Деактивировать сотрудника
```
PATCH http://localhost:8000/api/users/users/2/update-employee/
Headers:
  Authorization: Bearer {{access_token}}
  X-Tenant-Key: {{tenant_key}}
  Content-Type: application/json

Body:
{
  "is_active": false
}
```

---

## Роли и права

| Роль | Может просматривать | Может создавать | Может обновлять | Может удалять |
|------|-------------------|----------------|----------------|--------------|
| **owner** | Все сотрудники | ✅ Да | ✅ Да | ✅ Да |
| **manager** | Все сотрудники | ✅ Да | ✅ Да | ❌ Нет |
| **cashier** | Все сотрудники | ❌ Нет | ❌ Нет | ❌ Нет |
| **stockkeeper** | Все сотрудники | ❌ Нет | ❌ Нет | ❌ Нет |

---

## Резюме

### Что добавлено:
1. ✅ Поле `employee_info` в GET /api/users/users/ с ролью, телефоном, позицией
2. ✅ Endpoint для обновления: PATCH /api/users/users/{id}/update-employee/
3. ✅ Права доступа: только owner/manager могут обновлять
4. ✅ Частичное обновление: можно обновить только нужные поля

### Использование:
- **Просмотр**: GET /api/users/users/ - получить всех сотрудников с employee_info
- **Поиск**: GET /api/users/users/?name=имя
- **Обновление**: PATCH /api/users/users/{id}/update-employee/ - обновить роль/телефон/позицию

Все работает! 🚀
