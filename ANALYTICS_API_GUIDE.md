# API Аналитики и Отчётов

## Обзор

Модуль аналитики предоставляет готовые отчёты и статистику по:
- 📊 **Продажам** - дневные отчёты, тренды, графики
- 📦 **Товарам** - топ продаж, прибыльность, медленные товары
- 👥 **Покупателям** - RFM анализ, сегментация, группы риска
- 📈 **Остаткам** - снимки остатков, низкие остатки, переизбыток

**Важно:** Все endpoints только для чтения (read-only). Данные обновляются автоматически через signals при создании продаж.

---

## 1. Дневные отчёты по продажам

### 1.1. Список всех отчётов

```bash
GET /api/analytics/daily-sales/
```

**Ответ:**
```json
{
  "count": 30,
  "results": [
    {
      "id": 1,
      "date": "2025-11-17",
      "total_sales": 5000000.00,
      "total_sales_count": 150,
      "avg_sale_amount": 33333.33,
      "cash_sales": 3000000.00,
      "card_sales": 1500000.00,
      "credit_sales": 500000.00,
      "total_discount": 250000.00,
      "total_tax": 450000.00,
      "total_items_sold": 450,
      "unique_products_sold": 120,
      "unique_customers": 85,
      "new_customers": 5,
      "sessions_opened": 3,
      "sessions_closed": 2,
      "created_at": "2025-11-17T23:59:59+05:00",
      "updated_at": "2025-11-17T23:59:59+05:00"
    }
  ]
}
```

### 1.2. Отчёт за сегодня

```bash
GET /api/analytics/daily-sales/today/
```

**Ответ:** Данные за текущий день (структура как выше)

### 1.3. Отчёты за период

```bash
GET /api/analytics/daily-sales/period/?start_date=2025-11-01&end_date=2025-11-30
```

**Query параметры:**
- `start_date` - Дата начала (YYYY-MM-DD) **обязательно**
- `end_date` - Дата окончания (YYYY-MM-DD) **обязательно**

**Ответ:**
```json
{
  "period": {
    "start_date": "2025-11-01",
    "end_date": "2025-11-30",
    "days": 30
  },
  "totals": {
    "total_sales": 150000000.00,
    "total_count": 4500,
    "total_discount": 7500000.00,
    "total_tax": 13500000.00,
    "total_items": 13500,
    "avg_sale": 33333.33
  },
  "daily_reports": [
    {
      "id": 1,
      "date": "2025-11-01",
      "total_sales": 5000000.00,
      ...
    },
    ...
  ]
}
```

### 1.4. Тренды продаж (графики)

```bash
GET /api/analytics/daily-sales/trends/?days=30
```

**Query параметры:**
- `days` - Количество дней назад (по умолчанию 30)

**Ответ:**
```json
{
  "period": "Последние 30 дней",
  "trends": [
    {
      "date": "2025-10-18",
      "total_sales": 4500000.00,
      "total_count": 140,
      "avg_sale": 32142.86
    },
    {
      "date": "2025-10-19",
      "total_sales": 5200000.00,
      "total_count": 155,
      "avg_sale": 33548.39
    },
    ...
  ]
}
```

**Использование:** Отличные данные для построения графиков в Chart.js, Recharts и т.д.

---

## 2. Производительность товаров

### 2.1. Список всех данных по товарам

```bash
GET /api/analytics/product-performance/
```

**Фильтры:**
- `product` - ID товара
- `date` - Дата

**Сортировка:**
- `date` - По дате
- `total_revenue` - По выручке
- `quantity_sold` - По количеству
- `profit_margin` - По марже

**Ответ:**
```json
{
  "count": 500,
  "results": [
    {
      "id": 1,
      "product": 10,
      "product_name": "Молоко 3.2%",
      "product_code": "PROD-001",
      "product_barcode": "4870123456789",
      "date": "2025-11-17",
      "quantity_sold": 150.000,
      "total_revenue": 1800000.00,
      "sales_count": 45,
      "avg_price": 12000.00,
      "avg_discount": 5.00,
      "total_cost": 1350000.00,
      "total_profit": 450000.00,
      "profit_margin": 25.00,
      "created_at": "2025-11-17T23:59:59+05:00",
      "updated_at": "2025-11-17T23:59:59+05:00"
    }
  ]
}
```

