# Гайд по адаптации фронтенда под новый бэкенд

## 📋 Обзор изменений

Старый бэкенд (`/backend`) → Новый бэкенд (`/new_backend`)

**Ключевые изменения:**
1. ✅ Multi-tenant архитектура (X-Tenant-Key)
2. ✅ Новая структура API endpoints
3. ✅ Регистрация в одном окне
4. ✅ Создание товара в одном окне с партиями
5. ✅ Автоматическая генерация штрихкодов для партий

---

## 🎯 План адаптации

### Шаг 1: Копирование старого фронтенда

```bash
cd /Users/akkanat/Projects/erp_v2
cp -r frontend new_frontend
cd new_frontend
```

### Шаг 2: Обновление зависимостей

Убедитесь, что есть библиотека для штрихкодов (уже установлена):
```json
{
  "dependencies": {
    "jsbarcode": "^3.12.1"
  }
}
```

---

## ⚙️ Изменения в API конфигурации

### 1. Обновить базовый URL

**Файл:** `src/shared/api/base/config.ts`

```typescript
export const API_BASE_URL =
  import.meta.env.VITE_BASE_URL || "http://localhost:8000/api";
```

**Было:**
```typescript
"https://erp.avtoxizmet.uz"
```

---

### 2. Добавить поддержку tenant_key

**Файл:** `src/shared/api/auth/tokenService.ts`

**Добавить новые функции:**

```typescript
// ⭐ Новые функции для работы с tenant_key
export const setTenantKey = (tenantKey: string) => {
  localStorage.setItem("tenant_key", tenantKey);
};

export const getTenantKey = () => {
  return localStorage.getItem("tenant_key");
};
```

**Обновить clearTokens:**

```typescript
export const clearTokens = () => {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("tenant_key");  // ⭐ Добавить
};
```

**Обновить путь в refreshTokens:**

```typescript
export const refreshTokens = async (): Promise<string | null> => {
  // ...
  const res = await api.post("/users/auth/token/refresh/", {  // ⭐ Был /users/token/refresh/
    refresh: refreshToken,
  });
  // ...
};
```

---

### 3. Добавить X-Tenant-Key в interceptor

**Файл:** `src/shared/api/auth/authInterceptor.ts`

**Импортировать getTenantKey:**

```typescript
import { getAccessToken, setAccessToken, getTenantKey } from "./tokenService";
```

**Обновить request interceptor:**

```typescript
export const attachAuthInterceptor = (api: ReturnType<typeof axios.create>) => {
  api.interceptors.request.use((config) => {
    // Добавляем токен авторизации
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // ⭐ Добавляем X-Tenant-Key для всех запросов (кроме регистрации и логина)
    const isAuthEndpoint =
      config.url?.includes('/auth/register') ||
      config.url?.includes('/auth/login') ||
      config.url?.includes('/auth/token/refresh');

    if (!isAuthEndpoint) {
      const tenantKey = getTenantKey();
      if (tenantKey) {
        config.headers['X-Tenant-Key'] = tenantKey;
      }
    }

    return config;
  });

  // ... остальной код
};
```

---

## 🔐 Адаптация формы регистрации

### Структура нового API регистрации

**Endpoint:** `POST /api/users/auth/register/`

**Старый запрос (несколько шагов):**
```json
// Шаг 1: Регистрация
POST /users/register/
{
  "username": "ivan",
  "password": "...",
  // ...
}

// Шаг 2: Создание магазина
POST /stores/
{
  "name": "Мой магазин",
  // ...
}
```

**Новый запрос (одно окно):**
```json
POST /api/users/auth/register/
{
  // Личные данные владельца
  "first_name": "Иван",
  "last_name": "Петров",
  "middle_name": "Сергеевич",
  "owner_phone": "+998901234567",
  "email": "ivan@example.com",

  // Данные для входа
  "username": "ivan_owner",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",

  // Данные магазина
  "store_name": "Супермаркет Азия",
  "store_address": "ул. Навои, д. 45",
  "store_city": "Ташкент",
  "store_region": "Ташкентская область",
  "store_phone": "+998712345678",
  "store_email": "info@asiamarket.uz",
  "store_legal_name": "ООО Супермаркет Азия",
  "store_tax_id": "123456789"
}
```

