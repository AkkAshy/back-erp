# Поле "sex" (пол) для сотрудников

## Описание
Добавлено новое поле `sex` в модель Employee для хранения пола сотрудника.

## Возможные значения

| Значение | Отображение | Описание |
|----------|-------------|----------|
| `male` | Мужской | Мужчина |
| `female` | Женский | Женщина |
| `null` | - | Не указано |

---

## GET /api/users/users/ - Получить список сотрудников

Теперь в `employee_info` добавлены два новых поля:

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "first_name": "Иван",
  "last_name": "Петров",
  "full_name": "Иван Петров",
  "employee_info": {
    "id": 1,
    "role": "owner",
    "role_display": "Владелец",
    "phone": "+998901234567",
    "position": "Генеральный директор",
    "sex": "male",              // ← Новое поле
    "sex_display": "Мужской",   // ← Новое поле
    "is_active": true,
    "hired_at": "2025-11-17",
    "photo": null
  }
}
```

---

## PATCH /api/users/users/{id}/update-employee/ - Обновить пол сотрудника

### Запрос

#### cURL
```bash
curl -X PATCH "http://localhost:8000/api/users/users/2/update-employee/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-Key: YOUR_TENANT_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sex": "male"
  }'
```

#### Axios (JavaScript)
```javascript
import api from '@/utils/api';

// Установить пол
const updateEmployeeSex = async (userId, sex) => {
  const response = await api.patch(
    `/users/users/${userId}/update-employee/`,
    { sex: sex }
  );
  return response.data;
};

// Использование
await updateEmployeeSex(2, 'male');    // Мужской
await updateEmployeeSex(2, 'female');  // Женский
```

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
      "role": "cashier",
      "role_display": "Кассир",
      "phone": "+998901234567",
      "photo": null,
      "position": "Кассир",
      "sex": "female",
      "sex_display": "Женский",
      "is_active": true,
      "hired_at": "2025-11-17",
      "created_at": "2025-11-17T15:56:04.236550+05:00"
    }
  }
}
```

---

## POST /api/users/users/ - Создать сотрудника с полом

При создании нового сотрудника теперь можно указать пол:

```bash
curl -X POST "http://localhost:8000/api/users/users/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-Key: YOUR_TENANT_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ivan_manager",
    "password": "SecurePass123!",
    "first_name": "Иван",
    "last_name": "Петров",
    "email": "ivan@example.com",
    "role": "manager",
    "phone": "+998901234567",
    "position": "Менеджер зала",
    "sex": "male"
  }'
```

---

## Примеры для фронтенда

### React компонент с выбором пола

```typescript
// components/EmployeeSexSelector.tsx
import { useState } from 'react';

interface EmployeeSexSelectorProps {
  currentSex?: string;
  userId: number;
  onUpdate?: () => void;
}

export const EmployeeSexSelector = ({
  currentSex,
  userId,
  onUpdate
}: EmployeeSexSelectorProps) => {
  const [sex, setSex] = useState(currentSex || '');
  const [loading, setLoading] = useState(false);

  const handleChange = async (newSex: string) => {
    try {
      setLoading(true);
      setSex(newSex);

      await api.patch(`/users/users/${userId}/update-employee/`, {
        sex: newSex
      });

      alert('Пол обновлен');
      if (onUpdate) onUpdate();
    } catch (error) {
      console.error('Ошибка обновления пола:', error);
      alert('Не удалось обновить пол');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <label>Пол:</label>
      <select
        value={sex}
        onChange={(e) => handleChange(e.target.value)}
        disabled={loading}
        style={{ marginLeft: '10px', padding: '5px' }}
      >
        <option value="">Не указан</option>
        <option value="male">Мужской</option>
        <option value="female">Женский</option>
      </select>
    </div>
  );
};
```

### Использование в таблице сотрудников

