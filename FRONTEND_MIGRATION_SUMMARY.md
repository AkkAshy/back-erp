# Summary: Миграция фронтенда на новый бэкенд

## 📋 Что сделано

### 1. Копирование фронтенда

```bash
cd /Users/akkanat/Projects/erp_v2
cp -r frontend new_frontend
```

✅ Создана папка `/Users/akkanat/Projects/erp_v2/new_frontend`

---

### 2. Обновлены файлы API конфигурации

#### ✅ `src/shared/api/base/config.ts`

**Было:**
```typescript
export const API_BASE_URL = "https://erp.avtoxizmet.uz";
```

**Стало:**
```typescript
export const API_BASE_URL = import.meta.env.VITE_BASE_URL || "http://localhost:8000/api";
```

---

#### ✅ `src/shared/api/auth/tokenService.ts`

**Добавлено:**
```typescript
// Новые функции для работы с tenant_key
export const setTenantKey = (tenantKey: string) => {
  localStorage.setItem("tenant_key", tenantKey);
};

export const getTenantKey = () => {
  return localStorage.getItem("tenant_key");
};
```

**Обновлено:**
```typescript
export const clearTokens = () => {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("tenant_key");  // ⭐ Добавлено
};

// Обновлён путь API
export const refreshTokens = async (): Promise<string | null> => {
  const res = await api.post("/users/auth/token/refresh/", {...});  // ⭐ Был /users/token/refresh/
  // ...
};
```

---

#### ✅ `src/shared/api/auth/authInterceptor.ts`

**Добавлено:**
```typescript
import { getTenantKey } from "./tokenService";  // ⭐ Импорт

export const attachAuthInterceptor = (api) => {
  api.interceptors.request.use((config) => {
    // Добавляем токен
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // ⭐ Добавляем X-Tenant-Key (кроме auth эндпоинтов)
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
  // ...
};
```

---

## 📄 Документация создана

### 1. **FRONTEND_ADAPTATION_GUIDE.md** ⭐ ГЛАВНЫЙ ГАЙД

Полное руководство по адаптации включает:

- ✅ Обзор всех изменений
- ✅ Пошаговая инструкция
- ✅ Примеры кода для каждого компонента
- ✅ Маппинг старых/новых API эндпоинтов
- ✅ Чеклист для проверки

**Разделы:**
1. Обновление API конфигурации
2. Адаптация формы регистрации
3. Адаптация формы логина
4. Адаптация формы создания товара
5. Отображение штрихкодов партий
6. Обновление всех API эндпоинтов

---

## 🔑 Ключевые изменения в API

### Старый → Новый

| Компонент | Старый endpoint | Новый endpoint | Изменения |
|-----------|----------------|----------------|-----------|
| Регистрация | `POST /users/register/` | `POST /api/users/auth/register/` | + tenant_key в ответе, одно окно |
| Логин | `POST /users/login/` | `POST /api/users/auth/login/` | + tenant_key в ответе |
| Обновление токена | `POST /users/token/refresh/` | `POST /api/users/auth/token/refresh/` | - |
| Товары (список) | `GET /products/` | `GET /api/products/products/` | Требует X-Tenant-Key |
| Товары (создание) | `POST /products/` | `POST /api/products/products/` | Одно окно с партиями |
| Продажи | `GET/POST /sales/` | `GET/POST /api/sales/sales/` | Требует X-Tenant-Key |
| Клиенты | `GET/POST /customers/` | `GET/POST /api/customers/customers/` | Требует X-Tenant-Key |

---

## ⭐ Новый функционал бэкенда

### 1. Multi-tenant архитектура

**Теперь:**
- Каждый магазин получает уникальный `tenant_key`
- Все запросы требуют заголовок `X-Tenant-Key`
- Полная изоляция данных между магазинами

**Пример:**
```typescript
headers: {
  'Authorization': 'Bearer eyJ0eXAi...',
  'X-Tenant-Key': 'asia_market_a3f4b2c1'  // ⭐
}
```

---

### 2. Регистрация в одном окне

**Было:** 3 запроса (user → store → employee)

**Стало:** 1 запрос со всеми данными:

```json
{
  // Личные данные
  "first_name": "Иван",
  "owner_phone": "+998901234567",
  "username": "ivan",
  "password": "...",

  // Данные магазина
  "store_name": "Супермаркет Азия",
  "store_address": "...",
  "store_city": "Ташкент",
  "store_phone": "+998712345678"
}
```

**Ответ включает tenant_key:**
```json
{
  "data": {
    "store": {
      "tenant_key": "asia_market_a3f4b2c1"  // ⭐ ВАЖНО!
    },
    "tokens": {...}
  }
}
```

---

### 3. Создание товара в одном окне

**Было:** 3-4 запроса (product → pricing → inventory → batch)

**Стало:** 1 запрос:

```json
{
  "name": "Coca Cola 1.5л",
  "category": 1,
  "unit": 1,

  // Цены (одним запросом!)
  "cost_price": "8000.00",
  "sale_price": "12000.00",

  // Партия (одним запросом!)
  "initial_quantity": "50.000",
  "batch_number": "BATCH-001",
  "expiry_date": "2025-12-31"
}
```

