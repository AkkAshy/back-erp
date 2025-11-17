# Мультитенантность - Работа с магазинами

## Обзор

Система поддерживает **мультитенантность** - один пользователь может работать с несколькими магазинами. Каждый запрос должен указывать, с каким магазином вы работаете.

---

## Как это работает

### 1. Регистрация
При регистрации создается:
- **User** (пользователь Django)
- **Store** (магазин)
- **Employee** (запись сотрудника с ролью `owner`)

### 2. Вход в систему
При логине вы получаете:
- **Access Token** - JWT токен для аутентификации
- **Список магазинов** - все магазины, к которым у вас есть доступ

### 3. Работа с API
Для каждого запроса нужно указать **заголовок X-Tenant-Key** с ключом магазина.

---

## Получение списка магазинов

### GET `/api/users/auth/my-stores/`

Возвращает список всех магазинов, к которым у вас есть доступ.

**Response:**
```json
{
  "status": "success",
  "data": {
    "stores": [
      {
        "id": 1,
        "name": "Test Store",
        "slug": "test-store",
        "tenant_key": "abc123def456",
        "role": "owner",
        "is_active": true
      }
    ]
  }
}
```

**Важно:** Сохраните `tenant_key` - он нужен для всех последующих запросов!

---

## Работа с запросами

### Добавьте заголовок X-Tenant-Key

Все запросы к API (кроме аутентификации) требуют этот заголовок:

```
X-Tenant-Key: abc123def456
```

### Пример в Postman

1. Сделай Login
2. Получи список магазинов через `/api/users/auth/my-stores/`
3. Скопируй `tenant_key` из ответа
4. В Postman:
   - Открой коллекцию
   - Variables
   - Добавь переменную `tenant_key` со значением из ответа
5. Во всех запросах добавь заголовок:
   ```
   Key: X-Tenant-Key
   Value: {{tenant_key}}
   ```

### Пример в JavaScript/TypeScript

```typescript
import axios from 'axios';

// После логина сохрани tenant_key
const tenantKey = 'abc123def456';

// Создай axios instance с заголовком
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'X-Tenant-Key': tenantKey
  }
});

// Теперь все запросы будут с tenant_key
api.get('/products/products/');
api.post('/users/users/', { ... });
```

---

## Типичные ошибки

### Ошибка: "Не указан магазин. Добавьте заголовок X-Tenant-Key"

```json
{
  "status": "error",
  "code": "forbidden",
  "message": "Не указан магазин. Добавьте заголовок X-Tenant-Key",
  "errors": {}
}
```

**Решение:**
1. Получи список магазинов: `GET /api/users/auth/my-stores/`
2. Скопируй `tenant_key`
3. Добавь заголовок `X-Tenant-Key: <твой_ключ>` во все запросы

### Ошибка: "У вас нет доступа к этому магазину"

```json
{
  "status": "error",
  "code": "forbidden",
  "message": "У вас нет доступа к этому магазину",
  "errors": {}
}
```

**Решение:**
1. Проверь что ты используешь правильный `tenant_key`
2. Убедись что у тебя есть доступ к этому магазину через `/api/users/auth/my-stores/`

### Ошибка: "У вас нет прав для создания сотрудников"

Эта ошибка больше НЕ появляется, если:
1. Ты указал правильный `X-Tenant-Key`
2. У тебя роль `owner` или `manager`

---

## Workflow для фронтенда

### 1. Логин
```typescript
const response = await axios.post('/api/users/auth/login/', {
  username: 'owner',
  password: 'password'
});

const accessToken = response.data.data.access;
localStorage.setItem('access_token', accessToken);
```

### 2. Получение магазинов
```typescript
const response = await axios.get('/api/users/auth/my-stores/', {
  headers: {
    Authorization: `Bearer ${accessToken}`
  }
});

const stores = response.data.data.stores;
const defaultStore = stores[0]; // Берём первый магазин

// Сохраняем tenant_key
localStorage.setItem('tenant_key', defaultStore.tenant_key);
localStorage.setItem('store_name', defaultStore.name);
```

### 3. Настройка axios instance
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// Добавляем interceptor для всех запросов
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  const tenantKey = localStorage.getItem('tenant_key');

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  if (tenantKey) {
    config.headers['X-Tenant-Key'] = tenantKey;
  }

  return config;
});

