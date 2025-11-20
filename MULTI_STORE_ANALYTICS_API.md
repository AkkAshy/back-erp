# 📊 Мульти-магазинная аналитика - API Guide

## Обзор

Endpoint возвращает агрегированную аналитику по **ВСЕМ** магазинам пользователя одним запросом.

**Особенности:**
- ❌ НЕ требует X-Tenant-Key (работает в public схеме)
- ✅ Требует только Authorization token
- ✅ Собирает данные из каждой tenant схемы автоматически
- ✅ Агрегирует общие итоги по всем магазинам
- ✅ Показывает разбивку по каждому магазину
- ✅ Поддерживает готовые периоды (today, week, month) и кастомные даты

---

## 🔗 Эндпоинт

```
GET /api/users/stores/multi-store-analytics/
```

---

## 📋 Headers (обязательные)

| Заголовок | Описание | Пример |
|-----------|----------|--------|
| `Authorization` | Bearer токен пользователя | `Bearer eyJhbGc...` |

**⚠️ Примечание:** X-Tenant-Key НЕ требуется!

---

## 📤 Query Parameters (опционально)

| Параметр | Тип | Описание | Пример |
|----------|-----|----------|--------|
| `period` | string | Готовый период: `today`, `yesterday`, `week`, `month` | `period=month` |
| `start_date` | string | Дата начала (YYYY-MM-DD) | `start_date=2025-11-01` |
| `end_date` | string | Дата окончания (YYYY-MM-DD) | `end_date=2025-11-20` |

**Логика:**
- Если указан `period` - используется готовый период
- Если указаны `start_date` и `end_date` - используется кастомный период
- Если ничего не указано - последние 30 дней

---

## 📥 Response Format

### Успешный ответ (200 OK)

```json
{
  "status": "success",
  "data": {
    "total_stores": 3,
    "period": {
      "start_date": "2025-10-21",
      "end_date": "2025-11-20"
    },
    "aggregated": {
      "total_sales": 1227600000.0,
      "total_sales_count": 57,
      "total_discount": 0.0,
      "total_items_sold": 2088,
      "avg_sale_amount": 21536842.10
    },
    "by_store": [
      {
        "store_id": 2,
        "store_name": "Тестовый Магазин",
        "store_slug": "test_shop",
        "tenant_key": "test_shop_4dfa7a5a",
        "address": "ул. Тестовая, 1",
        "city": "Ташкент",
        "total_sales": 409200000.0,
        "sales_count": 19,
        "total_discount": 0.0,
        "total_items_sold": 696,
        "avg_sale": 21536842.10
      },
      {
        "store_id": 8,
        "store_name": "Магазин №2",
        "store_slug": "magazin_2",
        "tenant_key": "magazin_2_abc123",
        "address": "ул. Новая, 10",
        "city": "Самарканд",
        "total_sales": 409200000.0,
        "sales_count": 19,
        "total_discount": 0.0,
        "total_items_sold": 696,
        "avg_sale": 21536842.10
      }
    ]
  }
}
```

**Структура данных:**

- **total_stores** - количество магазинов пользователя
- **period** - период за который собрана аналитика
- **aggregated** - общие итоги по всем магазинам:
  - `total_sales` - общая сумма продаж
  - `total_sales_count` - общее количество продаж
  - `total_discount` - общая сумма скидок
  - `total_items_sold` - общее количество проданных товаров
  - `avg_sale_amount` - средний чек по всем магазинам
- **by_store** - разбивка по магазинам (отсортировано по убыванию продаж):
  - Данные каждого магазина
  - Tenant key для идентификации
  - Метрики продаж магазина

### Ответ при отсутствии магазинов (404 Not Found)

```json
{
  "status": "error",
  "message": "У вас нет активных магазинов"
}
```

### Ответ при ошибке в конкретном магазине (200 OK)

Если в одном из магазинов произошла ошибка, он все равно включается в список:

