# Frontend Quick Start - Интеграция с API

## Проблема и решение

### ❌ Было
```
POST /api/users/users/ → 405 Method Not Allowed
```

### ✅ Стало
```
POST /api/users/users/ → 201 Created (с tenant_key в заголовке)
```

---

## Быстрый старт (3 шага)

### Шаг 1: Настрой axios interceptor

```typescript
// src/utils/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// Добавляем токен и tenant_key ко всем запросам
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  const tenantKey = localStorage.getItem('tenant_key');

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // ВАЖНО: Добавляем X-Tenant-Key
  if (tenantKey) {
    config.headers['X-Tenant-Key'] = tenantKey;
  }

  return config;
});

// Обработка ошибок
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 403) {
      const message = error.response.data?.message;

      if (message?.includes('X-Tenant-Key')) {
        // Нет tenant_key - перенаправляем на выбор магазина
        window.location.href = '/select-store';
      } else if (message?.includes('нет доступа')) {
        // Нет прав
        alert('У вас нет доступа к этому ресурсу');
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Шаг 2: Логин и получение tenant_key

```typescript
// src/services/auth.ts
import api from '@/utils/api';

export const login = async (username: string, password: string) => {
  try {
    // 1. Логин
    const loginResponse = await api.post('/users/auth/login/', {
      username,
      password
    });

    const { access, refresh } = loginResponse.data.data;

    // Сохраняем токены
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);

    // 2. Получаем список магазинов
    const storesResponse = await api.get('/users/auth/my-stores/');
    const stores = storesResponse.data.data.stores;

    if (stores.length === 0) {
      throw new Error('У вас нет доступа ни к одному магазину');
    }

    // Сохраняем первый магазин (или даём выбрать)
    const defaultStore = stores[0];
    localStorage.setItem('tenant_key', defaultStore.tenant_key);
    localStorage.setItem('store_name', defaultStore.name);
    localStorage.setItem('user_role', defaultStore.role);

    return {
      success: true,
      stores,
      defaultStore
    };
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('tenant_key');
  localStorage.removeItem('store_name');
  localStorage.removeItem('user_role');
  window.location.href = '/login';
};
```

### Шаг 3: Используй API

```typescript
// src/services/users.ts
import api from '@/utils/api';

export const createUser = async (userData: any) => {
  const response = await api.post('/users/users/', userData);
  return response.data;
};

export const getUsers = async () => {
  const response = await api.get('/users/users/');
  return response.data;
};

export const searchUsers = async (name: string) => {
  const response = await api.get(`/users/users/?name=${name}`);
  return response.data;
};
```

---

## Полный пример (React)

### AuthContext.tsx
```typescript
import React, { createContext, useContext, useEffect, useState } from 'react';
import { login, logout } from '@/services/auth';

interface AuthContextType {
  isAuthenticated: boolean;
  user: any;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  currentStore: any;
}

