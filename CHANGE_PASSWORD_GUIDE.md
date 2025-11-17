# Изменение пароля сотрудника

## POST /api/users/users/{user_id}/change-password/

### Описание
Позволяет владельцу (owner) или менеджеру (manager) изменить пароль любого сотрудника в магазине.

### Права доступа
- ✅ **owner** - может менять пароли всех сотрудников
- ✅ **manager** - может менять пароли всех сотрудников
- ❌ **cashier** - не может менять пароли
- ❌ **stockkeeper** - не может менять пароли

---

## Запрос

### cURL
```bash
curl -X POST "http://localhost:8000/api/users/users/2/change-password/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-Key: YOUR_TENANT_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "NewSecurePass123!"
  }'
```

### JavaScript (fetch)
```javascript
const response = await fetch('http://localhost:8000/api/users/users/2/change-password/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'X-Tenant-Key': tenantKey,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    new_password: 'NewSecurePass123!'
  })
});

const data = await response.json();
console.log(data);
```

### Axios (React/Vue)
```javascript
import api from '@/utils/api';

const changeEmployeePassword = async (userId, newPassword) => {
  try {
    const response = await api.post(
      `/users/users/${userId}/change-password/`,
      { new_password: newPassword }
    );

    console.log('Успех:', response.data);
    return response.data;
  } catch (error) {
    console.error('Ошибка:', error.response?.data);
    throw error;
  }
};

// Использование
await changeEmployeePassword(2, 'NewSecurePass123!');
```

---

## Успешный ответ (200 OK)

```json
{
  "status": "success",
  "message": "Пароль для пользователя cashier1 успешно изменен",
  "data": {
    "user_id": 2,
    "username": "cashier1"
  }
}
```

---

## Ошибки

### 400 Bad Request - Пароль не указан
```json
{
  "status": "error",
  "code": "validation_error",
  "message": "Укажите новый пароль",
  "errors": {
    "new_password": ["Это поле обязательно"]
  }
}
```

### 400 Bad Request - Пароль слишком короткий
```json
{
  "status": "error",
  "code": "validation_error",
  "message": "Пароль слишком короткий",
  "errors": {
    "new_password": ["Пароль должен содержать минимум 8 символов"]
  }
}
```

### 403 Forbidden - Нет прав
```json
{
  "status": "error",
  "code": "forbidden",
  "message": "Только владелец или менеджер может менять пароли сотрудников"
}
```

### 404 Not Found - Сотрудник не найден
```json
{
  "status": "error",
  "code": "not_found",
  "message": "Сотрудник не найден в этом магазине"
}
```

---

## Полный пример в React компоненте

```typescript
// components/EmployeePasswordChange.tsx
import { useState } from 'react';
import api from '@/utils/api';

interface EmployeePasswordChangeProps {
  userId: number;
  username: string;
  onSuccess?: () => void;
}

export const EmployeePasswordChange = ({
  userId,
  username,
  onSuccess
}: EmployeePasswordChangeProps) => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Валидация на клиенте
    if (!newPassword) {
      setError('Введите новый пароль');
      return;
    }

    if (newPassword.length < 8) {
      setError('Пароль должен содержать минимум 8 символов');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }

    try {
      setLoading(true);

      const response = await api.post(
        `/users/users/${userId}/change-password/`,
        { new_password: newPassword }
      );

      alert(`✅ ${response.data.message}`);

      // Очистить форму
      setNewPassword('');
      setConfirmPassword('');

      // Вызвать callback
      if (onSuccess) {
        onSuccess();
      }
    } catch (error: any) {
      console.error('Ошибка изменения пароля:', error);

      if (error.response?.data) {
        const errorData = error.response.data;
        setError(errorData.message || 'Не удалось изменить пароль');
      } else {
        setError('Ошибка сети');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h3>Изменить пароль для: {username}</h3>

      <form onSubmit={handleChangePassword}>
        <div style={{ marginBottom: '10px' }}>
          <label>
            Новый пароль:
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Минимум 8 символов"
              style={{ display: 'block', width: '100%', padding: '8px', marginTop: '5px' }}
              disabled={loading}
            />
          </label>
        </div>

        <div style={{ marginBottom: '10px' }}>
          <label>
            Подтвердите пароль:
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Повторите пароль"
              style={{ display: 'block', width: '100%', padding: '8px', marginTop: '5px' }}
              disabled={loading}
            />
          </label>
        </div>

        {error && (
          <div style={{ color: 'red', marginBottom: '10px' }}>
            ❌ {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '10px 20px',
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Изменение...' : 'Изменить пароль'}
        </button>
      </form>
    </div>
  );
};
```

---

## Использование в списке сотрудников

