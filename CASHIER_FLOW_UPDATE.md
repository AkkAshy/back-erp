# 🔄 Обновление логики кассиров

## Что изменилось?

### ❌ Старая логика:
- При открытии смены ОБЯЗАТЕЛЬНО выбирать кассира
- Один кассир = одна смена
- Кассир привязывается к CashierSession

### ✅ Новая логика:
- При открытии смены **НЕ НУЖНО** выбирать кассира
- Несколько кассиров могут работать на одной смене одновременно
- Кассир выбирается **ПРИ КАЖДОЙ ПРОДАЖЕ**
- Кассир привязывается к Sale напрямую

---

## Новый флоу для фронтенда

### 1️⃣ Вход под Staff аккаунтом

```javascript
// Логин
const response = await axios.post('/api/users/auth/login/', {
  username: 'tokyo_staff',
  password: '12345678'
}, {
  headers: { 'X-Tenant-Key': 'tokyo_1a12e47a' }
});

// Получаем список кассиров
const cashiers = response.data.available_stores[0].cashiers;
// [
//   {id: 1, full_name: "Иванов Антон", phone: "+998901234567", role: "cashier"},
//   {id: 2, full_name: "Петров Иван", phone: "+998901234568", role: "cashier"},
//   {id: 3, full_name: "Сидоров Петр", phone: "+998901234569", role: "cashier"}
// ]

// Сохраняем список для дальнейшего использования
localStorage.setItem('cashiers', JSON.stringify(cashiers));
```

### 2️⃣ Открытие смены (БЕЗ выбора кассира)

```javascript
// ВНИМАНИЕ: cashier_id больше НЕ НУЖЕН!
const response = await api.post('/api/sales/cashier-sessions/', {
  opening_cash: '100000.00'
  // cashier_id НЕ ПЕРЕДАЁМ!
});

const session = response.data.data;
localStorage.setItem('session_id', session.id);
```

### 3️⃣ Создание продажи (с выбором кассира)

```javascript
// При каждой продаже ОБЯЗАТЕЛЬНО указываем кассира
const createSale = async (cashierId, items) => {
  const sessionId = localStorage.getItem('session_id');

  const response = await api.post('/api/sales/sales/', {
    session: parseInt(sessionId),
    cashier_id: cashierId,  // ⭐ ОБЯЗАТЕЛЬНОЕ ПОЛЕ!
    items: items,
    payments: [{
      payment_method: 'cash',
      amount: totalAmount
    }]
  });

  return response.data.data;
};

// Пример использования
const selectedCashierId = 1; // ID выбранного кассира из localStorage.cashiers
await createSale(selectedCashierId, cartItems);
```

---

## UI рекомендации

### Вариант 1: Выбор кассира при открытии приложения

```jsx
const CashierApp = () => {
  const [selectedCashier, setSelectedCashier] = useState(null);
  const [session, setSession] = useState(null);

  // Шаг 1: Показываем список кассиров
  if (!selectedCashier) {
    return (
      <div>
        <h2>Выберите кассира</h2>
        {cashiers.map(cashier => (
          <button key={cashier.id} onClick={() => setSelectedCashier(cashier)}>
            {cashier.full_name}
          </button>
        ))}
      </div>
    );
  }

  // Шаг 2: Проверяем/открываем смену
  if (!session) {
    return <OpenSessionScreen onOpen={setSession} />;
  }

  // Шаг 3: Экран продаж (с уже выбранным кассиром)
  return <SalesScreen cashier={selectedCashier} session={session} />;
};
```

### Вариант 2: Выбор кассира при каждой продаже

```jsx
const SalesScreen = ({ session }) => {
  const [cart, setCart] = useState([]);
  const [selectedCashier, setSelectedCashier] = useState(null);

  const handleCheckout = async () => {
    if (!selectedCashier) {
      alert('Выберите кассира');
      return;
    }

    await api.post('/api/sales/sales/', {
      session: session.id,
      cashier_id: selectedCashier.id,
      items: cart,
      payments: [...]
    });

    setCart([]);
    setSelectedCashier(null); // Сброс для следующей продажи
  };

  return (
    <div>
      <select onChange={(e) => setSelectedCashier(cashiers.find(c => c.id == e.target.value))}>
        <option value="">Выберите кассира</option>
        {cashiers.map(c => (
          <option key={c.id} value={c.id}>{c.full_name}</option>
        ))}
      </select>

      {/* Корзина */}
      {cart.map(item => <div>{item.name}</div>)}

      <button onClick={handleCheckout}>Оплатить</button>
    </div>
  );
};
```