### 2.2. Топ товаров за период

```bash
GET /api/analytics/product-performance/top_products/?start_date=2025-11-01&end_date=2025-11-30&limit=10&order_by=revenue
```

**Query параметры:**
- `start_date` - Дата начала (опционально, по умолчанию последние 30 дней)
- `end_date` - Дата окончания (опционально)
- `limit` - Количество товаров (по умолчанию 10)
- `order_by` - Сортировка: `revenue` (по умолчанию), `quantity`, `profit`

**Ответ:**
```json
{
  "period": {
    "start_date": "2025-11-01",
    "end_date": "2025-11-30"
  },
  "top_products": [
    {
      "product_id": 10,
      "product_name": "Молоко 3.2%",
      "product_code": "PROD-001",
      "total_revenue": 54000000.00,
      "total_quantity": 4500.000,
      "total_profit": 13500000.00,
      "sales_count": 1350
    },
    {
      "product_id": 15,
      "product_name": "Хлеб белый",
      "product_code": "PROD-002",
      "total_revenue": 27000000.00,
      "total_quantity": 3000.000,
      "total_profit": 8100000.00,
      "sales_count": 900
    },
    ...
  ]
}
```

### 2.3. Медленно продающиеся товары

```bash
GET /api/analytics/product-performance/slow_movers/?days=30
```

**Query параметры:**
- `days` - Количество дней назад (по умолчанию 30)

**Ответ:**
```json
{
  "period": "Последние 30 дней",
  "slow_movers": [
    {
      "product__id": 45,
      "product__name": "Редкий товар",
      "product__code": "PROD-045",
      "total_quantity": 2.000
    },
    {
      "product__id": 78,
      "product__name": "Непопулярный товар",
      "product__code": "PROD-078",
      "total_quantity": 4.000
    },
    ...
  ]
}
```

**Критерий:** Товары с продажами < 5 единиц за период

---

## 3. Аналитика покупателей (RFM)

### 3.1. Список аналитики по покупателям

```bash
GET /api/analytics/customer-analytics/
```

**Фильтры:**
- `customer` - ID покупателя
- `segment` - Сегмент (Champions, Loyal Customers, и т.д.)
- `rfm_score` - RFM балл

**Сортировка:**
- `monetary` - По сумме покупок
- `frequency` - По частоте
- `recency_days` - По давности
- `rfm_score` - По RFM баллу

**Ответ:**
```json
{
  "count": 250,
  "results": [
    {
      "id": 1,
      "customer": 5,
      "customer_name": "Петров Иван",
      "customer_phone": "+998901234567",
      "customer_type": "individual",
      "period_start": "2024-11-18",
      "period_end": "2025-11-18",
      "recency_days": 5,
      "frequency": 45,
      "monetary": 15000000.00,
      "rfm_score": 555,
      "segment": "Champions",
      "purchases_count": 45,
      "total_spent": 15000000.00,
      "avg_purchase_amount": 333333.33,
      "credit_purchases": 5,
      "total_credit_amount": 2000000.00,
      "avg_payment_delay_days": 3.5,
      "created_at": "2025-11-17T20:00:00+05:00",
      "updated_at": "2025-11-17T20:00:00+05:00"
    }
  ]
}
```

### 3.2. Статистика по сегментам

```bash
GET /api/analytics/customer-analytics/segments/
```