```typescript
// components/EmployeeList.tsx
import { useState } from 'react';
import { EmployeePasswordChange } from './EmployeePasswordChange';

export const EmployeeList = () => {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState<{id: number, username: string} | null>(null);

  const handleOpenPasswordChange = (employee: any) => {
    setSelectedEmployee({
      id: employee.id,
      username: employee.username
    });
  };

  const handleClosePasswordChange = () => {
    setSelectedEmployee(null);
  };

  return (
    <div>
      <h2>Список сотрудников</h2>

      <table>
        <thead>
          <tr>
            <th>Имя</th>
            <th>Роль</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {employees.map((emp: any) => (
            <tr key={emp.id}>
              <td>{emp.full_name}</td>
              <td>{emp.employee_info?.role_display}</td>
              <td>
                <button onClick={() => handleOpenPasswordChange(emp)}>
                  Изменить пароль
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Модальное окно для смены пароля */}
      {selectedEmployee && (
        <div style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          backgroundColor: 'white',
          padding: '20px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
          zIndex: 1000
        }}>
          <EmployeePasswordChange
            userId={selectedEmployee.id}
            username={selectedEmployee.username}
            onSuccess={handleClosePasswordChange}
          />

          <button
            onClick={handleClosePasswordChange}
            style={{ marginTop: '10px' }}
          >
            Закрыть
          </button>
        </div>
      )}

      {/* Затемнение фона */}
      {selectedEmployee && (
        <div
          onClick={handleClosePasswordChange}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 999
          }}
        />
      )}
    </div>
  );
};
```

---

## Простая функция для быстрого использования

```typescript
// utils/employeeActions.ts
import api from '@/utils/api';

/**
 * Изменить пароль сотрудника
 */
export const changeEmployeePassword = async (
  userId: number,
  newPassword: string
): Promise<void> => {
  // Валидация
  if (!newPassword || newPassword.length < 8) {
    throw new Error('Пароль должен содержать минимум 8 символов');
  }

  try {
    const response = await api.post(
      `/users/users/${userId}/change-password/`,
      { new_password: newPassword }
    );

    return response.data;
  } catch (error: any) {
    if (error.response?.data?.message) {
      throw new Error(error.response.data.message);
    }
    throw error;
  }
};

// Использование с confirm dialog
export const promptChangePassword = async (userId: number, username: string) => {
  const newPassword = prompt(
    `Введите новый пароль для ${username}:\n(минимум 8 символов)`
  );

  if (!newPassword) {
    return; // Отменено
  }

  try {
    await changeEmployeePassword(userId, newPassword);
    alert(`✅ Пароль для ${username} успешно изменен!`);
  } catch (error: any) {
    alert(`❌ Ошибка: ${error.message}`);
  }
};
```

**Использование:**
```typescript
// В любом компоненте
import { promptChangePassword } from '@/utils/employeeActions';

<button onClick={() => promptChangePassword(employee.id, employee.username)}>
  Изменить пароль
</button>
```

---

## Требования к паролю

| Требование | Значение |
|------------|----------|
| Минимальная длина | 8 символов |
| Максимальная длина | Не ограничена |
| Обязательные символы | Нет (но рекомендуется использовать буквы, цифры и спецсимволы) |

**Рекомендации:**
- Используйте комбинацию заглавных и строчных букв
- Добавьте цифры
- Используйте спецсимволы (!@#$%^&*)
- Пример надежного пароля: `SecurePass123!`

---

## Проверка в Postman

### 1. Успешное изменение
```
POST http://localhost:8000/api/users/users/2/change-password/
Headers:
  Authorization: Bearer {{access_token}}
  X-Tenant-Key: {{tenant_key}}
  Content-Type: application/json

Body:
{
  "new_password": "NewPassword123!"
}

Ожидаемый результат: 200 OK
```

### 2. Короткий пароль (ошибка)
```
Body:
{
  "new_password": "short"
}

Ожидаемый результат: 400 Bad Request
{
  "status": "error",
  "message": "Пароль слишком короткий"
}
```

### 3. Без прав (кассир пытается сменить пароль)
```
Войдите как cashier, попробуйте изменить пароль

Ожидаемый результат: 403 Forbidden
{
  "status": "error",
  "message": "Только владелец или менеджер может менять пароли сотрудников"
}
```

---

## Резюме

### Эндпоинт
```
POST /api/users/users/{user_id}/change-password/
```

### Параметры
| Параметр | Тип | Обязательно | Описание |
|----------|-----|-------------|----------|
| `new_password` | string | ✅ Да | Новый пароль (минимум 8 символов) |

### Требуемые заголовки
- `Authorization: Bearer {token}`
- `X-Tenant-Key: {tenant_key}`

### Права доступа
- ✅ owner
- ✅ manager
- ❌ cashier
- ❌ stockkeeper

Готово! 🔐