```json
{
  "status": "success",
  "data": {
    "total_stores": 2,
    "by_store": [
      {
        "store_id": 1,
        "store_name": "Работающий магазин",
        "total_sales": 500000.0,
        "sales_count": 100
      },
      {
        "store_id": 2,
        "store_name": "Проблемный магазин",
        "store_slug": "problem_shop",
        "tenant_key": "problem_shop_xyz",
        "total_sales": 0,
        "sales_count": 0,
        "error": "relation \"analytics_dailysalesreport\" does not exist"
      }
    ]
  }
}
```

---

## 💡 Примеры использования

### 1. Готовые периоды

```bash
# Сегодня
curl "http://localhost:8000/api/users/stores/multi-store-analytics/?period=today" \
  -H "Authorization: Bearer $TOKEN"

# Вчера
curl "http://localhost:8000/api/users/stores/multi-store-analytics/?period=yesterday" \
  -H "Authorization: Bearer $TOKEN"

# Последняя неделя
curl "http://localhost:8000/api/users/stores/multi-store-analytics/?period=week" \
  -H "Authorization: Bearer $TOKEN"

# Последний месяц (30 дней)
curl "http://localhost:8000/api/users/stores/multi-store-analytics/?period=month" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Кастомный период

```bash
curl "http://localhost:8000/api/users/stores/multi-store-analytics/?start_date=2025-11-01&end_date=2025-11-20" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. JavaScript - Получить аналитику за месяц

```javascript
async function getMultiStoreAnalytics(period = 'month') {
  const token = localStorage.getItem('access_token');

  try {
    const response = await fetch(
      `/api/users/stores/multi-store-analytics/?period=${period}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch analytics');
    }

    const data = await response.json();

    console.log(`📊 Аналитика за ${period}:`);
    console.log(`  Магазинов: ${data.data.total_stores}`);
    console.log(`  Общие продажи: ${data.data.aggregated.total_sales.toLocaleString()}`);
    console.log(`  Количество продаж: ${data.data.aggregated.total_sales_count}`);
    console.log(`  Средний чек: ${data.data.aggregated.avg_sale_amount.toLocaleString()}`);

    return data.data;
  } catch (error) {
    console.error('❌ Ошибка получения аналитики:', error);
    throw error;
  }
}

// Использование
const analytics = await getMultiStoreAnalytics('month');
```

### 4. React Hook - useMultiStoreAnalytics

```typescript
import { useState, useEffect } from 'react';
import { api } from './api';

interface Period {
  start_date: string;
  end_date: string;
}

interface Aggregated {
  total_sales: number;
  total_sales_count: number;
  total_discount: number;
  total_items_sold: number;
  avg_sale_amount: number;
}

interface StoreAnalytics {
  store_id: number;
  store_name: string;
  store_slug: string;
  tenant_key: string;
  address: string;
  city: string | null;
  total_sales: number;
  sales_count: number;
  total_discount: number;
  total_items_sold: number;
  avg_sale: number;
  error?: string;
}

interface MultiStoreAnalytics {
  total_stores: number;
  period: Period;
  aggregated: Aggregated;
  by_store: StoreAnalytics[];
}