**Ответ:**
```json
{
  "period": {
    "period_start": "2024-11-18",
    "period_end": "2025-11-18"
  },
  "segments": [
    {
      "segment": "Champions",
      "count": 25,
      "total_spent": 375000000.00,
      "avg_purchase": 500000.00
    },
    {
      "segment": "Loyal Customers",
      "count": 50,
      "total_spent": 250000000.00,
      "avg_purchase": 200000.00
    },
    {
      "segment": "Potential Loyalists",
      "count": 75,
      "total_spent": 150000000.00,
      "avg_purchase": 133333.33
    },
    {
      "segment": "At Risk",
      "count": 30,
      "total_spent": 90000000.00,
      "avg_purchase": 100000.00
    },
    ...
  ]
}
```

**RFM Сегменты:**
- **Champions** - Лучшие клиенты
- **Loyal Customers** - Лояльные клиенты
- **Potential Loyalists** - Потенциально лояльные
- **New Customers** - Новые клиенты
- **Promising** - Перспективные
- **Need Attention** - Требуют внимания
- **About To Sleep** - Уходят в спячку
- **At Risk** - В группе риска
- **Can't Lose Them** - Нельзя потерять
- **Hibernating** - Спящие
- **Lost** - Потерянные

### 3.3. Клиенты в группе риска

```bash
GET /api/analytics/customer-analytics/at_risk/
```

**Ответ:**
```json
{
  "count": 45,
  "customers": [
    {
      "id": 15,
      "customer": 25,
      "customer_name": "Сидоров Петр",
      "customer_phone": "+998907654321",
      "segment": "At Risk",
      "recency_days": 90,
      "frequency": 20,
      "monetary": 5000000.00,
      "rfm_score": 322,
      ...
    },
    ...
  ]
}
```

**Сегменты риска:**
- At Risk
- Can't Lose Them
- Hibernating
- Lost

---

## 4. Снимки остатков

### 4.1. Список всех снимков

```bash
GET /api/analytics/inventory-snapshots/
```

**Фильтры:**
- `product` - ID товара
- `date` - Дата
- `is_low_stock` - Низкий остаток (true/false)
- `is_out_of_stock` - Нет на складе (true/false)
- `is_overstock` - Переизбыток (true/false)

**Сортировка:**
- `date` - По дате
- `quantity_on_hand` - По количеству
- `turnover_rate` - По оборачиваемости
- `days_of_stock` - По дням запаса

**Ответ:**
```json
{
  "count": 300,
  "results": [
    {
      "id": 1,
      "product": 10,
      "product_name": "Молоко 3.2%",
      "product_code": "PROD-001",
      "date": "2025-11-17",
      "quantity_on_hand": 500.000,
      "reserved_quantity": 50.000,
      "available_quantity": 450.000,
      "total_cost": 4500000.00,
      "total_value": 6000000.00,
      "turnover_rate": 15.5,
      "days_of_stock": 23,
      "is_out_of_stock": false,
      "is_low_stock": false,
      "is_overstock": false,
      "created_at": "2025-11-17T23:59:59+05:00"
    }
  ]
}
```

### 4.2. Последние снимки (актуальные остатки)

```bash
GET /api/analytics/inventory-snapshots/latest/
```

**Ответ:**
```json
{
  "date": "2025-11-17",
  "snapshots": [
    {
      "id": 1,
      "product": 10,
      "product_name": "Молоко 3.2%",
      "quantity_on_hand": 500.000,
      "available_quantity": 450.000,
      "turnover_rate": 15.5,
      "days_of_stock": 23,
      ...
    },
    ...
  ]
}
```

### 4.3. Товары с низким остатком

```bash
GET /api/analytics/inventory-snapshots/low_stock_alerts/
```

**Ответ:**
```json
{
  "date": "2025-11-17",
  "count": 12,
  "products": [
    {
      "id": 45,
      "product": 78,
      "product_name": "Товар на исходе",
      "product_code": "PROD-078",
      "quantity_on_hand": 15.000,
      "available_quantity": 10.000,
      "days_of_stock": 3,
      "is_low_stock": true,
      ...
    },
    ...
  ]
}
```

### 4.4. Товары с нулевым остатком

```bash
GET /api/analytics/inventory-snapshots/out_of_stock/
```

