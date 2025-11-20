# 📊 Мульти-магазинная аналитика - Фронтенд подход

## Концепция

Вместо одного сложного endpoint, который переключает схемы на бэкенде, используем **простой подход на фронтенде**:

1. Получить список магазинов пользователя
2. Для каждого магазина запросить аналитику с его X-Tenant-Key
3. Агрегировать данные на фронтенде

## Преимущества

✅ **Простота:** Не нужно переключать схемы на бэкенде
✅ **Правильная изоляция:** Каждый запрос использует правильную tenant схему
✅ **Параллельность:** Можно запрашивать аналитику всех магазинов параллельно
✅ **Точность:** Данные гарантированно из правильных схем
✅ **Масштабируемость:** Легко кэшировать на уровне CDN/API Gateway

---

## Алгоритм

### 1. Получить список магазинов

```javascript
const stores = await fetch('/api/users/stores/my-stores-with-credentials/', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

**Ответ:**
```json
{
  "status": "success",
  "data": {
    "count": 3,
    "stores": [
      {
        "id": 2,
        "name": "Тестовый Магазин",
        "tenant_key": "test_shop_4dfa7a5a",
        "staff_credentials": { ... }
      },
      {
        "id": 8,
        "name": "Магазин №2",
        "tenant_key": "magazin_2_abc123",
        "staff_credentials": { ... }
      }
    ]
  }
}
```

### 2. Параллельно запросить аналитику для каждого магазина

```javascript
const analyticsPromises = stores.data.stores.map(store =>
  fetch(`/api/analytics/daily-sales-reports/period/?start_date=2025-11-01&end_date=2025-11-20`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Tenant-Key': store.tenant_key  // 🔑 Ключевой момент!
    }
  })
  .then(r => r.json())
  .then(data => ({
    store_id: store.id,
    store_name: store.name,
    store_slug: store.slug,
    tenant_key: store.tenant_key,
    analytics: data
  }))
);

const storesAnalytics = await Promise.all(analyticsPromises);
```

### 3. Агрегировать данные на фронтенде

```javascript
const aggregated = {
  total_stores: storesAnalytics.length,
  total_sales: 0,
  total_sales_count: 0,
  total_items_sold: 0,
  by_store: []
};

storesAnalytics.forEach(({ store_id, store_name, tenant_key, analytics }) => {
  const totals = analytics.totals || {};

  // Добавляем к общим итогам
  aggregated.total_sales += totals.total_sales || 0;
  aggregated.total_sales_count += totals.total_count || 0;
  aggregated.total_items_sold += totals.total_items || 0;

  // Добавляем в разбивку
  aggregated.by_store.push({
    store_id,
    store_name,
    tenant_key,
    total_sales: totals.total_sales || 0,
    sales_count: totals.total_count || 0,
    avg_sale: totals.avg_sale || 0
  });
});

