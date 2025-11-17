# 📡 API Examples - ERP v2 (Schema-based Multitenancy)

Примеры запросов к API с использованием **X-Tenant-Key** для мультитенантности.

---

## 🏗️ Архитектура

**ВАЖНО:** В этой версии используется **схемная мультитенантность**:
- JWT токены **НЕ содержат** `store_id`
- Каждый магазин имеет уникальный `tenant_key` (например: `magazin-ivanova_a4b3c2d1`)
- Для доступа к данным магазина добавляйте заголовок: `X-Tenant-Key: <tenant_key>`
- PostgreSQL схемы обеспечивают полную изоляцию данных

---

## 🔐 Аутентификация

### 1. Регистрация владельца магазина

**Endpoint:** `POST /api/users/auth/register/`

```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "owner1",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Иван",
    "last_name": "Иванов",
    "email": "ivan@example.com",
    "owner_phone": "+998901234567",
    "store_name": "Магазин Иванова",
    "store_slug": "magazin-ivanova",
    "store_description": "Продажа одежды премиум класса",
    "store_address": "г. Ташкент, ул. Навои, 25",
    "store_phone": "+998901234567"
  }'
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Регистрация успешна",
  "data": {
    "user": {
      "id": 1,
      "username": "owner1",
      "email": "ivan@example.com",
      "full_name": "Иван Иванов"
    },
    "store": {
      "id": 1,
      "name": "Магазин Иванова",
      "slug": "magazin-ivanova",
      "tenant_key": "magazin-ivanova_a4b3c2d1",
      "description": "Продажа одежды премиум класса"
    },
    "employee": {
      "id": 1,
      "role": "owner",
      "role_display": "Владелец",
      "permissions": ["view_all", "create_all", "update_all", "delete_all", ...]
    },
    "tokens": {
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
  }
}
```

**Python:**
```python
import requests

url = "http://127.0.0.1:8000/api/users/auth/register/"
data = {
    "username": "owner1",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Иван",
    "last_name": "Иванов",
    "email": "ivan@example.com",
    "store_name": "Магазин Иванова",
}

response = requests.post(url, json=data)
result = response.json()

# Сохраняем токены и tenant_key
access_token = result['data']['tokens']['access']
refresh_token = result['data']['tokens']['refresh']
tenant_key = result['data']['store']['tenant_key']  # ВАЖНО!

print(f"Access Token: {access_token}")
print(f"Tenant Key: {tenant_key}")
```

---

### 2. Вход в систему

**Endpoint:** `POST /api/users/auth/login/`

```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "owner1",
    "password": "SecurePass123!"
  }'
```

**Ответ:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "owner1",
    "email": "ivan@example.com",
    "full_name": "Иван Иванов"
  },
  "available_stores": [
    {
      "id": 1,
      "name": "Магазин Иванова",
      "slug": "magazin-ivanova",
      "tenant_key": "magazin-ivanova_a4b3c2d1",
      "role": "owner",
      "role_display": "Владелец",
      "permissions": ["view_all", "create_all", "update_all", "delete_all"]
    },
    {
      "id": 2,
      "name": "Второй Магазин",
      "slug": "vtoroi-magazin",
      "tenant_key": "vtoroi-magazin_x7y8z9a0",
      "role": "manager",
      "role_display": "Менеджер",
      "permissions": ["view_all", "create_all", "update_all"]
    }
  ],
  "default_store": {
    "tenant_key": "magazin-ivanova_a4b3c2d1",
    "name": "Магазин Иванова",
    "role": "owner"
  }
}
```

**Python:**
```python
import requests

url = "http://127.0.0.1:8000/api/users/auth/login/"
data = {
    "username": "owner1",
    "password": "SecurePass123!"
}

response = requests.post(url, json=data)
result = response.json()

access_token = result['access']
refresh_token = result['refresh']

# Получаем tenant_key первого магазина
tenant_key = result['available_stores'][0]['tenant_key']

print(f"Access Token: {access_token}")
print(f"Tenant Key: {tenant_key}")
```

---

### 3. Обновление токена

**Endpoint:** `POST /api/users/auth/token/refresh/`

```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

**Python:**
```python
import requests

url = "http://127.0.0.1:8000/api/users/auth/token/refresh/"
data = {
    "refresh": refresh_token
}

response = requests.post(url, json=data)
result = response.json()

new_access_token = result['access']
```

---

### 4. Информация о текущем пользователе

**Endpoint:** `GET /api/users/auth/me/`

**ВАЖНО:** Требует заголовок `X-Tenant-Key`