**Ответ:**
```json
{
  "date": "2025-11-17",
  "count": 5,
  "products": [
    {
      "id": 67,
      "product": 123,
      "product_name": "Закончившийся товар",
      "product_code": "PROD-123",
      "quantity_on_hand": 0.000,
      "available_quantity": 0.000,
      "is_out_of_stock": true,
      ...
    },
    ...
  ]
}
```

---

## Frontend примеры (React + TypeScript)

### Сервис для аналитики

```typescript
// services/analytics.ts
import api from '@/utils/api';

// Дневные отчёты
export const getDailySalesReport = async (startDate: string, endDate: string) => {
  const response = await api.get('/analytics/daily-sales/period/', {
    params: { start_date: startDate, end_date: endDate }
  });
  return response.data;
};

export const getTodayReport = async () => {
  const response = await api.get('/analytics/daily-sales/today/');
  return response.data;
};

export const getSalesTrends = async (days: number = 30) => {
  const response = await api.get('/analytics/daily-sales/trends/', {
    params: { days }
  });
  return response.data;
};

// Топ товары
export const getTopProducts = async (
  startDate?: string,
  endDate?: string,
  limit: number = 10,
  orderBy: 'revenue' | 'quantity' | 'profit' = 'revenue'
) => {
  const response = await api.get('/analytics/product-performance/top_products/', {
    params: {
      start_date: startDate,
      end_date: endDate,
      limit,
      order_by: orderBy
    }
  });
  return response.data;
};

// Медленные товары
export const getSlowMovers = async (days: number = 30) => {
  const response = await api.get('/analytics/product-performance/slow_movers/', {
    params: { days }
  });
  return response.data;
};

// Сегменты покупателей
export const getCustomerSegments = async () => {
  const response = await api.get('/analytics/customer-analytics/segments/');
  return response.data;
};

// Клиенты в группе риска
export const getAtRiskCustomers = async () => {
  const response = await api.get('/analytics/customer-analytics/at_risk/');
  return response.data;
};

// Остатки
export const getLatestInventory = async () => {
  const response = await api.get('/analytics/inventory-snapshots/latest/');
  return response.data;
};

export const getLowStockAlerts = async () => {
  const response = await api.get('/analytics/inventory-snapshots/low_stock_alerts/');
  return response.data;
};

export const getOutOfStock = async () => {
  const response = await api.get('/analytics/inventory-snapshots/out_of_stock/');
  return response.data;
};
```

### Компонент дашборда продаж

```typescript
import { useState, useEffect } from 'react';
import { getTodayReport, getSalesTrends } from '@/services/analytics';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

export const SalesDashboard = () => {
  const [todayData, setTodayData] = useState(null);
  const [trendsData, setTrendsData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [today, trends] = await Promise.all([
        getTodayReport(),
        getSalesTrends(30)
      ]);
      setTodayData(today);
      setTrendsData(trends.trends);
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Загрузка...</div>;

  return (
    <div className="sales-dashboard">
      {/* Карточки за сегодня */}
      <div className="stats-cards">
        <div className="card">
          <h3>Продажи за сегодня</h3>
          <p className="amount">
            {todayData?.total_sales?.toLocaleString()} сум
          </p>
          <p className="count">
            {todayData?.total_sales_count} чеков
          </p>
        </div>

        <div className="card">
          <h3>Средний чек</h3>
          <p className="amount">
            {todayData?.avg_sale_amount?.toLocaleString()} сум
          </p>
        </div>

        <div className="card">
          <h3>Товаров продано</h3>
          <p className="amount">
            {todayData?.total_items_sold}
          </p>
          <p className="count">
            {todayData?.unique_products_sold} уникальных
          </p>
        </div>

        <div className="card">
          <h3>Клиенты</h3>
          <p className="amount">
            {todayData?.unique_customers}
          </p>
          <p className="count new-customers">
            +{todayData?.new_customers} новых
          </p>
        </div>
      </div>

      {/* График трендов */}
      <div className="trends-chart">
        <h3>Продажи за последние 30 дней</h3>
        <LineChart width={800} height={300} data={trendsData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="total_sales"
            stroke="#8884d8"
            name="Сумма продаж"
          />
          <Line
            type="monotone"
            dataKey="total_count"
            stroke="#82ca9d"
            name="Количество чеков"
          />
        </LineChart>
      </div>

      {/* Оплаты */}
      <div className="payment-breakdown">
        <h3>Оплаты за сегодня</h3>
        <div className="payment-stats">
          <div className="payment-item">
            <span>Наличные:</span>
            <strong>{todayData?.cash_sales?.toLocaleString()} сум</strong>
          </div>
          <div className="payment-item">
            <span>Карта:</span>
            <strong>{todayData?.card_sales?.toLocaleString()} сум</strong>
          </div>
          <div className="payment-item">
            <span>В кредит:</span>
            <strong>{todayData?.credit_sales?.toLocaleString()} сум</strong>
          </div>
        </div>
      </div>
    </div>
  );
};
```

