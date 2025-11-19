# 📊 Топ Кассиров - Шпаргалка для Фронтенда

## 🚀 Быстрый старт

```javascript
// 1. Топ 10 кассиров за текущий месяц (по умолчанию)
const response = await api.get('/sales/sessions/cashier-stats/');
const { cashiers, total_cashiers } = response.data.data;

// 2. Топ 5 кассиров за сегодня
const today = new Date().toISOString().split('T')[0]; // "2025-11-19"
const response = await api.get(`/sales/sessions/cashier-stats/?date_from=${today}&date_to=${today}&limit=5`);

// 3. Топ 3 кассира за последние 7 дней
const dateTo = new Date().toISOString().split('T')[0];
const dateFrom = new Date(Date.now() - 7*24*60*60*1000).toISOString().split('T')[0];
const response = await api.get(`/sales/sessions/cashier-stats/?date_from=${dateFrom}&date_to=${dateTo}&limit=3`);
```

---

## 📋 Структура ответа

```typescript
interface CashierStatsResponse {
  status: "success";
  data: {
    period: {
      from: string;      // ISO datetime с timezone
      to: string;        // ISO datetime с timezone
    };
    cashiers: Cashier[];
    total_cashiers: number;
  };
}

interface Cashier {
  id: number;
  full_name: string;
  phone: string;
  role: "cashier" | "stockkeeper";
  total_sales: string;     // Decimal (общая сумма)
  cash_sales: string;      // Decimal (наличные)
  card_sales: string;      // Decimal (карта)
  sales_count: number;     // Количество продаж
  sessions_count: number;  // Количество смен
}
```

---

## 💡 Примеры использования

### React компонент - Топ кассиров за день

```jsx
import { useState, useEffect } from 'react';
import { api } from './api';

function TopCashiersToday() {
  const [cashiers, setCashiers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadCashiers() {
      try {
        const today = new Date().toISOString().split('T')[0];
        const response = await api.get(
          `/sales/sessions/cashier-stats/?date_from=${today}&date_to=${today}&limit=5`
        );
        setCashiers(response.data.data.cashiers);
      } catch (error) {
        console.error('Error loading cashiers:', error);
      } finally {
        setLoading(false);
      }
    }
    loadCashiers();
  }, []);

  if (loading) return <div>Загрузка...</div>;

  return (
    <div className="top-cashiers">
      <h2>🏆 Топ 5 кассиров сегодня</h2>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Кассир</th>
            <th>Продаж</th>
            <th>Сумма</th>
            <th>Наличные</th>
            <th>Карта</th>
          </tr>
        </thead>
        <tbody>
          {cashiers.map((cashier, index) => (
            <tr key={cashier.id}>
              <td>{index + 1}</td>
              <td>
                <strong>{cashier.full_name}</strong>
                <br />
                <small>{cashier.phone}</small>
              </td>
              <td>{cashier.sales_count}</td>
              <td>{Number(cashier.total_sales).toLocaleString()} сум</td>
              <td>{Number(cashier.cash_sales).toLocaleString()} сум</td>
              <td>{Number(cashier.card_sales).toLocaleString()} сум</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Vue компонент - Выбор периода

```vue
<template>
  <div class="cashier-stats">
    <div class="date-selector">
      <label>От: <input type="date" v-model="dateFrom" /></label>
      <label>До: <input type="date" v-model="dateTo" /></label>
      <label>Топ: <input type="number" v-model="limit" min="1" max="50" /></label>
      <button @click="loadStats">Загрузить</button>
    </div>

    <div v-if="loading">Загрузка...</div>

    <div v-else class="leaderboard">
      <div v-for="(cashier, index) in cashiers" :key="cashier.id" class="cashier-card">
        <div class="rank">{{ index + 1 }}</div>
        <div class="info">
          <h3>{{ cashier.full_name }}</h3>
          <p>{{ cashier.phone }}</p>
        </div>
        <div class="stats">
          <div class="stat">
            <span class="label">Продаж:</span>
            <span class="value">{{ cashier.sales_count }}</span>
          </div>
          <div class="stat">
            <span class="label">Сумма:</span>
            <span class="value">{{ formatMoney(cashier.total_sales) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      dateFrom: new Date().toISOString().split('T')[0],
      dateTo: new Date().toISOString().split('T')[0],
      limit: 10,
      cashiers: [],
      loading: false
    };
  },

  methods: {
    async loadStats() {
      this.loading = true;
      try {
        const params = new URLSearchParams({
          date_from: this.dateFrom,
          date_to: this.dateTo,
          limit: this.limit
        });

        const response = await this.$api.get(`/sales/sessions/cashier-stats/?${params}`);
        this.cashiers = response.data.data.cashiers;
      } catch (error) {
        console.error('Error:', error);
        this.$toast.error('Ошибка загрузки статистики');
      } finally {
        this.loading = false;
      }
    },

    formatMoney(amount) {
      return Number(amount).toLocaleString('ru-RU') + ' сум';
    }
  },

  mounted() {
    this.loadStats();
  }
};
</script>
```

---

## 🎨 UI компоненты

### Медали для топ-3

```jsx
function getMedal(position) {
  const medals = {
    1: { emoji: '🥇', color: '#FFD700', text: 'Золото' },
    2: { emoji: '🥈', color: '#C0C0C0', text: 'Серебро' },
    3: { emoji: '🥉', color: '#CD7F32', text: 'Бронза' }
  };
  return medals[position] || null;
}