const AuthContext = createContext<AuthContextType>(null!);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [currentStore, setCurrentStore] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const tenantKey = localStorage.getItem('tenant_key');
    const storeName = localStorage.getItem('store_name');

    if (token && tenantKey) {
      setIsAuthenticated(true);
      setCurrentStore({ tenant_key: tenantKey, name: storeName });
    }
  }, []);

  const handleLogin = async (username: string, password: string) => {
    const result = await login(username, password);
    setIsAuthenticated(true);
    setCurrentStore(result.defaultStore);
  };

  const handleLogout = () => {
    logout();
    setIsAuthenticated(false);
    setUser(null);
    setCurrentStore(null);
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        user,
        login: handleLogin,
        logout: handleLogout,
        currentStore
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
```

### CreateUserModal.tsx
```typescript
import React, { useState } from 'react';
import { createUser } from '@/services/users';

export const CreateUserModal = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'cashier',
    phone: '',
    position: ''
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await createUser(formData);
      console.log('User created:', result);
      onSuccess();
      onClose();
    } catch (err) {
      console.error('Error creating user:', err);

      if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else if (err.response?.data?.errors) {
        const errors = err.response.data.errors;
        const errorMessages = Object.values(errors).flat().join(', ');
        setError(errorMessages);
      } else {
        setError('Ошибка при создании пользователя');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal">
      <form onSubmit={handleSubmit}>
        <h2>Создать сотрудника</h2>

        {error && <div className="error">{error}</div>}

        <input
          type="text"
          placeholder="Логин"
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          required
        />

        <input
          type="password"
          placeholder="Пароль"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          required
        />

        <input
          type="text"
          placeholder="Имя"
          value={formData.first_name}
          onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
          required
        />

        <input
          type="text"
          placeholder="Фамилия"
          value={formData.last_name}
          onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
        />

        <select
          value={formData.role}
          onChange={(e) => setFormData({ ...formData, role: e.target.value })}
        >
          <option value="cashier">Кассир</option>
          <option value="manager">Менеджер</option>
          <option value="stockkeeper">Складчик</option>
        </select>

        <input
          type="tel"
          placeholder="+998901234567"
          value={formData.phone}
          onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
        />

        <input
          type="text"
          placeholder="Должность"
          value={formData.position}
          onChange={(e) => setFormData({ ...formData, position: e.target.value })}
        />

        <div className="buttons">
          <button type="button" onClick={onClose}>Отмена</button>
          <button type="submit" disabled={loading}>
            {loading ? 'Создание...' : 'Создать'}
          </button>
        </div>
      </form>
    </div>
  );
};
```

---

## Чеклист интеграции

### ✅ Перед деплоем проверь:

1. **Axios interceptor настроен**
   - [ ] Добавляет `Authorization: Bearer {token}`
   - [ ] Добавляет `X-Tenant-Key: {tenant_key}`
   - [ ] Обрабатывает ошибку 403

2. **Логин работает**
   - [ ] После логина получаем список магазинов
   - [ ] Сохраняем `tenant_key` в localStorage
   - [ ] Токен и tenant_key добавляются к запросам

3. **Создание пользователя работает**
   - [ ] `POST /api/users/users/` возвращает 201
   - [ ] Показываются правильные ошибки валидации
   - [ ] После создания пользователь появляется в списке

4. **Обработка ошибок**
   - [ ] Показывается сообщение если нет tenant_key
   - [ ] Показывается сообщение если нет прав
   - [ ] Ошибки валидации выводятся под полями формы

---

## Типичные ошибки

### Ошибка 1: "Не указан магазин"
```json
{
  "status": "error",
  "code": "forbidden",
  "message": "Не указан магазин. Добавьте заголовок X-Tenant-Key"
}
```

**Решение:**
```typescript
// Проверь что tenant_key сохраняется после логина
console.log('Tenant key:', localStorage.getItem('tenant_key'));

// Проверь что interceptor добавляет заголовок
api.interceptors.request.use(config => {
  console.log('Headers:', config.headers);
  return config;
});
```

### Ошибка 2: "У вас нет доступа"
```json
{
  "status": "error",
  "message": "У вас нет доступа к этому магазину"
}
```

**Причины:**
- Неправильный tenant_key
- У пользователя нет Employee записи для этого магазина

**Решение:**
```typescript
// Получи список доступных магазинов
const response = await api.get('/users/auth/my-stores/');
console.log('My stores:', response.data.data.stores);

// Проверь что используешь tenant_key из этого списка
```

### Ошибка 3: "Только владелец или менеджер"
```json
{
  "status": "error",
  "message": "Только владелец или менеджер может создавать сотрудников"
}
```

**Решение:**
- Войди как owner или manager
- Проверь роль: `localStorage.getItem('user_role')`

---

## FAQ

**Q: Нужно ли добавлять X-Tenant-Key к логину?**
A: Нет! Только к запросам после логина.

**Q: Где хранить tenant_key?**
A: В localStorage или sessionStorage.

**Q: Можно ли работать с несколькими магазинами одновременно?**
A: Да, но в разных вкладках браузера. В одной вкладке - один магазин.

**Q: Что делать если пользователь переключает магазин?**
A: Обнови tenant_key в localStorage и перезагрузи данные.

---

## Полезные ссылки

- [TENANT_GUIDE.md](TENANT_GUIDE.md) - Подробная документация по мультитенантности
- [USERS_API_GUIDE.md](USERS_API_GUIDE.md) - API для работы с пользователями
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Полная документация API
- [POSTMAN_GUIDE.md](POSTMAN_GUIDE.md) - Как тестировать в Postman

---

## Контакты

Если что-то не работает:
1. Проверь консоль браузера
2. Проверь Network tab в DevTools
3. Убедись что tenant_key есть в заголовках запроса
4. Проверь что роль пользователя правильная

Удачи! 🚀