export default api;
```

### 4. Использование API
```typescript
import api from './api';

// Теперь все запросы автоматически включают токен и tenant_key
const createUser = async (userData) => {
  const response = await api.post('/users/users/', userData);
  return response.data;
};

const getProducts = async () => {
  const response = await api.get('/products/products/');
  return response.data;
};
```

---

## Переключение между магазинами

Если у пользователя несколько магазинов:

```typescript
const switchStore = (store) => {
  localStorage.setItem('tenant_key', store.tenant_key);
  localStorage.setItem('store_name', store.name);

  // Обнови axios instance
  api.defaults.headers['X-Tenant-Key'] = store.tenant_key;

  // Перезагрузи данные
  window.location.reload();
};
```

---

## Проверка в Postman

### Шаг 1: Получи токен
```
POST {{base_url}}/api/users/auth/login/
Body: { "username": "owner", "password": "password" }
```

Токен сохранится автоматически в `{{access_token}}`.

### Шаг 2: Получи tenant_key
```
GET {{base_url}}/api/users/auth/my-stores/
Authorization: Bearer {{access_token}}
```

Скопируй `tenant_key` из ответа.

### Шаг 3: Добавь tenant_key в коллекцию
1. Нажми на коллекцию (три точки)
2. **Edit**
3. **Variables**
4. Добавь:
   - Key: `tenant_key`
   - Value: `<скопированный_ключ>`

### Шаг 4: Добавь заголовок во все запросы
1. Нажми на коллекцию (три точки)
2. **Edit**
3. **Headers**
4. Добавь:
   - Key: `X-Tenant-Key`
   - Value: `{{tenant_key}}`

Теперь все запросы в коллекции будут автоматически использовать tenant_key!

---

## FAQ

**Q: Зачем нужен X-Tenant-Key, если уже есть JWT токен?**
A: JWT токен идентифицирует пользователя, а X-Tenant-Key указывает, с каким магазином он работает. Один пользователь может быть сотрудником нескольких магазинов.

**Q: Можно ли добавить tenant_key в JWT токен?**
A: Технически можно, но это плохая практика. Пользователь может работать с разными магазинами в разных вкладках браузера.

**Q: Где хранить tenant_key на фронтенде?**
A: В `localStorage` или `sessionStorage`. При переключении магазина просто обновляй это значение.

**Q: Что если пользователь забыл добавить X-Tenant-Key?**
A: Получит ошибку 403 с сообщением "Не указан магазин. Добавьте заголовок X-Tenant-Key".

**Q: Можно ли работать без X-Tenant-Key?**
A: Только эндпоинты аутентификации работают без него:
- `/api/users/auth/register/`
- `/api/users/auth/login/`
- `/api/users/auth/my-stores/`

Все остальные эндпоинты требуют X-Tenant-Key.

---

## Примеры интеграции

### React
```typescript
// src/utils/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  const tenantKey = localStorage.getItem('tenant_key');

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  if (tenantKey) {
    config.headers['X-Tenant-Key'] = tenantKey;
  }

  return config;
});

export default api;
```

### Vue
```typescript
// src/plugins/axios.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL,
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  const tenantKey = localStorage.getItem('tenant_key');

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  if (tenantKey) {
    config.headers['X-Tenant-Key'] = tenantKey;
  }

  return config;
});

export default api;
```

### Angular
```typescript
// src/app/services/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    let headers = new HttpHeaders();

    const token = localStorage.getItem('access_token');
    const tenantKey = localStorage.getItem('tenant_key');

    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }

    if (tenantKey) {
      headers = headers.set('X-Tenant-Key', tenantKey);
    }

    return headers;
  }

  get(url: string) {
    return this.http.get(`${this.baseUrl}${url}`, {
      headers: this.getHeaders()
    });
  }

  post(url: string, data: any) {
    return this.http.post(`${this.baseUrl}${url}`, data, {
      headers: this.getHeaders()
    });
  }
}
```

---

## Резюме

1. ✅ После логина получи список магазинов
2. ✅ Сохрани `tenant_key` первого магазина
3. ✅ Добавь заголовок `X-Tenant-Key` во все запросы
4. ✅ Если нужно переключить магазин - обнови `tenant_key`

Теперь создание пользователей будет работать! 🎉
