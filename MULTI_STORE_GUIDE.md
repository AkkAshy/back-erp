# Работа с несколькими магазинами (Multi-Tenant)

## 🏪 Архитектура

Система поддерживает **неограниченное количество магазинов** благодаря PostgreSQL schema-based мультитенантности.

### Как это работает:

```
┌─────────────────────────────────────────────┐
│         PostgreSQL Database                  │
├─────────────────────────────────────────────┤
│                                              │
│  📁 public schema (общая)                   │
│  ├── auth_user (все пользователи)           │
│  ├── users_store (все магазины)             │
│  └── users_employee (все сотрудники)        │
│                                              │
│  📁 tenant_asia_market (Магазин 1)          │
│  ├── products_product                       │
│  ├── products_productbatch                  │
│  ├── sales_sale                             │
│  ├── customers_customer                     │
│  └── ...                                    │
│                                              │
│  📁 tenant_shop_24 (Магазин 2)              │
│  ├── products_product                       │
│  ├── products_productbatch                  │
│  ├── sales_sale                             │
│  ├── customers_customer                     │
│  └── ...                                    │
│                                              │
│  📁 tenant_supermarket (Магазин 3)          │
│  └── ...                                    │
└─────────────────────────────────────────────┘
```

### Основные принципы:

1. **Public схема** - хранит владельцев и список всех магазинов
2. **Tenant схемы** - каждый магазин получает свою отдельную "вселенную" данных
3. **Полная изоляция** - товары, продажи, клиенты одного магазина НЕ ВИДНЫ другим
4. **Уникальный ключ** - каждый магазин получает `tenant_key` для доступа к своим данным

---

## 📝 Регистрация нескольких магазинов

### Магазин #1: "Супермаркет Азия"

```bash
curl -X POST http://localhost:8000/api/users/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Иван",
    "last_name": "Петров",
    "owner_phone": "+998901234567",
    "username": "ivan_asia",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "store_name": "Супермаркет Азия",
    "store_address": "ул. Навои, д. 45",
    "store_city": "Ташкент",
    "store_phone": "+998712345678"
  }'
```

**Ответ:**
```json
{
  "status": "success",
  "data": {
    "store": {
      "id": 1,
      "name": "Супермаркет Азия",
      "slug": "asia_market",
      "tenant_key": "asia_market_a3f4b2c1",  ⭐
      "schema_name": "tenant_asia_market"
    },
    "tokens": {
      "access": "eyJ0eXAiOi...",
      "refresh": "eyJ0eXAiOi..."
    }
  }
}
```

### Магазин #2: "Магазин 24"

```bash
curl -X POST http://localhost:8000/api/users/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Мария",
    "last_name": "Иванова",
    "owner_phone": "+998902345678",
    "username": "maria_shop24",
    "password": "SecurePass456!",
    "password_confirm": "SecurePass456!",
    "store_name": "Магазин 24",
    "store_address": "ул. Мирабад, д. 12",
    "store_city": "Ташкент",
    "store_phone": "+998713456789"
  }'
```

**Ответ:**
```json
{
  "status": "success",
  "data": {
    "store": {
      "id": 2,
      "name": "Магазин 24",
      "slug": "shop_24",
      "tenant_key": "shop_24_d5e6f7g8",  ⭐
      "schema_name": "tenant_shop_24"
    },
    "tokens": {
      "access": "eyJ0eXAiOi...",
      "refresh": "eyJ0eXAiOi..."
    }
  }
}
```

### Магазин #3: "Продукты у дома"

```bash
curl -X POST http://localhost:8000/api/users/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Азиз",
    "owner_phone": "+998903456789",
    "username": "aziz_store",
    "password": "SecurePass789!",
    "password_confirm": "SecurePass789!",
    "store_name": "Продукты у дома",
    "store_address": "ул. Чиланзар, д. 8",
    "store_city": "Ташкент",
    "store_phone": "+998714567890"
  }'
```

**Ответ:**
```json
{
  "status": "success",
  "data": {
    "store": {
      "id": 3,
      "name": "Продукты у дома",
      "slug": "produkty_u_doma",
      "tenant_key": "produkty_u_doma_h9i0j1k2",  ⭐
      "schema_name": "tenant_produkty_u_doma"
    }
  }
}
```

---

## 🔑 Работа с tenant_key

### Что такое tenant_key?

`tenant_key` - это **уникальный ключ магазина**, который нужен для всех запросов.

**Формат:**
```
{slug}_{random_8_chars}
```

**Примеры:**
```
asia_market_a3f4b2c1
shop_24_d5e6f7g8
produkty_u_doma_h9i0j1k2
```

### Как использовать в запросах:

**Все запросы (кроме регистрации и входа) требуют два заголовка:**