```typescript
// components/EmployeeTable.tsx
import { EmployeeSexSelector } from './EmployeeSexSelector';

export const EmployeeTable = () => {
  const [employees, setEmployees] = useState([]);

  const loadEmployees = async () => {
    const response = await api.get('/users/users/');
    setEmployees(response.data.results);
  };

  return (
    <table>
      <thead>
        <tr>
          <th>Имя</th>
          <th>Email</th>
          <th>Роль</th>
          <th>Пол</th>
          <th>Телефон</th>
        </tr>
      </thead>
      <tbody>
        {employees.map((emp: any) => (
          <tr key={emp.id}>
            <td>{emp.full_name}</td>
            <td>{emp.email}</td>
            <td>{emp.employee_info?.role_display}</td>
            <td>
              <EmployeeSexSelector
                currentSex={emp.employee_info?.sex}
                userId={emp.id}
                onUpdate={loadEmployees}
              />
            </td>
            <td>{emp.employee_info?.phone}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
```

### Простое отображение пола

```typescript
// Просто показать пол (без редактирования)
const EmployeeCard = ({ employee }) => {
  const sexDisplay = employee.employee_info?.sex_display || 'Не указан';
  const sexIcon = employee.employee_info?.sex === 'male' ? '👨' :
                  employee.employee_info?.sex === 'female' ? '👩' :
                  '👤';

  return (
    <div className="employee-card">
      <h3>{employee.full_name}</h3>
      <p>
        {sexIcon} Пол: {sexDisplay}
      </p>
      <p>Роль: {employee.employee_info?.role_display}</p>
      <p>Телефон: {employee.employee_info?.phone}</p>
    </div>
  );
};
```

---

## Примеры запросов

### 1. Установить пол "мужской"

```javascript
await api.patch('/users/users/2/update-employee/', {
  sex: 'male'
});
```

### 2. Установить пол "женский"

```javascript
await api.patch('/users/users/2/update-employee/', {
  sex: 'female'
});
```

### 3. Сбросить пол (установить null)

```javascript
await api.patch('/users/users/2/update-employee/', {
  sex: null
});
```

### 4. Обновить несколько полей одновременно

```javascript
await api.patch('/users/users/2/update-employee/', {
  sex: 'male',
  phone: '+998901234567',
  position: 'Старший менеджер'
});
```

---

## Фильтрация по полу (если понадобится в будущем)

Если нужно будет добавить фильтрацию по полу в списке сотрудников:

```javascript
// Backend: добавить в views.py
def get_queryset(self):
    queryset = super().get_queryset()

    # Фильтр по полу
    sex = self.request.query_params.get('sex')
    if sex:
        queryset = queryset.filter(employments__sex=sex)

    return queryset

// Frontend: использование
const getMaleEmployees = async () => {
  const response = await api.get('/users/users/?sex=male');
  return response.data.results;
};

const getFemaleEmployees = async () => {
  const response = await api.get('/users/users/?sex=female');
  return response.data.results;
};
```

---

## Валидация

Поле `sex` принимает только следующие значения:
- `"male"` - мужской
- `"female"` - женский
- `null` или не указано - пол не указан

Любое другое значение будет отклонено с ошибкой валидации.

---

## Миграция базы данных

Миграция уже применена. Поле добавлено в таблицу `users_employee`:

```sql
ALTER TABLE users_employee
ADD COLUMN sex VARCHAR(10) NULL;
```

Для существующих сотрудников значение `sex` будет `NULL` (не указано).

---

## Резюме

### Новые поля в API:
- `employee_info.sex` - значение пола (`male`, `female`, `null`)
- `employee_info.sex_display` - отображаемое название (`"Мужской"`, `"Женский"`, `null`)

### Обновление пола:
```javascript
PATCH /users/users/{id}/update-employee/
Body: { "sex": "male" } или { "sex": "female" }
```

### Права доступа:
- ✅ Owner и Manager могут обновлять пол сотрудников
- ❌ Cashier и Stockkeeper не могут

Готово! 🚀
