# 🔑 Tenant Key в каждом ответе

## Обзор

Все API ответы автоматически включают информацию о текущем магазине:
- `tenant_key` - ключ магазина
- `store_name` - название магазина
- `store_slug` - slug магазина

Это упрощает работу фронтенда - не нужно отдельно хранить и передавать tenant_key.

---

## Как это работает

### Middleware автоматически добавляет поля

В файле `core/middleware.py` функция `process_response()` автоматически добавляет информацию о магазине в каждый JSON ответ, если:
- Запрос содержит валидный X-Tenant-Key header
- Ответ имеет Content-Type: application/json
- Статус код < 400 (не ошибка)

```python
def process_response(self, request, response):
    # Добавляем tenant_key в JSON ответы
    if (hasattr(request, 'tenant') and request.tenant and
        response.get('Content-Type', '').startswith('application/json') and
        hasattr(response, 'data') and isinstance(response.data, dict)):

        if response.status_code < 400 and 'tenant_key' not in response.data:
            response.data['tenant_key'] = request.tenant.tenant_key
            response.data['store_name'] = request.tenant.name
            response.data['store_slug'] = request.tenant.slug
```

---

## Примеры ответов

### 1. Список продуктов

**Запрос:**
```bash
GET /api/products/products/
Headers:
  Authorization: Bearer {token}
  X-Tenant-Key: test_shop_4dfa7a5a
```

**Ответ:**
```json
{
  "count": 150,
  "next": null,
  "previous": null,
  "results": [...],
  "tenant_key": "test_shop_4dfa7a5a",    // ✅ Автоматически добавлено
  "store_name": "Тестовый Магазин",      // ✅ Автоматически добавлено
  "store_slug": "test_shop"              // ✅ Автоматически добавлено
}
```

### 2. Список продаж

**Запрос:**
```bash
GET /api/sales/sales/
Headers:
  Authorization: Bearer {token}
  X-Tenant-Key: magazin_2_abc123
```

**Ответ:**
```json
{
  "count": 45,
  "results": [...],
  "tenant_key": "magazin_2_abc123",      // ✅
  "store_name": "Магазин №2",            // ✅
  "store_slug": "magazin_2"              // ✅
}
```

### 3. Создание продажи

**Запрос:**
```bash
POST /api/sales/sales/
Headers:
  Authorization: Bearer {token}
  X-Tenant-Key: test_shop_4dfa7a5a
Body: {...}
```

**Ответ:**
```json
{
  "status": "success",
  "data": {
    "sale_id": 123,
    "total_amount": 50000,
    ...
  },
  "tenant_key": "test_shop_4dfa7a5a",    // ✅
  "store_name": "Тестовый Магазин",      // ✅
  "store_slug": "test_shop"              // ✅
}
```

### 4. Аналитика

**Запрос:**
```bash
GET /api/analytics/daily-sales-reports/
Headers:
  Authorization: Bearer {token}
  X-Tenant-Key: test_shop_4dfa7a5a
```

**Ответ:**
```json
{
  "count": 30,
  "results": [...],
  "tenant_key": "test_shop_4dfa7a5a",    // ✅
  "store_name": "Тестовый Магазин",      // ✅
  "store_slug": "test_shop"              // ✅
}
```

---

## Использование на фронтенде

### 1. Автоматическое определение магазина

```javascript
// Не нужно хранить tenant_key отдельно!
async function fetchProducts() {
  const response = await api.get('/products/products/', {
    headers: {
      'X-Tenant-Key': currentTenantKey
    }
  });

  const data = response.data;

  // Магазин автоматически определяется из ответа
  console.log('Магазин:', data.store_name);        // "Тестовый Магазин"
  console.log('Tenant Key:', data.tenant_key);     // "test_shop_4dfa7a5a"
  console.log('Slug:', data.store_slug);           // "test_shop"

  return data.results;
}
```

### 2. Отображение текущего магазина

```javascript
// После любого запроса можем показать название магазина
async function loadDashboard() {
  const sales = await api.get('/sales/sales/');

  // Обновляем UI с информацией о магазине
  document.getElementById('store-name').textContent = sales.data.store_name;
  document.getElementById('store-slug').textContent = sales.data.store_slug;

  return sales.data.results;
}
```

### 3. React Hook - автоматическое отслеживание магазина

