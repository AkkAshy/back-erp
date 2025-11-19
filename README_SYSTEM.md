# 🏪 ERP POS System - Обзор системы

Полное руководство по архитектуре и возможностям системы.

---

## 📋 Оглавление

1. [Архитектура](#архитектура)
2. [Типы аккаунтов](#типы-аккаунтов)
3. [Основные возможности](#основные-возможности)
4. [API Endpoints](#api-endpoints)
5. [Документация](#документация)

---

## 🏗️ Архитектура

### Multi-tenant система

Каждый магазин изолирован:
- Отдельная PostgreSQL схема: `tenant_{slug}`
- Уникальный `tenant_key` для доступа
- JWT аутентификация без store_id в токене
- Tenant определяется через заголовок `X-Tenant-Key`

### При создании магазина автоматически:

```
Store создан
  ↓
├─ Employee (OWNER) - для владельца
├─ User + Employee (STAFF) - общий аккаунт сотрудников
│  └─ Username: {slug}_staff
│  └─ Password: 12345678
└─ CashRegister - общая касса для всех
```

---

## 👥 Типы аккаунтов

### 1. Админ (Owner)
- **Индивидуальный аккаунт**
- Полный доступ к системе
- Может иметь несколько магазинов
- Может создавать сотрудников

**Разрешения:**
- `view_all`, `create_all`, `update_all`, `delete_all`
- `manage_employees`, `manage_store`, `view_analytics`
- `manage_products`, `manage_sales`, `manage_customers`

### 2. Сотрудники (Staff)
- **Общий аккаунт для всех**
- Username: `{slug}_staff`
- Password: `12345678`
- Используется для входа кассиров/складчиков

**Разрешения:**
- `view_products`, `create_sales`, `view_customers`
- `create_customers`, `update_products`, `manage_inventory`

### 3. Кассиры (Employee без User)
- **НЕ имеют аккаунта**
- Только имя + телефон
- Выбираются из списка после входа под Staff аккаунтом
- Все продажи привязываются к конкретному кассиру

---

## 🎯 Основные возможности

### ✅ Для админа:

1. **Управление магазинами**
   - Создание магазинов
   - Просмотр списка своих магазинов
   - Переключение между магазинами

2. **Управление сотрудниками**
   - Создание кассиров (без аккаунта)
   - Создание менеджеров (с аккаунтом)
   - Просмотр списка сотрудников
   - Деактивация сотрудников

3. **Аналитика**
   - Статистика по кассирам за период
   - Топ кассиров по продажам
   - Отчёты по сменам
   - Общая аналитика продаж

4. **Управление товарами**
   - Добавление/редактирование товаров
   - Управление категориями
   - Штрихкодирование
   - Учёт остатков

### ✅ Для кассира:

1. **Работа со сменами**
   - Выбор себя из списка при входе
   - Открытие смены (ввод начальной суммы)
   - Закрытие смены (подсчёт наличных)
   - Просмотр результатов смены

2. **Продажи**
   - Сканирование штрихкодов
   - Добавление товаров в чек
   - Применение скидок
   - Оплата (наличные/карта)
   - Печать чека

3. **Работа с клиентами**
   - Поиск клиента по номеру
   - Добавление нового клиента
   - Просмотр истории покупок

---

## 🔌 API Endpoints

### Аутентификация

```
POST   /api/users/auth/login/           # Вход
POST   /api/users/auth/token/refresh/   # Обновить токен
GET    /api/users/auth/me/              # Текущий пользователь
GET    /api/users/auth/my-stores/       # Мои магазины
```

### Сотрудники

```
GET    /api/users/employees/              # Список сотрудников
POST   /api/users/employees/              # Создать сотрудника
GET    /api/users/employees/{id}/         # Детали сотрудника
PUT    /api/users/employees/{id}/         # Обновить сотрудника
DELETE /api/users/employees/{id}/         # Удалить сотрудника
GET    /api/users/employees/cashiers/     # Список кассиров (для выбора)
```

### Кассовые смены

```
GET    /api/sales/cashier-sessions/                # Список смен
POST   /api/sales/cashier-sessions/                # Открыть смену
GET    /api/sales/cashier-sessions/{id}/           # Детали смены
POST   /api/sales/cashier-sessions/{id}/close/     # Закрыть смену
POST   /api/sales/cashier-sessions/{id}/suspend/   # Приостановить
POST   /api/sales/cashier-sessions/{id}/resume/    # Возобновить
GET    /api/sales/cashier-sessions/current/        # Текущая открытая смена
GET    /api/sales/cashier-sessions/{id}/report/    # Отчёт по смене
GET    /api/sales/cashier-sessions/cashier-stats/  # Статистика кассиров ⭐
```

### Продажи

```
GET    /api/sales/sales/               # Список продаж
POST   /api/sales/sales/               # Создать продажу
GET    /api/sales/sales/{id}/          # Детали продажи
PUT    /api/sales/sales/{id}/          # Обновить продажу
POST   /api/sales/sales/{id}/cancel/   # Отменить продажу
POST   /api/sales/sales/{id}/refund/   # Возврат
```

### Товары

```
GET    /api/products/products/           # Список товаров
POST   /api/products/products/           # Создать товар
GET    /api/products/products/{id}/      # Детали товара
PUT    /api/products/products/{id}/      # Обновить товар
DELETE /api/products/products/{id}/      # Удалить товар
POST   /api/products/scan/               # Сканировать штрихкод ⭐
GET    /api/products/search/?q=name      # Поиск товаров
```

### Клиенты

```
GET    /api/customers/customers/         # Список клиентов
POST   /api/customers/customers/         # Создать клиента
GET    /api/customers/customers/{id}/    # Детали клиента
PUT    /api/customers/customers/{id}/    # Обновить клиента
```

### Аналитика

```
GET    /api/analytics/dashboard/           # Главная панель
GET    /api/analytics/sales-by-period/     # Продажи по периодам
GET    /api/analytics/top-products/        # Топ товаров
GET    /api/analytics/top-customers/       # Топ клиентов
```

---

## 📚 Документация

### Для фронтенд разработчиков:

1. **[FRONTEND_GUIDE.md](FRONTEND_GUIDE.md)** - Полный гайд
   - Детальное описание всех endpoints
   - Примеры запросов и ответов
   - UI/UX рекомендации
   - Обработка ошибок

2. **[QUICK_START.md](QUICK_START.md)** - Быстрый старт
   - Готовые функции на JavaScript
   - React компонент пример
   - Минимум текста, максимум кода

### Технические документы:

3. **[ANALYTICS_API_GUIDE.md](ANALYTICS_API_GUIDE.md)** - Аналитика
4. **[CREATE_SALE_GUIDE.md](CREATE_SALE_GUIDE.md)** - Создание продаж
5. **[BARCODE_SCAN_API.md](BARCODE_SCAN_API.md)** - Сканирование
6. **[LOGIN_CREDENTIALS.md](LOGIN_CREDENTIALS.md)** - Тестовые креды

---

## 🔐 Безопасность

### JWT Tokens

```javascript
// Access token - короткий срок жизни (15 минут)
localStorage.setItem('access_token', 'eyJhbGc...');

// Refresh token - длинный срок (7 дней)
localStorage.setItem('refresh_token', 'eyJhbGc...');
```

### Обязательные заголовки:

```javascript
headers: {
  'Authorization': 'Bearer <access_token>',
  'X-Tenant-Key': '<tenant_key>',
  'Content-Type': 'application/json'
}
```

### Tenant Key:

Получается при логине из `available_stores[0].tenant_key`:
```json
{
  "tenant_key": "tokyo_1a12e47a"
}
```

---

## 🎨 Примеры использования

### React App Structure

```
src/
├── api/
│   ├── axios.js          # Axios instance с interceptors
│   ├── auth.js           # Логин, logout
│   ├── employees.js      # CRUD сотрудников
│   ├── sessions.js       # Кассовые смены
│   ├── sales.js          # Продажи
│   └── products.js       # Товары
├── components/
│   ├── CashierSelection.jsx   # Выбор кассира
│   ├── OpenSession.jsx        # Открытие смены
│   ├── SalesScreen.jsx        # Экран продаж
│   ├── CloseSession.jsx       # Закрытие смены
│   └── CashierStats.jsx       # Аналитика
├── contexts/
│   ├── AuthContext.jsx        # Аутентификация
│   └── CartContext.jsx        # Корзина
└── App.jsx
```

### Axios Setup (api/axios.js)

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://back-erp-gules.vercel.app/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token');
    const tenantKey = localStorage.getItem('tenant_key');

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    if (tenantKey) {
      config.headers['X-Tenant-Key'] = tenantKey;
    }

    return config;
  },
  error => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    // Token expired
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(
          'https://back-erp-gules.vercel.app/api/users/auth/token/refresh/',
          { refresh: refreshToken }
        );

        const { access } = response.data;
        localStorage.setItem('access_token', access);

        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);
      } catch (err) {
        // Refresh failed - logout
        localStorage.clear();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

---

## 🚀 Деплой

### Backend (производство):
```
URL: https://back-erp-gules.vercel.app
```

### Frontend:
```
URL: https://front-erp-gules.vercel.app
```

---

## 📊 Схема работы системы

```
                        ┌─────────────────┐
                        │   Frontend App  │
                        └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
            ┌───────▼──────┐         ┌───────▼──────┐
            │ Admin Panel  │         │   POS App    │
            └───────┬──────┘         └───────┬──────┘
                    │                         │
                    │   HTTP/JSON + JWT      │
                    │   X-Tenant-Key         │
                    │                         │
            ┌───────▼─────────────────────────▼──────┐
            │          Django REST API                │
            │  ┌──────────────────────────────────┐  │
            │  │  TenantMiddleware                │  │
            │  │  - Проверка X-Tenant-Key        │  │
            │  │  - Переключение PostgreSQL схемы │  │
            │  └──────────────────────────────────┘  │
            └────────────────┬────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼────────┐                   ┌─────────▼─────────┐
│ public schema  │                   │ tenant_tokyo      │
│                │                   │                   │
│ - Store        │                   │ - CashRegister   │
│ - User         │                   │ - CashierSession │
│ - Employee     │                   │ - Sale           │
│                │                   │ - SaleItem       │
└────────────────┘                   │ - Payment        │
                                     │ - Product        │
                                     │ - Customer       │
                                     └───────────────────┘
```

---

## 💡 Советы по разработке

### 1. Всегда проверяйте tenant_key
```javascript
if (!localStorage.getItem('tenant_key')) {
  console.error('Tenant key not found!');
  // Redirect to login
}
```

### 2. Обрабатывайте ошибки API
```javascript
try {
  await api.post('/sales/sales/', data);
} catch (error) {
  if (error.response) {
    // Server responded with error
    console.error(error.response.data.message);
  } else if (error.request) {
    // No response from server
    console.error('Network error');
  }
}
```

### 3. Используйте TypeScript интерфейсы
```typescript
interface Cashier {
  id: number;
  full_name: string;
  phone: string;
  role: 'cashier' | 'stockkeeper';
}

interface Session {
  id: number;
  cashier_full_name: string;
  status: 'open' | 'closed' | 'suspended';
  opening_cash: string;
  expected_cash: string;
}
```

---

## 🎯 Roadmap

### В разработке:
- [ ] Поддержка нескольких валют
- [ ] Интеграция с фискальным регистратором
- [ ] Мобильное приложение
- [ ] Офлайн режим
- [ ] Push уведомления

### Планируется:
- [ ] Интеграция с 1С
- [ ] API для маркетплейсов
- [ ] Программа лояльности
- [ ] Бонусная система

---

## 📞 Контакты

При возникновении вопросов или проблем:
1. Проверьте документацию выше
2. Посмотрите примеры в QUICK_START.md
3. Проверьте логи в DevTools

---

**Удачной разработки!** 🚀
