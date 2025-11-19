# 🚀 Quick Start - Frontend Integration

Быстрый старт для фронтенд разработчиков. Минимум текста, максимум примеров кода.

---

## 🔑 Базовые настройки

```javascript
const API_BASE_URL = 'https://back-erp-gules.vercel.app/api';
const TENANT_KEY = 'tokyo_1a12e47a'; // Получаете после логина

// Axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-Tenant-Key': TENANT_KEY
  }
});

// Add token to requests
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

## 1️⃣ Логин кассира + выбор себя

```javascript
// Step 1: Login
async function loginCashier() {
  const response = await axios.post(`${API_BASE_URL}/users/auth/login/`, {
    username: 'tokyo_staff',
    password: '12345678'
  }, {
    headers: {
      'X-Tenant-Key': TENANT_KEY
    }
  });

  const { access, refresh, available_stores } = response.data;

  // Save tokens
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
  localStorage.setItem('tenant_key', available_stores[0].tenant_key);

  // Get cashiers list
  const cashiers = available_stores[0].cashiers;

  return cashiers;
}

// Step 2: Show cashier selection UI
function showCashierSelection(cashiers) {
  // Render UI with cashiers list
  cashiers.forEach(cashier => {
    console.log(`${cashier.id}: ${cashier.full_name} - ${cashier.phone}`);
  });
}

// Step 3: User selects cashier
function selectCashier(cashierId) {
  localStorage.setItem('selected_cashier_id', cashierId);
  checkOpenSession();
}

// Usage:
loginCashier()
  .then(cashiers => showCashierSelection(cashiers));
```

---

## 2️⃣ Проверка/открытие смены

⚠️ **ВАЖНО**: При открытии смены НЕ НУЖНО указывать кассира! Кассир выбирается при каждой продаже.

```javascript
async function checkOpenSession() {
  try {
    // Check if session already open
    const response = await api.get('/sales/cashier-sessions/current/');

    if (response.data.status === 'success') {
      // Session is open
      const session = response.data.data;
      localStorage.setItem('session_id', session.id);
      goToSalesScreen();
    }
  } catch (error) {
    if (error.response.status === 404) {
      // No open session - show open session screen
      showOpenSessionScreen();
    }
  }
}

async function openSession(openingCash) {
  // ⭐ cashier_id НЕ НУЖЕН - смена общая для всех!
  const response = await api.post('/sales/cashier-sessions/', {
    opening_cash: openingCash
  });

  const session = response.data.data;
  localStorage.setItem('session_id', session.id);

  goToSalesScreen();
}

// Usage:
openSession('100000.00');
```

---

## 3️⃣ Сканирование товара

```javascript
async function scanProduct(barcode) {
  const response = await api.post('/products/scan/', {
    barcode: barcode
  });

  const product = response.data.data;

  // Add to cart
  addToCart(product);

  return product;
}

// Example cart state
let cart = [];

function addToCart(product) {
  const existingItem = cart.find(item => item.product_id === product.id);

  if (existingItem) {
    existingItem.quantity += 1;
  } else {
    cart.push({
      product_id: product.id,
      name: product.name,
      price: product.price,
      quantity: 1
    });
  }
}

// Usage:
scanProduct('4600051000014');
```

---

## 4️⃣ Создание продажи

⚠️ **ВАЖНО**: При создании продажи ОБЯЗАТЕЛЬНО указывать `cashier_id`!

```javascript
async function createSale(cashierId, customerPhone = '', paymentMethod = 'cash', receivedAmount = null) {
  const sessionId = localStorage.getItem('session_id');

  // Prepare items
  const items = cart.map(item => ({
    product: item.product_id,
    quantity: item.quantity,
    unit_price: item.price
  }));

  // Calculate total
  const totalAmount = cart.reduce((sum, item) =>
    sum + (parseFloat(item.price) * item.quantity), 0
  );

  // Prepare payments
  const payments = [{
    payment_method: paymentMethod,
    amount: totalAmount.toFixed(2),
    ...(paymentMethod === 'cash' && receivedAmount ? {
      received_amount: receivedAmount
    } : {})
  }];

  // Create sale
  const response = await api.post('/sales/sales/', {
    session: parseInt(sessionId),
    cashier_id: cashierId,  // ⭐ ОБЯЗАТЕЛЬНОЕ ПОЛЕ!
    customer_phone: customerPhone,
    items: items,
    payments: payments,
    discount_percent: '0.00'
  });

  const sale = response.data.data;

  // Clear cart
  cart = [];

  // Print receipt
  printReceipt(sale);

  return sale;
}

function printReceipt(sale) {
  console.log('Receipt:', sale.receipt_number);
  console.log('Cashier:', sale.cashier_name);  // ⭐ Имя кассира в ответе
  console.log('Total:', sale.total_amount);
  console.log('Change:', sale.payments[0].change_amount);
}

// Usage:
const cashierId = localStorage.getItem('selected_cashier_id');
createSale(parseInt(cashierId), '+998901234567', 'cash', '60000.00');
```

---

## 5️⃣ Закрытие смены

```javascript
async function closeSession(actualCash) {
  const sessionId = localStorage.getItem('session_id');

  const response = await api.post(
    `/sales/cashier-sessions/${sessionId}/close/`,
    { actual_cash: actualCash }
  );

  const result = response.data;

  // Show results
  showSessionResults(result);

  // Clear session
  localStorage.removeItem('session_id');

  return result;
}