**Новый ответ:**
```json
{
  "status": "success",
  "message": "Регистрация успешна",
  "data": {
    "user": {
      "id": 1,
      "username": "ivan_owner",
      "full_name": "Петров Иван"
    },
    "store": {
      "id": 1,
      "name": "Супермаркет Азия",
      "slug": "asia_market",
      "tenant_key": "asia_market_a3f4b2c1",  // ⭐ ВАЖНО!
      "city": "Ташкент",
      "region": "Ташкентская область"
    },
    "employee": {
      "id": 1,
      "role": "owner",
      "phone": "+998901234567"
    },
    "tokens": {
      "access": "eyJ0eXAiOi...",
      "refresh": "eyJ0eXAiOi..."
    }
  }
}
```

### Обновление RegisterForm

**Файл:** `src/features/Auth/Register/ui/RegisterForm.tsx`

**Ключевые изменения:**

1. **Добавить поля магазина в форму:**

```typescript
const [formData, setFormData] = useState({
  // Личные данные
  first_name: '',
  last_name: '',
  middle_name: '',
  owner_phone: '',
  email: '',

  // Данные для входа
  username: '',
  password: '',
  password_confirm: '',

  // Данные магазина
  store_name: '',
  store_address: '',
  store_city: '',
  store_region: '',
  store_phone: '',
  store_email: '',
  store_legal_name: '',
  store_tax_id: ''
});
```

2. **Сохранить tenant_key после регистрации:**

```typescript
import { setAccessToken, setRefreshToken, setTenantKey } from '@/shared/api/auth/tokenService';

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  try {
    const response = await api.post('/users/auth/register/', formData);

    if (response.data.status === 'success') {
      // Сохраняем токены
      setAccessToken(response.data.data.tokens.access);
      setRefreshToken(response.data.data.tokens.refresh);

      // ⭐ ВАЖНО: Сохраняем tenant_key
      setTenantKey(response.data.data.store.tenant_key);

      // Сохраняем дополнительно для удобства
      localStorage.setItem('user', JSON.stringify(response.data.data.user));
      localStorage.setItem('store', JSON.stringify(response.data.data.store));

      // Редирект в панель
      navigate('/dashboard');
    }
  } catch (error) {
    console.error('Registration error:', error);
  }
};
```

---

## 🔑 Адаптация формы логина

**Endpoint:** `POST /api/users/auth/login/`

**Старый:**
```
POST /users/login/
```

**Новый:**
```
POST /api/users/auth/login/
```

**Новый ответ включает tenant_key:**
```json
{
  "status": "success",
  "data": {
    "user": {...},
    "store": {
      "tenant_key": "asia_market_a3f4b2c1"  // ⭐ ВАЖНО!
    },
    "tokens": {
      "access": "...",
      "refresh": "..."
    }
  }
}
```

**Файл:** `src/features/Auth/Login/ui/index.tsx` или `api/useLogin.ts`

**Обновить сохранение данных после логина:**

```typescript
import { setTenantKey } from '@/shared/api/auth/tokenService';

const handleLogin = async (credentials) => {
  const response = await api.post('/users/auth/login/', credentials);

  if (response.data.status === 'success') {
    setAccessToken(response.data.data.tokens.access);
    setRefreshToken(response.data.data.tokens.refresh);

    // ⭐ ВАЖНО: Сохраняем tenant_key
    setTenantKey(response.data.data.store.tenant_key);

    navigate('/dashboard');
  }
};
```

---

## 📦 Адаптация формы создания товара

### Структура нового API создания товара

**Endpoint:** `POST /api/products/products/`

**Старый подход (несколько запросов):**
```json
// Шаг 1: Создать товар
POST /products/
{
  "name": "Coca Cola",
  "price": "12000"
}

// Шаг 2: Установить цены
POST /products/{id}/pricing/
{...}

// Шаг 3: Создать партию
POST /batches/
{...}
```

**Новый подход (одно окно):**
```json
POST /api/products/products/
{
  // Основная информация
  "name": "Coca Cola 1.5л",
  "sku": "COCA-1.5L",  // Опционально (генерируется автоматически)
  "barcode": "4870123456789",  // Опционально
  "category": 1,
  "unit": 1,

  // Цены (обязательно)
  "cost_price": "8000.00",
  "sale_price": "12000.00",
  "wholesale_price": "10000.00",  // Опционально
  "tax_rate": "12.00",  // Опционально

  // Количество (обязательно)
  "initial_quantity": "50.000",

  // Настройки учёта (опционально)
  "min_quantity": "10.000",
  "max_quantity": "200.000",
  "track_inventory": true,

  // Партия (опционально)
  "batch_number": "BATCH-001",  // Генерируется автоматически
  "expiry_date": "2025-12-31",
  "supplier": 3
}
```