```typescript
import { useState, useEffect } from 'react';
import { api } from './api';

interface ResponseWithStore<T> {
  tenant_key: string;
  store_name: string;
  store_slug: string;
  results?: T[];
  data?: any;
}

export const useApiWithStore = <T,>(url: string) => {
  const [data, setData] = useState<T[] | null>(null);
  const [storeInfo, setStoreInfo] = useState<{
    tenant_key: string;
    store_name: string;
    store_slug: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response: ResponseWithStore<T> = await api.get(url);

        // Сохраняем информацию о магазине
        setStoreInfo({
          tenant_key: response.tenant_key,
          store_name: response.store_name,
          store_slug: response.store_slug
        });

        // Сохраняем данные
        setData(response.results || response.data);

      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [url]);

  return { data, storeInfo, loading };
};

// Использование
function ProductsList() {
  const { data: products, storeInfo, loading } = useApiWithStore('/products/products/');

  if (loading) return <div>Загрузка...</div>;

  return (
    <div>
      <h2>Продукты магазина: {storeInfo?.store_name}</h2>
      <p>Tenant Key: {storeInfo?.tenant_key}</p>

      {products?.map(product => (
        <div key={product.id}>{product.name}</div>
      ))}
    </div>
  );
}
```

### 4. Мульти-магазинная аналитика (упрощенная)

```javascript
async function getMultiStoreAnalytics(stores, startDate, endDate) {
  // Запрашиваем аналитику для каждого магазина
  const analyticsPromises = stores.map(async (store) => {
    const response = await api.get(
      `/analytics/daily-sales-reports/period/?start_date=${startDate}&end_date=${endDate}`,
      {
        headers: { 'X-Tenant-Key': store.tenant_key }
      }
    );

    // В ответе уже есть tenant_key, store_name, store_slug!
    return {
      ...response.data,
      // Не нужно дублировать, уже есть в response.data:
      // tenant_key: response.data.tenant_key
      // store_name: response.data.store_name
      // store_slug: response.data.store_slug
    };
  });

  const analytics = await Promise.all(analyticsPromises);

  // Агрегируем
  const total = analytics.reduce((sum, a) => sum + (a.totals?.total_sales || 0), 0);

  return {
    total_sales: total,
    by_store: analytics.map(a => ({
      tenant_key: a.tenant_key,       // ✅ Из ответа API
      store_name: a.store_name,       // ✅ Из ответа API
      store_slug: a.store_slug,       // ✅ Из ответа API
      total_sales: a.totals?.total_sales || 0
    }))
  };
}
```

---

## Когда поля НЕ добавляются

1. **Ошибки (status >= 400):**
```json
{
  "status": "error",
  "message": "Product not found"
  // ❌ tenant_key НЕ добавляется в ошибки
}
```

2. **Запросы без X-Tenant-Key:**
```bash
GET /api/users/stores/
Headers:
  Authorization: Bearer {token}
  # НЕТ X-Tenant-Key
```

Ответ:
```json
{
  "count": 3,
  "stores": [...]
  // ❌ tenant_key НЕ добавляется (public endpoint)
}
```

3. **Не-JSON ответы:**
- HTML страницы
- Файлы (CSV, PDF)
- Binary данные

---

## Преимущества

✅ **Простота:** Фронтенд автоматически знает из какого магазина данные
✅ **Безопасность:** Подтверждение что данные из правильного магазина
✅ **Отладка:** Легко видеть tenant_key в каждом ответе
✅ **UI:** Можно показывать название магазина из любого ответа
✅ **Мультимагазинность:** Упрощает работу с несколькими магазинами

---

## Пример: Dashboard с автоопределением магазина

```tsx
import { useEffect, useState } from 'react';
import { api } from './api';

interface StoreInfo {
  tenant_key: string;
  store_name: string;
  store_slug: string;
}

export const Dashboard = () => {
  const [storeInfo, setStoreInfo] = useState<StoreInfo | null>(null);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    const loadDashboard = async () => {
      // Делаем любой запрос - получаем информацию о магазине автоматически
      const response = await api.get('/sales/sales/');

      // Сохраняем информацию о магазине
      setStoreInfo({
        tenant_key: response.data.tenant_key,
        store_name: response.data.store_name,
        store_slug: response.data.store_slug
      });

      setStats(response.data);
    };

    loadDashboard();
  }, []);

  if (!storeInfo) {
    return <div>Загрузка...</div>;
  }

  return (
    <div className="dashboard">
      {/* Хедер с информацией о магазине */}
      <header>
        <h1>{storeInfo.store_name}</h1>
        <p className="subtitle">
          Магазин: {storeInfo.store_slug} |
          Tenant: {storeInfo.tenant_key}
        </p>
      </header>

      {/* Остальной контент */}
      <div className="stats">
        <h2>Продажи: {stats?.count}</h2>
      </div>
    </div>
  );
};
```

---

## Проверка

```bash
# Получить токен
TOKEN=$(curl -s -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin_testshop", "password": "admin123"}' | jq -r '.access')

# Проверить что tenant_key добавляется
curl "http://localhost:8000/api/products/products/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a" | \
  jq '{tenant_key, store_name, store_slug, count}'
```

**Ожидаемый результат:**
```json
{
  "tenant_key": "test_shop_4dfa7a5a",
  "store_name": "Тестовый Магазин",
  "store_slug": "test_shop",
  "count": 150
}
```

---

**Дата внедрения:** 2025-11-20
**Версия API:** 1.0
**Затронутые файлы:** core/middleware.py (строки 124-150)