---

### 4. Автоматические штрихкоды для партий

**Новая возможность:**

Каждая партия автоматически получает уникальный штрихкод:

```json
{
  "batches": [
    {
      "id": 456,
      "batch_number": "BATCH-001",
      "barcode": "BATCH-20241215103045-A3F4B2C1"  // ⭐ Автоматически!
    }
  ]
}
```

**Формат:** `BATCH-{timestamp}-{random}`

---

## 🎯 Что нужно доделать на фронтенде

### Pending задачи:

1. **Форма регистрации** (`src/features/Auth/Register/`)
   - [ ] Добавить поля магазина (store_name, store_address и т.д.)
   - [ ] Сохранять `tenant_key` после успешной регистрации

2. **Форма логина** (`src/features/Auth/Login/`)
   - [ ] Обновить endpoint на `/api/users/auth/login/`
   - [ ] Сохранять `tenant_key` из ответа

3. **Форма создания товара** (`src/shared/ui/CreateProduct/`)
   - [ ] Добавить поля цен (cost_price, sale_price)
   - [ ] Добавить поля партии (initial_quantity, batch_number, expiry_date)
   - [ ] Упростить submit (один запрос вместо нескольких)

4. **Отображение штрихкодов**
   - [ ] Создать компонент `BatchBarcode` с использованием jsbarcode
   - [ ] Добавить отображение штрихкодов в списке товаров

5. **Обновление всех API путей**
   - [ ] Обновить пути в entities/features/widgets
   - [ ] Добавить `/api/` префикс ко всем запросам

---

## 📚 Ссылки на документацию

### Для фронтенд-разработчика:

1. **[FRONTEND_ADAPTATION_GUIDE.md](FRONTEND_ADAPTATION_GUIDE.md)** ⭐ ГЛАВНЫЙ ГАЙД
   - Полное руководство по адаптации
   - Примеры кода
   - Чеклист

2. **[FRONTEND_REGISTRATION_GUIDE.md](FRONTEND_REGISTRATION_GUIDE.md)**
   - Готовый React компонент регистрации
   - CSS стили
   - Примеры использования

3. **[PRODUCT_CREATION_GUIDE.md](PRODUCT_CREATION_GUIDE.md)**
   - Готовый React компонент создания товара
   - Примеры API запросов

4. **[FRONTEND_BARCODE_PRINTING_GUIDE.md](FRONTEND_BARCODE_PRINTING_GUIDE.md)**
   - Работа со штрихкодами
   - Компонент для отображения
   - Печать этикеток

### Для понимания бэкенда:

5. **[MULTI_STORE_GUIDE.md](MULTI_STORE_GUIDE.md)**
   - Как работает мультитенантность
   - Примеры для нескольких магазинов

6. **[REGISTRATION_EXAMPLE.md](REGISTRATION_EXAMPLE.md)**
   - Примеры API регистрации

7. **[BATCH_BARCODE_AUTO_GENERATION.md](BATCH_BARCODE_AUTO_GENERATION.md)**
   - Как работают штрихкоды партий

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd /Users/akkanat/Projects/erp_v2/new_frontend
npm install
```

### 2. Запуск development сервера

```bash
npm run dev
```

### 3. Проверка подключения к бэкенду

Убедитесь что бэкенд запущен:

```bash
cd /Users/akkanat/Projects/erp_v2/new_backend
source venv/bin/activate
python manage.py runserver
```

Backend: `http://localhost:8000`
Frontend: `http://localhost:5173`

---

## ✅ Текущий статус

### Готово ✅

- [x] Копирование фронтенда в `new_frontend`
- [x] Обновление API_BASE_URL
- [x] Добавление функций работы с tenant_key
- [x] Добавление X-Tenant-Key в interceptor
- [x] Создание полной документации

### В процессе 🔄

- [ ] Адаптация форм регистрации/логина
- [ ] Адаптация формы создания товара
- [ ] Добавление компонента отображения штрихкодов
- [ ] Обновление всех API эндпоинтов

---

## 💡 Важно помнить

### 1. tenant_key обязателен!

```typescript
// ✅ Правильно
fetch('/api/products/products/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'X-Tenant-Key': tenantKey
  }
});

// ❌ Неправильно (без X-Tenant-Key)
fetch('/api/products/products/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### 2. Сохранять tenant_key после логина/регистрации

```typescript
// После успешной регистрации или логина:
setTenantKey(response.data.data.store.tenant_key);
```

### 3. Штрихкоды генерируются автоматически

Не нужно генерировать на фронтенде - просто отображайте!

```typescript
<BatchBarcode barcode={batch.barcode} />
```

---

## 🎉 Итого

**Базовая инфраструктура готова!**

Осталось:
1. Адаптировать формы
2. Обновить API пути
3. Добавить отображение штрихкодов

Все примеры кода и руководства есть в [FRONTEND_ADAPTATION_GUIDE.md](FRONTEND_ADAPTATION_GUIDE.md)!
