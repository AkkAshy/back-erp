# 🔐 Данные для входа в систему

## Тестовый пользователь

```
Username: testuser
Password: test123456
Email: test@test.com
```

## API Login

### Endpoint:
```
POST /api/users/auth/login/
```

### Request Body:
```json
{
  "username": "testuser",
  "password": "test123456"
}
```

⚠️ **Важно:** Используйте `username`, а НЕ `email`!

### cURL пример:
```bash
curl -X POST 'http://localhost:8000/api/users/auth/login/' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "testuser",
    "password": "test123456"
  }'
```

### Успешный ответ:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 4,
    "username": "testuser",
    "email": "test@test.com",
    "full_name": "Test User"
  },
  "available_stores": [
    {
      "id": 1,
      "name": "admin",
      "slug": "admin",
      "tenant_key": "admin_1a12e47a",
      "role": "owner",
      "role_display": "Владелец",
      "permissions": [
        "view_all",
        "create_all",
        "update_all",
        "delete_all"
      ]
    }
  ],
  "default_store": {
    "tenant_key": "admin_1a12e47a",
    "name": "admin",
    "role": "owner"
  }
}
```

## Использование токена

После успешного входа используйте полученный токен в заголовках всех API запросов:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Tenant-Key: admin_1a12e47a
```

### Пример запроса с токеном:

```bash
curl 'http://localhost:8000/api/products/products/' \
  -H 'Authorization: Bearer {access_token}' \
  -H 'X-Tenant-Key: admin_1a12e47a'
```

## Frontend примеры

### TypeScript/JavaScript:

```typescript
// Login
const login = async (username: string, password: string) => {
  const response = await fetch('http://localhost:8000/api/users/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password })
  });

  if (!response.ok) {
    throw new Error('Login failed');
  }

  const data = await response.json();

  // Сохраняем токены
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  localStorage.setItem('tenant_key', data.default_store.tenant_key);

  return data;
};

// Использование в запросах
const fetchProducts = async () => {
  const token = localStorage.getItem('access_token');
  const tenantKey = localStorage.getItem('tenant_key');

  const response = await fetch('http://localhost:8000/api/products/products/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Tenant-Key': tenantKey
    }
  });

  return response.json();
};
```

### React Hook:

```typescript
import { useState } from 'react';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const login = async (username: string, password: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/users/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();

      // Сохраняем данные
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      localStorage.setItem('tenant_key', data.default_store.tenant_key);
      localStorage.setItem('user', JSON.stringify(data.user));

      setUser(data.user);

      return data;

    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('tenant_key');
    localStorage.removeItem('user');
    setUser(null);
  };

  return { user, login, logout, loading, error };
};
```

### Компонент Login:

```typescript
import { useState } from 'react';
import { useAuth } from './hooks/useAuth';

export const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, loading, error } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      await login(username, password);
      // Перенаправление после успешного входа
      window.location.href = '/dashboard';
    } catch (err) {
      console.error('Login error:', err);
    }
  };

  return (
    <div className="login-page">
      <form onSubmit={handleSubmit}>
        <h1>Вход в систему</h1>

        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          required
        />

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          required
        />

        <button type="submit" disabled={loading}>
          {loading ? 'Вход...' : 'Войти'}
        </button>

        {error && <div className="error">{error}</div>}
      </form>

      <div className="test-credentials">
        <p>Тестовые данные:</p>
        <p>Username: testuser</p>
        <p>Password: test123456</p>
      </div>
    </div>
  );
};
```

## Другие пользователи

### Admin (superuser):
```
Email: asdmi@asdads.com
Username: admin
Password: (неизвестен - нужно сбросить)
```

Чтобы сбросить пароль для admin:
```bash
python manage.py shell << 'EOF'
from users.models import User
user = User.objects.get(username='admin')
user.set_password('newpassword123')
user.save()
print(f"Password reset for {user.username}")
EOF
```

## Tenant Key

Для всех запросов используйте:
```
X-Tenant-Key: admin_1a12e47a
```

## Резюме

✅ **Username:** testuser
✅ **Password:** test123456
✅ **Tenant Key:** admin_1a12e47a
✅ **Role:** owner (владелец)
✅ **Permissions:** Полный доступ ко всем операциям

Готово! 🎉