---

## API изменения

### POST /api/sales/cashier-sessions/ (Открытие смены)

**Старый запрос:**
```json
{
  "cashier_id": 1,
  "opening_cash": "100000.00"
}
```

**Новый запрос:**
```json
{
  "opening_cash": "100000.00"
}
```

`cashier_id` теперь **опционален** и может быть пропущен.

---

### POST /api/sales/sales/ (Создание продажи)

**Старый запрос:**
```json
{
  "session": 1,
  "items": [...],
  "payments": [...]
}
```

**Новый запрос:**
```json
{
  "session": 1,
  "cashier_id": 2,  // ⭐ НОВОЕ ОБЯЗАТЕЛЬНОЕ ПОЛЕ
  "items": [...],
  "payments": [...]
}
```

`cashier_id` теперь **обязателен** при создании продажи.

---

### GET /api/sales/sales/ (Список продаж)

**Ответ теперь включает информацию о кассире:**
```json
{
  "id": 1,
  "receipt_number": "2025-001",
  "cashier_name": "Иванов Антон",  // ⭐ Прямой кассир продажи
  "session_info": {
    "id": 1,
    "cashier_full_name": null  // Может быть null, если смена открыта без кассира
  },
  "total_amount": "50000.00",
  ...
}
```

---

## Аналитика кассиров

GET /api/sales/cashier-sessions/cashier-stats/ - теперь использует прямую связь `Sale.cashier`:

```json
{
  "status": "success",
  "data": {
    "period": {
      "from": "2025-01-01",
      "to": "2025-01-31"
    },
    "cashiers": [
      {
        "id": 1,
        "full_name": "Иванов Антон",
        "phone": "+998901234567",
        "total_sales": "5000000.00",
        "cash_sales": "3000000.00",
        "card_sales": "2000000.00",
        "sales_count": 150,
        "sessions_count": 20
      }
    ]
  }
}
```

---

## Миграция существующих данных

Если у вас есть старые продажи без `cashier`, система попытается получить кассира из `session.cashier`.

Если оба поля пусты, `cashier_name` вернёт "Не указан".

---

## Тестирование

### Тест 1: Открытие смены без кассира

```bash
curl -X POST https://back-erp-gules.vercel.app/api/sales/cashier-sessions/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: tokyo_1a12e47a" \
  -H "Content-Type: application/json" \
  -d '{
    "opening_cash": "100000.00"
  }'
```

Ожидаем: 201 Created

### Тест 2: Создание продажи с кассиром

```bash
curl -X POST https://back-erp-gules.vercel.app/api/sales/sales/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: tokyo_1a12e47a" \
  -H "Content-Type: application/json" \
  -d '{
    "session": 1,
    "cashier_id": 2,
    "items": [
      {
        "product": 1,
        "quantity": 1,
        "unit_price": "50000.00"
      }
    ],
    "payments": [
      {
        "payment_method": "cash",
        "amount": "50000.00"
      }
    ]
  }'
```

Ожидаем: 201 Created с `cashier_name` в ответе

### Тест 3: Создание продажи БЕЗ кассира

```bash
# Без cashier_id - должно быть ошибка
curl -X POST https://back-erp-gules.vercel.app/api/sales/sales/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: tokyo_1a12e47a" \
  -H "Content-Type: application/json" \
  -d '{
    "session": 1,
    "items": [...],
    "payments": [...]
  }'
```

Ожидаем: 400 Bad Request - "This field is required."

---

## Вопросы и ответы

**Q: Что если кассир уходит с смены раньше?**
A: Это не проблема, так как смена общая для всех. Кассир просто перестаёт выбирать себя при продажах.

**Q: Как закрыть смену?**
A: Также как и раньше - любой с доступом может закрыть смену:

```javascript
await api.post(`/api/sales/cashier-sessions/${sessionId}/close/`, {
  actual_cash: '122000.00'
});
```

**Q: Можно ли не указывать кассира при продаже?**
A: Нет, `cashier_id` теперь обязателен. Это позволяет точно отслеживать кто делал продажи.

**Q: Как получить статистику по конкретному кассиру?**
A: Используйте endpoint `/api/sales/cashier-sessions/cashier-stats/?date_from=2025-01-01&date_to=2025-01-31` - он вернёт список кассиров отсортированный по сумме продаж.

---

**Дата обновления:** 2025-01-19