function showSessionResults(result) {
  console.log('Expected:', result.expected_cash);
  console.log('Actual:', result.actual_cash);
  console.log('Difference:', result.cash_difference);

  if (parseFloat(result.cash_difference) > 0) {
    console.log('✅ Излишек!');
  } else if (parseFloat(result.cash_difference) < 0) {
    console.log('❌ Недостача!');
  } else {
    console.log('✅ Точно!');
  }
}

// Usage:
closeSession('122000.00');
```

---

## 6️⃣ Статистика кассиров (админ)

```javascript
async function getCashierStats(dateFrom = null, dateTo = null) {
  let url = '/sales/cashier-sessions/cashier-stats/';

  const params = new URLSearchParams();
  if (dateFrom) params.append('date_from', dateFrom);
  if (dateTo) params.append('date_to', dateTo);

  if (params.toString()) {
    url += '?' + params.toString();
  }

  const response = await api.get(url);

  return response.data.data;
}

function displayCashierStats(stats) {
  console.log(`Период: ${stats.period.from} - ${stats.period.to}`);

  stats.cashiers.forEach((cashier, index) => {
    console.log(`\n${index + 1}. ${cashier.full_name}`);
    console.log(`   Продажи: ${cashier.total_sales} сум`);
    console.log(`   Чеков: ${cashier.sales_count}`);
    console.log(`   Смен: ${cashier.sessions_count}`);
  });
}

// Usage:
getCashierStats('2025-01-01', '2025-01-31')
  .then(stats => displayCashierStats(stats));
```

---

## 7️⃣ Создание кассира (админ)

```javascript
async function createCashier(firstName, lastName, phone) {
  const response = await api.post('/users/employees/', {
    first_name: firstName,
    last_name: lastName,
    phone: phone,
    role: 'cashier'
  });

  return response.data.data.employee;
}

// Usage:
createCashier('Антон', 'Иванов', '+998901234567');
```

---

## 📱 React Example

```jsx
import { useState, useEffect } from 'react';
import axios from 'axios';

const CashierApp = () => {
  const [cashiers, setCashiers] = useState([]);
  const [selectedCashier, setSelectedCashier] = useState(null);
  const [session, setSession] = useState(null);
  const [cart, setCart] = useState([]);

  // Login and get cashiers
  useEffect(() => {
    const login = async () => {
      const response = await axios.post('/api/users/auth/login/', {
        username: 'tokyo_staff',
        password: '12345678'
      }, {
        headers: { 'X-Tenant-Key': 'tokyo_1a12e47a' }
      });

      localStorage.setItem('access_token', response.data.access);
      setCashiers(response.data.available_stores[0].cashiers);
    };

    login();
  }, []);

  // Select cashier
  const handleSelectCashier = (cashierId) => {
    setSelectedCashier(cashierId);
    localStorage.setItem('selected_cashier_id', cashierId);
  };

  // Open session
  const handleOpenSession = async (openingCash) => {
    const response = await api.post('/sales/cashier-sessions/', {
      cashier_id: selectedCashier,
      opening_cash: openingCash
    });

    setSession(response.data.data);
  };

  // Scan product
  const handleScan = async (barcode) => {
    const response = await api.post('/products/scan/', { barcode });
    const product = response.data.data;

    setCart([...cart, {
      id: product.id,
      name: product.name,
      price: product.price,
      quantity: 1
    }]);
  };

  // Create sale
  const handleCreateSale = async () => {
    await api.post('/sales/sales/', {
      session: session.id,
      items: cart.map(item => ({
        product: item.id,
        quantity: item.quantity,
        unit_price: item.price
      })),
      payments: [{
        payment_method: 'cash',
        amount: cart.reduce((sum, item) => sum + item.price * item.quantity, 0)
      }]
    });

    setCart([]);
  };

  return (
    <div>
      {!selectedCashier && (
        <div>
          <h2>Выберите кассира</h2>
          {cashiers.map(cashier => (
            <button key={cashier.id} onClick={() => handleSelectCashier(cashier.id)}>
              {cashier.full_name}
            </button>
          ))}
        </div>
      )}

      {selectedCashier && !session && (
        <div>
          <h2>Открыть смену</h2>
          <input type="number" placeholder="Начальная сумма" id="opening-cash" />
          <button onClick={() => handleOpenSession(document.getElementById('opening-cash').value)}>
            Открыть
          </button>
        </div>
      )}

      {session && (
        <div>
          <h2>Продажа</h2>
          <input type="text" placeholder="Штрихкод" onKeyPress={(e) => {
            if (e.key === 'Enter') handleScan(e.target.value);
          }} />

          <ul>
            {cart.map((item, i) => (
              <li key={i}>{item.name} - {item.price}</li>
            ))}
          </ul>

          <button onClick={handleCreateSale}>Оплатить</button>
        </div>
      )}
    </div>
  );
};
```

---

## 🎯 Готово!

Теперь у вас есть все необходимое для интеграции. Полная документация в `FRONTEND_GUIDE.md`.