function CashierRow({ cashier, position }) {
  const medal = getMedal(position);

  return (
    <div className="cashier-row" style={{ borderLeft: medal ? `4px solid ${medal.color}` : 'none' }}>
      <span className="position">
        {medal ? medal.emoji : position}
      </span>
      <span className="name">{cashier.full_name}</span>
      <span className="sales">{cashier.total_sales} сум</span>
    </div>
  );
}
```

### Прогресс-бары для визуализации

```jsx
function CashierProgressBar({ cashier, maxSales }) {
  const percentage = (Number(cashier.total_sales) / maxSales) * 100;

  return (
    <div className="cashier-progress">
      <div className="cashier-info">
        <span>{cashier.full_name}</span>
        <span>{Number(cashier.total_sales).toLocaleString()} сум</span>
      </div>
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="cashier-details">
        <span>💰 Наличные: {Number(cashier.cash_sales).toLocaleString()}</span>
        <span>💳 Карта: {Number(cashier.card_sales).toLocaleString()}</span>
        <span>🛒 Продаж: {cashier.sales_count}</span>
      </div>
    </div>
  );
}

function CashierLeaderboard({ cashiers }) {
  const maxSales = Math.max(...cashiers.map(c => Number(c.total_sales)));

  return (
    <div className="leaderboard">
      {cashiers.map(cashier => (
        <CashierProgressBar
          key={cashier.id}
          cashier={cashier}
          maxSales={maxSales}
        />
      ))}
    </div>
  );
}
```

---

## 📊 Интеграция с графиками

### Chart.js пример

```javascript
import { Bar } from 'react-chartjs-2';

async function getCashierChartData(dateFrom, dateTo) {
  const response = await api.get(
    `/sales/sessions/cashier-stats/?date_from=${dateFrom}&date_to=${dateTo}&limit=10`
  );

  const cashiers = response.data.data.cashiers;

  return {
    labels: cashiers.map(c => c.full_name),
    datasets: [
      {
        label: 'Наличные',
        data: cashiers.map(c => Number(c.cash_sales)),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
      },
      {
        label: 'Карта',
        data: cashiers.map(c => Number(c.card_sales)),
        backgroundColor: 'rgba(153, 102, 255, 0.6)',
      }
    ]
  };
}

function CashierChart() {
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    getCashierChartData(today, today).then(setChartData);
  }, []);

  if (!chartData) return <div>Загрузка...</div>;

  return (
    <Bar
      data={chartData}
      options={{
        responsive: true,
        scales: {
          x: { stacked: true },
          y: { stacked: true }
        }
      }}
    />
  );
}
```

---

## ⚠️ Важные замечания

### Формат даты

```javascript
// ✅ ПРАВИЛЬНО - используйте простой формат YYYY-MM-DD
const dateFrom = "2025-11-01";
const dateTo = "2025-11-30";

// ❌ НЕПРАВИЛЬНО - не добавляйте T00:00:00 для date_to!
const dateTo = "2025-11-30T00:00:00";  // Пропустит весь день 30-го!

// ✅ Если нужно точное время, используйте полный формат
const dateFrom = "2025-11-01T09:00:00";
const dateTo = "2025-11-30T18:00:00";
```

### Конвертация из Date

```javascript
// Получить YYYY-MM-DD из объекта Date
const date = new Date();
const dateString = date.toISOString().split('T')[0];  // "2025-11-19"

// Или используйте библиотеку
import { format } from 'date-fns';
const dateString = format(new Date(), 'yyyy-MM-dd');
```

### Обработка Decimal полей

```javascript
// ✅ ПРАВИЛЬНО - конвертируйте в Number перед использованием
const total = Number(cashier.total_sales);
const formatted = total.toLocaleString('ru-RU', {
  style: 'currency',
  currency: 'UZS'
});

// ❌ НЕПРАВИЛЬНО - не используйте строки напрямую
const sum = cashier.total_sales + cashier.cash_sales;  // Конкатенация строк!
```

---

## 🔐 Авторизация

Не забудьте добавить заголовки:

```javascript
// Axios
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
    'X-Tenant-Key': 'test_shop_4dfa7a5a'
  }
});

// Добавить токен
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

## 📱 Мобильная адаптация

```css
/* Адаптивная таблица */
@media (max-width: 768px) {
  .top-cashiers table {
    display: block;
    overflow-x: auto;
  }

  .cashier-card {
    flex-direction: column;
    padding: 15px;
  }

  .stats {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }
}
```

---

**Дата создания:** 2025-11-19
**Версия API:** 1.0