### Компонент топ товаров

```typescript
import { useState, useEffect } from 'react';
import { getTopProducts } from '@/services/analytics';

export const TopProductsWidget = () => {
  const [topProducts, setTopProducts] = useState([]);
  const [orderBy, setOrderBy] = useState<'revenue' | 'quantity' | 'profit'>('revenue');

  useEffect(() => {
    loadTopProducts();
  }, [orderBy]);

  const loadTopProducts = async () => {
    try {
      const data = await getTopProducts(undefined, undefined, 10, orderBy);
      setTopProducts(data.top_products);
    } catch (error) {
      console.error('Ошибка загрузки топ товаров:', error);
    }
  };

  return (
    <div className="top-products-widget">
      <div className="header">
        <h3>Топ товары</h3>
        <select
          value={orderBy}
          onChange={(e) => setOrderBy(e.target.value as any)}
        >
          <option value="revenue">По выручке</option>
          <option value="quantity">По количеству</option>
          <option value="profit">По прибыли</option>
        </select>
      </div>

      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Товар</th>
            <th>Продано</th>
            <th>Выручка</th>
            <th>Прибыль</th>
          </tr>
        </thead>
        <tbody>
          {topProducts.map((product, index) => (
            <tr key={product.product_id}>
              <td>{index + 1}</td>
              <td>
                <div>
                  <strong>{product.product_name}</strong>
                  <br />
                  <small>{product.product_code}</small>
                </div>
              </td>
              <td>{product.total_quantity}</td>
              <td>{product.total_revenue.toLocaleString()} сум</td>
              <td className="profit">
                {product.total_profit.toLocaleString()} сум
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

### Компонент сегментов покупателей

```typescript
import { useState, useEffect } from 'react';
import { getCustomerSegments } from '@/services/analytics';
import { PieChart, Pie, Cell, Legend, Tooltip } from 'recharts';

const SEGMENT_COLORS = {
  'Champions': '#00C49F',
  'Loyal Customers': '#0088FE',
  'Potential Loyalists': '#00C49F',
  'At Risk': '#FF8042',
  'Lost': '#FF0000',
};