// Сортируем по убыванию продаж
aggregated.by_store.sort((a, b) => b.total_sales - a.total_sales);
```

---

## Полный пример

### JavaScript функция

```javascript
async function getMultiStoreAnalytics(startDate, endDate) {
  const token = localStorage.getItem('access_token');

  try {
    // 1. Получаем список магазинов
    const storesResponse = await fetch('/api/users/stores/my-stores-with-credentials/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const storesData = await storesResponse.json();
    const stores = storesData.data.stores;

    if (!stores || stores.length === 0) {
      return {
        total_stores: 0,
        total_sales: 0,
        by_store: []
      };
    }

    // 2. Параллельно запрашиваем аналитику для каждого магазина
    const analyticsPromises = stores.map(async (store) => {
      try {
        const response = await fetch(
          `/api/analytics/daily-sales-reports/period/?start_date=${startDate}&end_date=${endDate}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'X-Tenant-Key': store.tenant_key
            }
          }
        );
        const data = await response.json();

        return {
          store_id: store.id,
          store_name: store.name,
          store_slug: store.slug,
          tenant_key: store.tenant_key,
          address: store.address,
          city: store.city,
          analytics: data,
          error: null
        };
      } catch (error) {
        console.error(`Error fetching analytics for ${store.name}:`, error);
        return {
          store_id: store.id,
          store_name: store.name,
          store_slug: store.slug,
          tenant_key: store.tenant_key,
          error: error.message,
          analytics: null
        };
      }
    });

    const storesAnalytics = await Promise.all(analyticsPromises);

    // 3. Агрегируем данные
    const aggregated = {
      total_stores: storesAnalytics.length,
      period: { start_date: startDate, end_date: endDate },
      aggregated: {
        total_sales: 0,
        total_sales_count: 0,
        total_discount: 0,
        total_items_sold: 0
      },
      by_store: []
    };

    storesAnalytics.forEach((storeData) => {
      if (storeData.error || !storeData.analytics) {
        // Добавляем магазин с ошибкой
        aggregated.by_store.push({
          store_id: storeData.store_id,
          store_name: storeData.store_name,
          tenant_key: storeData.tenant_key,
          error: storeData.error || 'No data',
          total_sales: 0,
          sales_count: 0
        });
        return;
      }

      const totals = storeData.analytics.totals || {};

      // Суммируем общие итоги
      aggregated.aggregated.total_sales += totals.total_sales || 0;
      aggregated.aggregated.total_sales_count += totals.total_count || 0;
      aggregated.aggregated.total_discount += totals.total_discount || 0;
      aggregated.aggregated.total_items_sold += totals.total_items || 0;

      // Добавляем в разбивку по магазинам
      aggregated.by_store.push({
        store_id: storeData.store_id,
        store_name: storeData.store_name,
        store_slug: storeData.store_slug,
        tenant_key: storeData.tenant_key,
        address: storeData.address,
        city: storeData.city,
        total_sales: totals.total_sales || 0,
        sales_count: totals.total_count || 0,
        total_discount: totals.total_discount || 0,
        total_items_sold: totals.total_items || 0,
        avg_sale: totals.avg_sale || 0
      });
    });

    // Вычисляем средний чек
    if (aggregated.aggregated.total_sales_count > 0) {
      aggregated.aggregated.avg_sale_amount =
        aggregated.aggregated.total_sales / aggregated.aggregated.total_sales_count;
    } else {
      aggregated.aggregated.avg_sale_amount = 0;
    }

    // Сортируем магазины по убыванию продаж
    aggregated.by_store.sort((a, b) => b.total_sales - a.total_sales);

    return aggregated;

  } catch (error) {
    console.error('Error getting multi-store analytics:', error);
    throw error;
  }
}

// Использование
const analytics = await getMultiStoreAnalytics('2025-11-01', '2025-11-20');
console.log('📊 Аналитика по всем магазинам:', analytics);
```

---

## React Hook

```typescript
import { useState, useEffect } from 'react';
import { api } from './api';

interface StoreAnalytics {
  store_id: number;
  store_name: string;
  store_slug: string;
  tenant_key: string;
  total_sales: number;
  sales_count: number;
  avg_sale: number;
  error?: string;
}

interface AggregatedAnalytics {
  total_stores: number;
  period: {
    start_date: string;
    end_date: string;
  };
  aggregated: {
    total_sales: number;
    total_sales_count: number;
    avg_sale_amount: number;
  };
  by_store: StoreAnalytics[];
}

export const useMultiStoreAnalytics = (startDate: string, endDate: string) => {
  const [analytics, setAnalytics] = useState<AggregatedAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      // 1. Получаем список магазинов
      const storesResponse = await api.get('/users/stores/my-stores-with-credentials/');
      const stores = storesResponse.data.data.stores;

      if (!stores || stores.length === 0) {
        setAnalytics({
          total_stores: 0,
          period: { start_date: startDate, end_date: endDate },
          aggregated: { total_sales: 0, total_sales_count: 0, avg_sale_amount: 0 },
          by_store: []
        });
        return;
      }

      // 2. Параллельно запрашиваем аналитику
      const analyticsPromises = stores.map(async (store: any) => {
        try {
          const response = await api.get(
            `/analytics/daily-sales-reports/period/?start_date=${startDate}&end_date=${endDate}`,
            {
              headers: { 'X-Tenant-Key': store.tenant_key }
            }
          );

          const totals = response.data.totals || {};

          return {
            store_id: store.id,
            store_name: store.name,
            store_slug: store.slug,
            tenant_key: store.tenant_key,
            total_sales: totals.total_sales || 0,
            sales_count: totals.total_count || 0,
            avg_sale: totals.avg_sale || 0,
            error: null
          };
        } catch (err: any) {
          return {
            store_id: store.id,
            store_name: store.name,
            store_slug: store.slug,
            tenant_key: store.tenant_key,
            total_sales: 0,
            sales_count: 0,
            avg_sale: 0,
            error: err.message
          };
        }
      });

      const storesAnalytics = await Promise.all(analyticsPromises);

      // 3. Агрегируем
      const totalSales = storesAnalytics.reduce((sum, s) => sum + s.total_sales, 0);
      const totalCount = storesAnalytics.reduce((sum, s) => sum + s.sales_count, 0);

      setAnalytics({
        total_stores: storesAnalytics.length,
        period: { start_date: startDate, end_date: endDate },
        aggregated: {
          total_sales: totalSales,
          total_sales_count: totalCount,
          avg_sale_amount: totalCount > 0 ? totalSales / totalCount : 0
        },
        by_store: storesAnalytics.sort((a, b) => b.total_sales - a.total_sales)
      });

    } catch (err: any) {
      setError(err.message || 'Ошибка загрузки аналитики');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [startDate, endDate]);

  return { analytics, loading, error, refetch: fetchAnalytics };
};
```

---

## React компонент

```tsx
import { useState } from 'react';
import { useMultiStoreAnalytics } from './hooks/useMultiStoreAnalytics';

export const MultiStoreDashboard = () => {
  const [period, setPeriod] = useState({
    start: '2025-11-01',
    end: '2025-11-20'
  });

  const { analytics, loading, error } = useMultiStoreAnalytics(
    period.start,
    period.end
  );

  if (loading) {
    return <div className="loading">Загрузка аналитики...</div>;
  }

  if (error) {
    return <div className="error">Ошибка: {error}</div>;
  }

  if (!analytics) {
    return null;
  }

  return (
    <div className="dashboard">
      <h1>Аналитика по всем магазинам</h1>

      {/* Общие итоги */}
      <div className="totals">
        <div className="stat">
          <h3>Магазинов</h3>
          <div className="value">{analytics.total_stores}</div>
        </div>
        <div className="stat">
          <h3>Общие продажи</h3>
          <div className="value">
            {analytics.aggregated.total_sales.toLocaleString()} сум
          </div>
        </div>
        <div className="stat">
          <h3>Количество чеков</h3>
          <div className="value">
            {analytics.aggregated.total_sales_count}
          </div>
        </div>
        <div className="stat">
          <h3>Средний чек</h3>
          <div className="value">
            {analytics.aggregated.avg_sale_amount.toLocaleString()} сум
          </div>
        </div>
      </div>

      {/* Разбивка по магазинам */}
      <div className="stores">
        <h2>По магазинам</h2>
        {analytics.by_store.map((store, index) => (
          <div key={store.store_id} className="store-card">
            <div className="rank">#{index + 1}</div>
            <div className="info">
              <h3>{store.store_name}</h3>
              {store.error ? (
                <p className="error">⚠️ {store.error}</p>
              ) : (
                <div className="stats">
                  <span>Продажи: {store.total_sales.toLocaleString()}</span>
                  <span>Чеков: {store.sales_count}</span>
                  <span>Средний чек: {store.avg_sale.toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## Производительность

### Параллельные запросы

```javascript
// ✅ Хорошо: Параллельные запросы
const analytics = await Promise.all(
  stores.map(store => fetchAnalytics(store.tenant_key))
);

// ❌ Плохо: Последовательные запросы
for (const store of stores) {
  const analytics = await fetchAnalytics(store.tenant_key);
}
```

### Кэширование

```javascript
// Кэшируем результаты на 5 минут
const cache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 минут

async function getCachedAnalytics(tenantKey, startDate, endDate) {
  const cacheKey = `${tenantKey}_${startDate}_${endDate}`;
  const cached = cache.get(cacheKey);

  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }

  const data = await fetchAnalytics(tenantKey, startDate, endDate);
  cache.set(cacheKey, { data, timestamp: Date.now() });

  return data;
}
```

---

## Сравнение подходов

| Характеристика | Backend Aggregation | Frontend Aggregation |
|----------------|---------------------|----------------------|
| **Сложность бэкенда** | Высокая (переключение схем) | Низкая (стандартные запросы) |
| **Сложность фронтенда** | Низкая | Средняя (агрегация) |
| **Производительность** | Зависит от кол-ва магазинов | Параллельные запросы быстрее |
| **Кэширование** | Сложное | Простое (на уровне браузера/CDN) |
| **Изоляция данных** | Рискованная | Безопасная (каждый запрос изолирован) |
| **Масштабируемость** | Проблемы при >10 магазинах | Хорошая (параллелизм) |
| **Точность данных** | Риск ошибок при переключении схем | Гарантированно точные данные |

**Вывод:** Фронтенд подход **лучше** для мульти-магазинной аналитики.

---

## Тестирование

```bash
# 1. Получить список магазинов
TOKEN=$(curl -s -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin_testshop", "password": "admin123"}' | jq -r '.access')

STORES=$(curl -s http://localhost:8000/api/users/stores/my-stores-with-credentials/ \
  -H "Authorization: Bearer $TOKEN")

echo "$STORES" | jq '.data.stores[] | {name, tenant_key}'

# 2. Для каждого магазина получить аналитику
# Магазин 1
curl "http://localhost:8000/api/analytics/daily-sales-reports/period/?start_date=2025-11-01&end_date=2025-11-20" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a" | jq '.totals'

# Магазин 2
curl "http://localhost:8000/api/analytics/daily-sales-reports/period/?start_date=2025-11-01&end_date=2025-11-20" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: asdawd_8b43a536" | jq '.totals'
```

---

## Рекомендации

1. **Используйте фронтенд подход** для мульти-магазинной аналитики
2. **Запрашивайте данные параллельно** (Promise.all)
3. **Кэшируйте результаты** на фронтенде
4. **Показывайте прогресс** загрузки для каждого магазина
5. **Обрабатывайте ошибки** индивидуально для каждого магазина

---

**Дата создания:** 2025-11-20
**Статус:** Рекомендуемый подход