```javascript
headers: {
  'Authorization': `Bearer ${access_token}`,
  'X-Tenant-Key': tenant_key  // ⭐ ОБЯЗАТЕЛЬНО!
}
```

### Пример: создание товара в "Супермаркет Азия"

```javascript
const token = 'eyJ0eXAiOi...';  // Токен от Ивана
const tenantKey = 'asia_market_a3f4b2c1';  // Ключ магазина Ивана

fetch('http://localhost:8000/api/products/products/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
    'X-Tenant-Key': tenantKey  // ⭐
  },
  body: JSON.stringify({
    name: 'Coca Cola 1.5л',
    category: 1,
    unit: 1,
    cost_price: '8000.00',
    sale_price: '12000.00',
    initial_quantity: '50.000'
  })
});
```

**Результат:**
- Товар создаётся **только в магазине "Супермаркет Азия"**
- Мария (владелец "Магазин 24") его **НЕ ВИДИТ**
- Азиз (владелец "Продукты у дома") его **НЕ ВИДИТ**

---

## 🔐 Изоляция данных

### Полная изоляция

Каждый магазин работает в **своей отдельной вселенной**:

```
Супермаркет Азия (schema: tenant_asia_market)
├── 100 товаров
├── 500 продаж
├── 50 клиентов
└── Товар "Coca Cola 1.5л" ID=1

Магазин 24 (schema: tenant_shop_24)
├── 80 товаров
├── 300 продаж
├── 30 клиентов
└── Товар "Pepsi 1.5л" ID=1  ⭐ Тоже ID=1!

Продукты у дома (schema: tenant_produkty_u_doma)
├── 120 товаров
├── 200 продаж
├── 40 клиентов
└── Товар "Fanta 1.5л" ID=1  ⭐ Тоже ID=1!
```

**Важно:**
- У каждого магазина свои ID (начинаются с 1)
- Данные полностью изолированы
- Невозможно случайно получить данные чужого магазина

### Штрихкоды партий - тоже изолированы!

```
Супермаркет Азия:
└── Партия "BATCH-20241215103045-A3F4B2C1" (Coca Cola)

Магазин 24:
└── Партия "BATCH-20241215103046-D5E6F7G8" (Pepsi)

Продукты у дома:
└── Партия "BATCH-20241215103047-H9I0J1K2" (Fanta)
```

Каждый магазин может сканировать **только свои штрихкоды**.

---

## 🌐 Фронтенд для нескольких магазинов

### Сценарий 1: Отдельные установки (рекомендуется)

Каждый магазин получает **свой сайт**:

```
https://asia-market.erp.uz
https://shop24.erp.uz
https://produkty-u-doma.erp.uz
```

**В каждом сайте:**
```javascript
// Сохраняем при регистрации/входе
localStorage.setItem('tenant_key', 'asia_market_a3f4b2c1');
localStorage.setItem('access_token', '...');

// Используем во всех запросах
const headers = {
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  'X-Tenant-Key': localStorage.getItem('tenant_key')
};
```

### Сценарий 2: Один фронтенд для всех

Один сайт `https://erp.uz` для всех магазинов:

```javascript
// После входа - показываем список магазинов пользователя
fetch('/api/users/auth/my-stores/', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
})
.then(r => r.json())
.then(stores => {
  // Выводим список магазинов
  stores.forEach(store => {
    console.log(store.name, store.tenant_key);
  });

  // Пользователь выбирает магазин
  // Сохраняем tenant_key
  localStorage.setItem('current_tenant_key', selectedStore.tenant_key);
});
```

### Переключение между магазинами

```javascript
function switchStore(newTenantKey) {
  // Меняем tenant_key
  localStorage.setItem('tenant_key', newTenantKey);

  // Перезагружаем данные
  window.location.reload();
}
```

---

## 📊 Примеры запросов

### Получить товары СВОЕГО магазина

```javascript
// Иван (Супермаркет Азия)
fetch('/api/products/products/', {
  headers: {
    'Authorization': 'Bearer <ivan_token>',
    'X-Tenant-Key': 'asia_market_a3f4b2c1'
  }
})
// → Вернёт только товары Супермаркета Азия
```

```javascript
// Мария (Магазин 24)
fetch('/api/products/products/', {
  headers: {
    'Authorization': 'Bearer <maria_token>',
    'X-Tenant-Key': 'shop_24_d5e6f7g8'
  }
})
// → Вернёт только товары Магазина 24
```

### Создать продажу

```javascript
// Азиз (Продукты у дома)
fetch('/api/sales/sales/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <aziz_token>',
    'X-Tenant-Key': 'produkty_u_doma_h9i0j1k2'
  },
  body: JSON.stringify({
    items: [
      {product_id: 1, quantity: 2, price: '15000.00'}
    ],
    payment_method: 'cash'
  })
})
// → Продажа создаётся только в магазине "Продукты у дома"
```