```bash
curl -X GET http://127.0.0.1:8000/api/users/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-Key: magazin-ivanova_a4b3c2d1"
```

**Python:**
```python
import requests

url = "http://127.0.0.1:8000/api/users/auth/me/"
headers = {
    "Authorization": f"Bearer {access_token}",
    "X-Tenant-Key": tenant_key  # ОБЯЗАТЕЛЬНО!
}

response = requests.get(url, headers=headers)
user_info = response.json()

print(user_info)
```

---

### 5. Список доступных магазинов

**Endpoint:** `GET /api/users/auth/my-stores/`

```bash
curl -X GET http://127.0.0.1:8000/api/users/auth/my-stores/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Python:**
```python
import requests

url = "http://127.0.0.1:8000/api/users/auth/my-stores/"
headers = {
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(url, headers=headers)
stores = response.json()['data']

for store in stores:
    print(f"Store: {store['name']}, Tenant Key: {store['tenant_key']}")
```

---

## 🏪 Работа с данными магазина

### Использование X-Tenant-Key

Все запросы к данным магазина (товары, продажи, клиенты и т.д.) **ОБЯЗАТЕЛЬНО** должны содержать заголовок `X-Tenant-Key`:

```bash
curl -X GET http://127.0.0.1:8000/api/inventory/products/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-Key: magazin-ivanova_a4b3c2d1"
```

### Переключение между магазинами

**НЕ требуется новый токен!** Просто меняйте значение `X-Tenant-Key`:

```python
# Работаем с первым магазином
headers_store1 = {
    "Authorization": f"Bearer {access_token}",
    "X-Tenant-Key": "magazin-ivanova_a4b3c2d1"
}

response = requests.get("http://127.0.0.1:8000/api/inventory/products/", headers=headers_store1)
products_store1 = response.json()

# Переключаемся на второй магазин
headers_store2 = {
    "Authorization": f"Bearer {access_token}",
    "X-Tenant-Key": "vtoroi-magazin_x7y8z9a0"  # Другой tenant_key
}

response = requests.get("http://127.0.0.1:8000/api/inventory/products/", headers=headers_store2)
products_store2 = response.json()  # Товары второго магазина
```

---

## 🔧 Полезные паттерны

### Класс для работы с API

```python
import requests
from typing import Optional, Dict, Any


class ERPClient:
    """Клиент для работы с ERP v2 API (Schema-based multitenancy)"""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.tenant_key: Optional[str] = None
        self.available_stores: list = []

    def _get_headers(self, include_tenant: bool = False) -> Dict[str, str]:
        """Получить заголовки для запросов"""
        headers = {"Content-Type": "application/json"}

        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        if include_tenant and self.tenant_key:
            headers["X-Tenant-Key"] = self.tenant_key

        return headers

    def register(self, username: str, password: str, first_name: str,
                 store_name: str, **kwargs) -> Dict[str, Any]:
        """Регистрация нового владельца магазина"""
        url = f"{self.base_url}/api/users/auth/register/"
        data = {
            "username": username,
            "password": password,
            "password_confirm": password,
            "first_name": first_name,
            "store_name": store_name,
            **kwargs
        }

        response = requests.post(url, json=data)
        response.raise_for_status()

        result = response.json()
        self.access_token = result['data']['tokens']['access']
        self.refresh_token = result['data']['tokens']['refresh']
        self.tenant_key = result['data']['store']['tenant_key']

        return result

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Вход в систему"""
        url = f"{self.base_url}/api/users/auth/login/"
        data = {"username": username, "password": password}

        response = requests.post(url, json=data)
        response.raise_for_status()

        result = response.json()
        self.access_token = result['access']
        self.refresh_token = result['refresh']
        self.available_stores = result['available_stores']

        # Устанавливаем первый магазин как текущий
        if self.available_stores:
            self.tenant_key = self.available_stores[0]['tenant_key']

        return result

    def refresh_access_token(self) -> str:
        """Обновить access токен"""
        url = f"{self.base_url}/api/users/auth/token/refresh/"
        data = {"refresh": self.refresh_token}

        response = requests.post(url, json=data)
        response.raise_for_status()

        result = response.json()
        self.access_token = result['access']

        return self.access_token

    def switch_store(self, tenant_key: str):
        """Переключиться на другой магазин"""
        if not any(s['tenant_key'] == tenant_key for s in self.available_stores):
            raise ValueError(f"Tenant key {tenant_key} not in available stores")

        self.tenant_key = tenant_key

    def get_me(self) -> Dict[str, Any]:
        """Получить информацию о текущем пользователе"""
        url = f"{self.base_url}/api/users/auth/me/"
        response = requests.get(url, headers=self._get_headers(include_tenant=True))
        response.raise_for_status()

        return response.json()['data']

    def get_my_stores(self) -> list:
        """Получить список доступных магазинов"""
        url = f"{self.base_url}/api/users/auth/my-stores/"
        response = requests.get(url, headers=self._get_headers(include_tenant=False))
        response.raise_for_status()

        self.available_stores = response.json()['data']
        return self.available_stores


# Использование
if __name__ == "__main__":
    client = ERPClient()

    # Регистрация
    client.register(
        username="test_owner",
        password="TestPass123!",
        first_name="Тест",
        store_name="Тестовый Магазин"
    )

    print(f"Registered! Tenant Key: {client.tenant_key}")

    # Получить информацию о пользователе
    user_info = client.get_me()
    print(f"Logged in as: {user_info['user']['full_name']}")
    print(f"Store: {user_info['store']['name']}")
    print(f"Role: {user_info['employee']['role']}")

    # Список магазинов
    stores = client.get_my_stores()
    for store in stores:
        print(f"Store: {store['name']} (Tenant Key: {store['tenant_key']})")

    # Переключение между магазинами (если их несколько)
    if len(client.available_stores) > 1:
        second_store_key = client.available_stores[1]['tenant_key']
        client.switch_store(second_store_key)
        print(f"Switched to: {client.tenant_key}")
```

---

## 📱 React/React Native пример

```typescript
// api/client.ts
import axios, { AxiosInstance } from 'axios';

class ERPApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private tenantKey: string | null = null;
  private availableStores: any[] = [];

  constructor(baseURL: string = 'http://127.0.0.1:8000') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Interceptor для автоматического добавления токенов
    this.client.interceptors.request.use((config) => {
      if (this.accessToken) {
        config.headers.Authorization = `Bearer ${this.accessToken}`;
      }

      // Добавляем X-Tenant-Key если установлен
      if (this.tenantKey) {
        config.headers['X-Tenant-Key'] = this.tenantKey;
      }

      return config;
    });

    // Interceptor для обновления токена при 401
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const newToken = await this.refreshAccessToken();
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // Redirect to login
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  async register(data: RegisterData) {
    const response = await this.client.post('/api/users/auth/register/', data);
    this.setTokens(
      response.data.data.tokens.access,
      response.data.data.tokens.refresh
    );
    this.tenantKey = response.data.data.store.tenant_key;
    return response.data;
  }

  async login(username: string, password: string) {
    const response = await this.client.post('/api/users/auth/login/', {
      username,
      password,
    });
    this.setTokens(response.data.access, response.data.refresh);
    this.availableStores = response.data.available_stores;

    // Устанавливаем первый магазин как текущий
    if (this.availableStores.length > 0) {
      this.tenantKey = this.availableStores[0].tenant_key;
    }

    return response.data;
  }

  async refreshAccessToken() {
    const response = await this.client.post('/api/users/auth/token/refresh/', {
      refresh: this.refreshToken,
    });
    this.accessToken = response.data.access;
    return this.accessToken;
  }

  switchStore(tenantKey: string) {
    const store = this.availableStores.find(s => s.tenant_key === tenantKey);
    if (!store) {
      throw new Error(`Tenant key ${tenantKey} not found in available stores`);
    }
    this.tenantKey = tenantKey;
  }

  async getMe() {
    const response = await this.client.get('/api/users/auth/me/');
    return response.data.data;
  }

  async getMyStores() {
    const response = await this.client.get('/api/users/auth/my-stores/');
    this.availableStores = response.data.data;
    return response.data.data;
  }

  private setTokens(access: string, refresh: string) {
    this.accessToken = access;
    this.refreshToken = refresh;

    // Сохраняем в AsyncStorage для React Native
    // или localStorage для веб
  }

  getCurrentTenantKey(): string | null {
    return this.tenantKey;
  }

  getAvailableStores() {
    return this.availableStores;
  }
}

export const apiClient = new ERPApiClient();
```

---

## 🎯 Важные моменты

1. **X-Tenant-Key обязателен** для всех запросов к данным магазина
2. **JWT токены НЕ содержат store_id** - они универсальны для всех магазинов пользователя
3. **Переключение между магазинами** - просто меняйте `X-Tenant-Key`, новый токен не нужен
4. **Регистрация и вход** не требуют `X-Tenant-Key` (работают в public схеме)
5. **tenant_key уникален** и генерируется автоматически (формат: `{slug}_{hash}`)

---

**Готово! 🎉**