**Ответ:**
```json
{
  "id": 123,
  "name": "Coca Cola 1.5л",
  "sku": "COCA-1.5L",

  "pricing": {
    "cost_price": "8000.00",
    "sale_price": "12000.00",
    "margin": "50.00",
    "profit": "4000.00"
  },

  "inventory": {
    "quantity": "50.000",
    "min_quantity": "10.000",
    "stock_status": "in_stock"
  },

  "batches": [
    {
      "id": 456,
      "batch_number": "BATCH-001",
      "barcode": "BATCH-20241215103045-A3F4B2C1",  // ⭐ Автоматически!
      "quantity": "50.000",
      "expiry_date": "2025-12-31"
    }
  ]
}
```

### Обновление CreateProduct компонента

**Файл:** `src/shared/ui/CreateProduct/index.tsx`

**Ключевые изменения:**

1. **Добавить новые поля:**

```typescript
const [formData, setFormData] = useState({
  // Основное
  name: '',
  category: '',
  unit: '',
  sku: '',  // Опционально
  barcode: '',

  // Цены (обязательно!)
  cost_price: '',
  sale_price: '',
  wholesale_price: '',
  tax_rate: '0',

  // Количество (обязательно!)
  initial_quantity: '',

  // Настройки
  min_quantity: '0',
  max_quantity: '',
  track_inventory: true,

  // Партия
  batch_number: '',  // Опционально
  expiry_date: '',
  supplier: ''
});
```

2. **Упростить submit:**

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  try {
    const response = await api.post('/products/products/', formData);

    if (response.status === 201) {
      const product = response.data;

      // Товар создан!
      console.log('Товар создан:', product.name);
      console.log('Партия создана:', product.batches[0].batch_number);
      console.log('Штрихкод партии:', product.batches[0].barcode);  // ⭐

      // Можно сразу распечатать этикетку с штрихкодом
      navigate(`/products/${product.id}`);
    }
  } catch (error) {
    console.error('Error creating product:', error);
  }
};
```

---

## 📊 Обновление API эндпоинтов

### Маппинг старых эндпоинтов на новые

| Старый endpoint | Новый endpoint | Примечания |
|----------------|----------------|------------|
| `POST /users/register/` | `POST /api/users/auth/register/` | Теперь в одном запросе с магазином |
| `POST /users/login/` | `POST /api/users/auth/login/` | Возвращает tenant_key |
| `POST /users/token/refresh/` | `POST /api/users/auth/token/refresh/` | - |
| `GET /products/` | `GET /api/products/products/` | Требует X-Tenant-Key |
| `POST /products/` | `POST /api/products/products/` | Создание в одно окно |
| `GET /sales/` | `GET /api/sales/sales/` | Требует X-Tenant-Key |
| `POST /sales/` | `POST /api/sales/sales/` | Требует X-Tenant-Key |
| `GET /customers/` | `GET /api/customers/customers/` | Требует X-Tenant-Key |

**Важно:** Все эндпоинты (кроме регистрации/логина) требуют заголовок `X-Tenant-Key`!

---

## 🏷️ Отображение штрихкодов партий

### Установка библиотеки

Уже установлено:
```json
"jsbarcode": "^3.12.1"
```

### Компонент для отображения штрихкода

**Создать:** `src/shared/ui/BatchBarcode/index.tsx`

```typescript
import { useEffect, useRef } from 'react';
import JsBarcode from 'jsbarcode';

interface BatchBarcodeProps {
  barcode: string;
  width?: number;
  height?: number;
  displayValue?: boolean;
}

export const BatchBarcode = ({
  barcode,
  width = 2,
  height = 60,
  displayValue = true
}: BatchBarcodeProps) => {
  const barcodeRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (barcodeRef.current && barcode) {
      JsBarcode(barcodeRef.current, barcode, {
        format: 'CODE128',
        width,
        height,
        displayValue,
        fontSize: 14,
        margin: 10
      });
    }
  }, [barcode, width, height, displayValue]);

  return <svg ref={barcodeRef}></svg>;
};
```

### Использование в компоненте

```typescript
import { BatchBarcode } from '@/shared/ui/BatchBarcode';