### Сканировать штрихкод партии

```javascript
// Иван сканирует штрихкод в Супермаркете Азия
const scannedBarcode = 'BATCH-20241215103045-A3F4B2C1';

fetch(`/api/products/batches/?barcode=${scannedBarcode}`, {
  headers: {
    'Authorization': 'Bearer <ivan_token>',
    'X-Tenant-Key': 'asia_market_a3f4b2c1'
  }
})
// → Найдёт партию, если она принадлежит Супермаркету Азия
// → Вернёт пустой результат, если партия из другого магазина
```

---

## ⚠️ Важные моменты

### ❌ Что НЕ работает:

```javascript
// НЕТ! Иван НЕ может использовать tenant_key Марии
fetch('/api/products/products/', {
  headers: {
    'Authorization': 'Bearer <ivan_token>',
    'X-Tenant-Key': 'shop_24_d5e6f7g8'  // ❌ Чужой магазин!
  }
})
// → Вернёт ошибку 403 или пустые данные
```

### ✅ Правила безопасности:

1. **Каждый владелец работает только со своим магазином**
2. **tenant_key обязателен** для всех запросов (кроме регистрации/входа)
3. **Данные полностью изолированы** между магазинами
4. **Штрихкоды партий уникальны глобально**, но видны только в своём магазине

---

## 🗄️ База данных

### Создание схем

При регистрации магазина **автоматически**:

1. Создаётся запись в `public.users_store`
2. Генерируется `tenant_key` и `schema_name`
3. Создаётся PostgreSQL схема `tenant_{slug}`
4. Копируются все таблицы в новую схему

### Структура после 3 магазинов:

```sql
-- public схема
SELECT * FROM users_store;
┌────┬────────────────────┬──────────────┬─────────────────────────┬──────────────────────────┐
│ id │ name               │ slug         │ tenant_key              │ schema_name              │
├────┼────────────────────┼──────────────┼─────────────────────────┼──────────────────────────┤
│ 1  │ Супермаркет Азия   │ asia_market  │ asia_market_a3f4b2c1    │ tenant_asia_market       │
│ 2  │ Магазин 24         │ shop_24      │ shop_24_d5e6f7g8        │ tenant_shop_24           │
│ 3  │ Продукты у дома    │ produkty_...  │ produkty_u_doma_h9i0... │ tenant_produkty_u_doma   │
└────┴────────────────────┴──────────────┴─────────────────────────┴──────────────────────────┘

-- tenant_asia_market схема
SELECT * FROM products_product;
┌────┬──────────────────┬─────────────┐
│ id │ name             │ sku         │
├────┼──────────────────┼─────────────┤
│ 1  │ Coca Cola 1.5л   │ COCA-1.5L   │
│ 2  │ Sprite 1л        │ SPRITE-1L   │
└────┴──────────────────┴─────────────┘

-- tenant_shop_24 схема
SELECT * FROM products_product;
┌────┬──────────────────┬─────────────┐
│ id │ name             │ sku         │
├────┼──────────────────┼─────────────┤
│ 1  │ Pepsi 1.5л       │ PEPSI-1.5L  │
│ 2  │ Fanta 1л         │ FANTA-1L    │
└────┴──────────────────┴─────────────┘
```

---

## 🚀 Масштабирование

Система поддерживает **неограниченное количество магазинов**:

- ✅ 10 магазинов
- ✅ 100 магазинов
- ✅ 1000 магазинов
- ✅ 10000+ магазинов

Каждый новый магазин получает:
- Свою схему в PostgreSQL
- Уникальный `tenant_key`
- Полную изоляцию данных
- Автоматическую генерацию штрихкодов для партий

---

## 📋 Итого

### Для установки в несколько магазинов:

1. **Backend** - уже готов! Поддерживает мультитенантность
2. **Регистрация** - каждый владелец регистрируется отдельно
3. **tenant_key** - каждый магазин получает уникальный ключ
4. **Frontend** - сохраняет `tenant_key` и использует в запросах
5. **Изоляция** - данные каждого магазина полностью изолированы

### Два варианта развёртывания:

**Вариант 1: Отдельные сайты**
```
asia-market.erp.uz    → tenant_key: asia_market_a3f4b2c1
shop24.erp.uz         → tenant_key: shop_24_d5e6f7g8
produkty-u-doma.erp.uz → tenant_key: produkty_u_doma_h9i0j1k2
```

**Вариант 2: Один сайт**
```
erp.uz → пользователь выбирает магазин после входа
```

### Безопасность:

✅ **Полная изоляция** данных между магазинами
✅ **Уникальные штрихкоды** для каждого магазина
✅ **Невозможно** получить данные чужого магазина
✅ **PostgreSQL схемы** гарантируют разделение на уровне БД

**Система готова к работе с любым количеством магазинов!** 🎉