export const useMultiStoreAnalytics = (period: string = 'month') => {
  const [analytics, setAnalytics] = useState<MultiStoreAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async (newPeriod?: string) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ period: newPeriod || period });
      const response = await api.get(`/users/stores/multi-store-analytics/?${params}`);
      setAnalytics(response.data.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Ошибка загрузки аналитики');
      console.error('Error fetching analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [period]);

  return { analytics, loading, error, refetch: fetchAnalytics };
};
```

### 5. React компонент - Dashboard с аналитикой

```tsx
import { useState } from 'react';
import { useMultiStoreAnalytics } from './hooks/useMultiStoreAnalytics';

export const MultiStoreDashboard = () => {
  const [period, setPeriod] = useState('month');
  const { analytics, loading, error, refetch } = useMultiStoreAnalytics(period);

  if (loading) {
    return <div className="loading">Загрузка аналитики...</div>;
  }

  if (error) {
    return (
      <div className="error">
        <p>Ошибка: {error}</p>
        <button onClick={() => refetch()}>Повторить</button>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  return (
    <div className="multi-store-dashboard">
      <div className="header">
        <h1>Аналитика по всем магазинам</h1>

        <div className="period-selector">
          <button
            className={period === 'today' ? 'active' : ''}
            onClick={() => setPeriod('today')}
          >
            Сегодня
          </button>
          <button
            className={period === 'week' ? 'active' : ''}
            onClick={() => setPeriod('week')}
          >
            Неделя
          </button>
          <button
            className={period === 'month' ? 'active' : ''}
            onClick={() => setPeriod('month')}
          >
            Месяц
          </button>
        </div>
      </div>

      <div className="period-info">
        <span>Период: {analytics.period.start_date} — {analytics.period.end_date}</span>
        <span>Магазинов: {analytics.total_stores}</span>
      </div>

      <div className="aggregated-stats">
        <div className="stat-card">
          <h3>Общие продажи</h3>
          <div className="value">
            {analytics.aggregated.total_sales.toLocaleString()} сум
          </div>
        </div>

        <div className="stat-card">
          <h3>Количество продаж</h3>
          <div className="value">
            {analytics.aggregated.total_sales_count}
          </div>
        </div>

        <div className="stat-card">
          <h3>Средний чек</h3>
          <div className="value">
            {analytics.aggregated.avg_sale_amount.toLocaleString()} сум
          </div>
        </div>

        <div className="stat-card">
          <h3>Продано товаров</h3>
          <div className="value">
            {analytics.aggregated.total_items_sold}
          </div>
        </div>
      </div>

      <div className="stores-breakdown">
        <h2>Разбивка по магазинам</h2>

        {analytics.by_store.map((store, index) => (
          <div key={store.store_id} className="store-card">
            <div className="store-header">
              <div className="rank">#{index + 1}</div>
              <div className="store-info">
                <h3>{store.store_name}</h3>
                <p className="address">{store.address || store.city || '—'}</p>
              </div>
            </div>

            {store.error ? (
              <div className="error-badge">
                ⚠️ Ошибка: {store.error}
              </div>
            ) : (
              <div className="store-stats">
                <div className="stat">
                  <label>Продажи:</label>
                  <span>{store.total_sales.toLocaleString()} сум</span>
                </div>
                <div className="stat">
                  <label>Кол-во:</label>
                  <span>{store.sales_count}</span>
                </div>
                <div className="stat">
                  <label>Средний чек:</label>
                  <span>{store.avg_sale.toLocaleString()} сум</span>
                </div>
                <div className="stat">
                  <label>Товаров:</label>
                  <span>{store.total_items_sold}</span>
                </div>
              </div>
            )}

            <div className="store-actions">
              <button
                onClick={() => {
                  localStorage.setItem('current_tenant_key', store.tenant_key);
                  window.location.href = `/stores/${store.store_slug}/analytics`;
                }}
              >
                Детальная аналитика
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 6. React компонент - График сравнения магазинов

```tsx
import { useMultiStoreAnalytics } from './hooks/useMultiStoreAnalytics';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

export const StoresComparisonChart = () => {
  const { analytics, loading } = useMultiStoreAnalytics('month');

  if (loading || !analytics) {
    return <div>Загрузка...</div>;
  }

  // Форматируем данные для графика
  const chartData = analytics.by_store.map(store => ({
    name: store.store_name,
    Продажи: store.total_sales,
    'Кол-во чеков': store.sales_count * 100000, // Масштабируем для видимости
    'Средний чек': store.avg_sale
  }));

  return (
    <div className="comparison-chart">
      <h2>Сравнение магазинов</h2>

      <BarChart width={800} height={400} data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="Продажи" fill="#8884d8" />
        <Bar dataKey="Средний чек" fill="#82ca9d" />
      </BarChart>
    </div>
  );
};
```

---

## 🔍 Логика работы

1. **Получение магазинов:**
   - Запрос: `Store.objects.filter(owner=request.user, is_active=True)`

2. **Парсинг периода:**
   - Проверяется параметр `period` (today, week, month)
   - Или используются `start_date` / `end_date`
   - По умолчанию: последние 30 дней

3. **Сбор данных из каждой схемы:**
   - Для каждого магазина переключается `search_path` на его схему
   - Запрашиваются `DailySalesReport` за период
   - Агрегируются метрики (total_sales, sales_count и т.д.)
   - Возвращается `search_path` в public

4. **Агрегация общих итогов:**
   - Суммируются данные всех магазинов
   - Вычисляется средний чек

5. **Сортировка:**
   - Магазины сортируются по убыванию total_sales

---

## 🎯 Use Cases

### 1. Владелец сети магазинов - Dashboard

```javascript
// Отображаем общую картину по всем магазинам
async function renderNetworkDashboard() {
  const analytics = await getMultiStoreAnalytics('month');

  const dashboard = {
    totalRevenue: analytics.aggregated.total_sales,
    totalStores: analytics.total_stores,
    topStore: analytics.by_store[0],
    worstStore: analytics.by_store[analytics.by_store.length - 1],
    averagePerStore: analytics.aggregated.total_sales / analytics.total_stores
  };

  console.log('🏆 Лучший магазин:', dashboard.topStore.store_name);
  console.log('📉 Требует внимания:', dashboard.worstStore.store_name);

  return dashboard;
}
```

### 2. Сравнение магазинов

```javascript
// Находим магазины с низкими показателями
async function findUnderperformingStores() {
  const analytics = await getMultiStoreAnalytics('month');

  const avgSales = analytics.aggregated.total_sales / analytics.total_stores;

  const underperforming = analytics.by_store.filter(
    store => store.total_sales < avgSales * 0.7 // Меньше 70% от среднего
  );

  console.log('⚠️ Магазины с низкими показателями:');
  underperforming.forEach(store => {
    console.log(`  - ${store.store_name}: ${store.total_sales.toLocaleString()}`);
  });

  return underperforming;
}
```

### 3. Экспорт отчета

```javascript
// Генерируем CSV отчет по всем магазинам
async function exportAnalyticsToCSV() {
  const analytics = await getMultiStoreAnalytics('month');

  const csv = [
    ['Магазин', 'Адрес', 'Продажи', 'Кол-во чеков', 'Средний чек', 'Товаров продано'],
    ...analytics.by_store.map(store => [
      store.store_name,
      store.address || store.city || '',
      store.total_sales,
      store.sales_count,
      store.avg_sale,
      store.total_items_sold
    ])
  ].map(row => row.join(',')).join('\n');

  // Скачиваем файл
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `multi-store-analytics-${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
}
```

---

## ⚠️ Важные замечания

1. **Производительность:**
   - Запрос переключает схемы для каждого магазина
   - Для большого количества магазинов (>10) может быть медленным
   - Рекомендуется кэширование на стороне клиента

2. **Ошибки в магазинах:**
   - Если в одном магазине ошибка, остальные данные все равно возвращаются
   - Проверяйте поле `error` в данных магазина

3. **Отсутствие данных:**
   - Если в магазине нет продаж за период, все метрики будут = 0
   - Это нормально, магазин все равно включается в список

4. **Безопасность:**
   - Только владелец видит аналитику своих магазинов
   - Сотрудники магазинов НЕ имеют доступа к этому endpoint

---

## 🔐 Требования

- **Аутентификация:** Bearer token (JWT) владельца магазинов
- **НЕ требуется:** X-Tenant-Key
- **Права:** Пользователь должен быть владельцем хотя бы одного магазина

---

## 📝 Связанные эндпоинты

- `GET /api/users/stores/` - Список магазинов без аналитики
- `GET /api/users/stores/my-stores-with-credentials/` - Список магазинов с credentials
- `GET /api/analytics/daily-sales-reports/` - Детальная аналитика одного магазина (требует X-Tenant-Key)

---

**Дата создания:** 2025-11-20
**Версия API:** 1.0