export const CustomerSegmentsWidget = () => {
  const [segments, setSegments] = useState([]);

  useEffect(() => {
    loadSegments();
  }, []);

  const loadSegments = async () => {
    try {
      const data = await getCustomerSegments();
      setSegments(data.segments);
    } catch (error) {
      console.error('Ошибка загрузки сегментов:', error);
    }
  };

  const chartData = segments.map(seg => ({
    name: seg.segment,
    value: seg.count,
    total: seg.total_spent
  }));

  return (
    <div className="customer-segments-widget">
      <h3>Сегменты покупателей</h3>

      <div className="chart-container">
        <PieChart width={400} height={300}>
          <Pie
            data={chartData}
            cx={200}
            cy={150}
            labelLine={false}
            label={(entry) => `${entry.name}: ${entry.value}`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={SEGMENT_COLORS[entry.name] || '#999999'}
              />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </div>

      <table>
        <thead>
          <tr>
            <th>Сегмент</th>
            <th>Клиентов</th>
            <th>Общая сумма</th>
            <th>Средний чек</th>
          </tr>
        </thead>
        <tbody>
          {segments.map(seg => (
            <tr key={seg.segment}>
              <td>
                <span
                  className="segment-badge"
                  style={{ backgroundColor: SEGMENT_COLORS[seg.segment] }}
                >
                  {seg.segment}
                </span>
              </td>
              <td>{seg.count}</td>
              <td>{seg.total_spent.toLocaleString()} сум</td>
              <td>{seg.avg_purchase.toLocaleString()} сум</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

### Компонент оповещений об остатках

```typescript
import { useState, useEffect } from 'react';
import { getLowStockAlerts, getOutOfStock } from '@/services/analytics';

export const StockAlertsWidget = () => {
  const [lowStock, setLowStock] = useState([]);
  const [outOfStock, setOutOfStock] = useState([]);

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      const [lowData, outData] = await Promise.all([
        getLowStockAlerts(),
        getOutOfStock()
      ]);
      setLowStock(lowData.products);
      setOutOfStock(outData.products);
    } catch (error) {
      console.error('Ошибка загрузки оповещений:', error);
    }
  };

  return (
    <div className="stock-alerts-widget">
      <h3>Оповещения об остатках</h3>

      {/* Нет на складе */}
      {outOfStock.length > 0 && (
        <div className="alert-section danger">
          <h4>❌ Нет на складе ({outOfStock.length})</h4>
          <ul>
            {outOfStock.map(item => (
              <li key={item.id}>
                <strong>{item.product_name}</strong>
                <span className="code">{item.product_code}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Низкий остаток */}
      {lowStock.length > 0 && (
        <div className="alert-section warning">
          <h4>⚠️ Низкий остаток ({lowStock.length})</h4>
          <ul>
            {lowStock.map(item => (
              <li key={item.id}>
                <strong>{item.product_name}</strong>
                <span className="code">{item.product_code}</span>
                <span className="stock">
                  Осталось: {item.quantity_on_hand} ({item.days_of_stock} дней)
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {lowStock.length === 0 && outOfStock.length === 0 && (
        <p className="no-alerts">✅ Все товары в наличии</p>
      )}
    </div>
  );
};
```

---

## Резюме

### Базовые URL:
- `/api/analytics/daily-sales/` - Дневные отчёты
- `/api/analytics/product-performance/` - Производительность товаров
- `/api/analytics/customer-analytics/` - Аналитика покупателей
- `/api/analytics/inventory-snapshots/` - Снимки остатков

### Ключевые endpoints:
| Endpoint | Описание |
|----------|----------|
| `GET /api/analytics/daily-sales/today/` | Отчёт за сегодня |
| `GET /api/analytics/daily-sales/period/` | Отчёты за период |
| `GET /api/analytics/daily-sales/trends/` | График трендов |
| `GET /api/analytics/product-performance/top_products/` | Топ товары |
| `GET /api/analytics/product-performance/slow_movers/` | Медленные товары |
| `GET /api/analytics/customer-analytics/segments/` | Сегменты покупателей |
| `GET /api/analytics/customer-analytics/at_risk/` | Клиенты в группе риска |
| `GET /api/analytics/inventory-snapshots/latest/` | Актуальные остатки |
| `GET /api/analytics/inventory-snapshots/low_stock_alerts/` | Низкие остатки |
| `GET /api/analytics/inventory-snapshots/out_of_stock/` | Товары без остатка |

### Обязательные заголовки:
```
Authorization: Bearer {access_token}
X-Tenant-Key: {tenant_key}
```

### Особенности:
- ✅ Все endpoints только для чтения (read-only)
- ✅ Данные обновляются автоматически через signals
- ✅ Поддержка фильтрации и сортировки
- ✅ Пагинация для больших списков
- ✅ RFM анализ для сегментации клиентов

Готово! 🎉