function ProductBatchList({ batches }) {
  return (
    <div>
      {batches.map(batch => (
        <div key={batch.id}>
          <h3>{batch.batch_number}</h3>

          {/* Отображение штрихкода */}
          <BatchBarcode barcode={batch.barcode} />

          <p>Количество: {batch.quantity}</p>
          <p>Срок годности: {batch.expiry_date}</p>
        </div>
      ))}
    </div>
  );
}
```

---

## 🔄 Обновление .env файла

**Файл:** `.env`

```env
VITE_BASE_URL=http://localhost:8000/api
```

**Для production:**
```env
VITE_BASE_URL=https://your-domain.com/api
```

---

## ✅ Чеклист адаптации

### API конфигурация
- [x] Обновить `API_BASE_URL` на `http://localhost:8000/api`
- [x] Добавить `setTenantKey` и `getTenantKey` в `tokenService.ts`
- [x] Добавить `X-Tenant-Key` в `authInterceptor.ts`
- [x] Обновить `clearTokens()` для очистки tenant_key

### Формы аутентификации
- [ ] Обновить форму регистрации (добавить поля магазина)
- [ ] Сохранять `tenant_key` после регистрации
- [ ] Обновить форму логина
- [ ] Сохранять `tenant_key` после логина

### Формы товаров
- [ ] Обновить форму создания товара (добавить поля цен и партии)
- [ ] Упростить submit (один запрос вместо нескольких)
- [ ] Добавить компонент отображения штрихкодов
- [ ] Обновить список товаров для отображения партий

### API эндпоинты
- [ ] Обновить все API пути с `/users/` на `/api/users/auth/`
- [ ] Обновить все пути товаров с `/products/` на `/api/products/products/`
- [ ] Обновить все пути продаж с `/sales/` на `/api/sales/sales/`
- [ ] Обновить все пути клиентов на `/api/customers/customers/`

### Тестирование
- [ ] Тест регистрации нового магазина
- [ ] Тест логина существующего пользователя
- [ ] Тест создания товара с партией
- [ ] Тест отображения штрихкодов
- [ ] Тест мультитенантности (два магазина не видят данные друг друга)

---

## 🚀 Запуск

### Backend

```bash
cd /Users/akkanat/Projects/erp_v2/new_backend
source venv/bin/activate
python manage.py runserver
```

Backend доступен на: `http://localhost:8000`

### Frontend

```bash
cd /Users/akkanat/Projects/erp_v2/new_frontend
npm install  # Если нужно
npm run dev
```

Frontend доступен на: `http://localhost:5173` (или другой порт Vite)

---

## 📚 Дополнительные гайды

- **REGISTRATION_EXAMPLE.md** - Примеры API регистрации
- **FRONTEND_REGISTRATION_GUIDE.md** - Готовый React компонент регистрации
- **PRODUCT_CREATION_GUIDE.md** - Примеры API создания товаров
- **BATCH_BARCODE_AUTO_GENERATION.md** - Работа с штрихкодами партий
- **MULTI_STORE_GUIDE.md** - Мультитенантность для нескольких магазинов
- **FRONTEND_BARCODE_PRINTING_GUIDE.md** - Печать этикеток со штрихкодами

---

## 💡 Важные примечания

### 1. tenant_key обязателен!

Все запросы (кроме регистрации/логина) требуют `X-Tenant-Key`:

```typescript
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'X-Tenant-Key': tenantKey  // ⭐ ОБЯЗАТЕЛЬНО!
}
```

### 2. Штрихкоды генерируются автоматически

Каждая партия получает уникальный штрихкод:
```
BATCH-20241215103045-A3F4B2C1
```

Не нужно генерировать на фронтенде - просто отобразите!

### 3. Одна форма = один запрос

- Регистрация: Вся информация (владелец + магазин) в одном запросе
- Товар: Вся информация (товар + цены + партия) в одном запросе

### 4. Изоляция данных

Каждый магазин видит только свои данные благодаря `tenant_key`.

---

## 🎉 Готово!

После выполнения всех шагов фронтенд будет полностью адаптирован под новый бэкенд с поддержкой:

- ✅ Мультитенантности
- ✅ Регистрации в одном окне
- ✅ Создания товаров в одном окне
- ✅ Автоматических штрихкодов для партий
- ✅ Полной изоляции данных между магазинами
