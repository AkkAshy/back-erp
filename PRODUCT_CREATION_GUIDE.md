# Создание товара - одно окно

## Описание

Владелец заполняет **одну форму** со всей информацией о товаре и получает:
- ✅ Товар с полными данными
- ✅ Цены (себестоимость, продажная, оптовая)
- ✅ Первая партия с количеством
- ✅ Настройки учёта остатков
- ✅ Штрихкод (если указан)

**Товар сразу готов к продаже!**

---

## API Endpoint

```
POST /api/products/products/
```

**Требуется аутентификация:**
```
Authorization: Bearer <access_token>
X-Tenant-Key: <tenant_key>
```

---

## Минимальный запрос (только обязательные поля)

```json
{
  "name": "Coca Cola 1.5л",
  "category": 1,
  "unit": 1,
  "cost_price": "8000.00",
  "sale_price": "12000.00",
  "initial_quantity": "50.000"
}
```

Товар создан! SKU и номер партии сгенерируются автоматически.

---

## Полный запрос (все поля)

```json
{
  "name": "Coca Cola 1.5л",
  "sku": "COCA-1.5L",
  "barcode": "4870123456789",
  "description": "Газированный напиток Кока-Кола 1.5 литра",
  "category": 1,
  "unit": 1,

  "cost_price": "8000.00",
  "sale_price": "12000.00",
  "wholesale_price": "10000.00",
  "tax_rate": "12.00",

  "initial_quantity": "50.000",
  "min_quantity": "10.000",
  "max_quantity": "200.000",
  "track_inventory": true,

  "batch_number": "BATCH-001-2024",
  "expiry_date": "2025-12-31",
  "supplier": 3,

  "weight": "1.500",
  "volume": "1.500",
  "is_featured": false
}
```

---

## Поля формы создания товара

### 📦 Основная информация (обязательно)

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `name` | string | ✅ Да | Название товара |
| `category` | int | ✅ Да | ID категории |
| `unit` | int | ✅ Да | ID единицы измерения (шт, кг, л) |

### 🏷️ Идентификация (опционально)

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `sku` | string | ❌ Нет | Артикул (уникальный, генерируется авто) |
| `barcode` | string | ❌ Нет | Штрихкод |
| `description` | text | ❌ Нет | Описание товара |

### 💰 Цены (обязательно)

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `cost_price` | decimal | ✅ Да | Себестоимость (закупочная цена) |
| `sale_price` | decimal | ✅ Да | Цена продажи |
| `wholesale_price` | decimal | ❌ Нет | Оптовая цена |
| `tax_rate` | decimal | ❌ Нет | Налог (%, по умолчанию 0) |

### 📊 Количество (обязательно)

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `initial_quantity` | decimal | ✅ Да | Начальное количество (первая партия) |

### ⚙️ Настройки учёта (опционально)

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `min_quantity` | decimal | ❌ Нет | Минимум для уведомлений (по умолчанию 0) |
| `max_quantity` | decimal | ❌ Нет | Максимальный остаток |
| `track_inventory` | boolean | ❌ Нет | Вести учёт (по умолчанию true) |

### 📦 Партия (опционально)

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `batch_number` | string | ❌ Нет | Номер партии (генерируется авто) |
| `expiry_date` | date | ❌ Нет | Срок годности (YYYY-MM-DD) |
| `supplier` | int | ❌ Нет | ID поставщика |

### 📏 Дополнительно (опционально)

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `weight` | decimal | ❌ Нет | Вес (кг) |
| `volume` | decimal | ❌ Нет | Объём (л) |
| `is_featured` | boolean | ❌ Нет | Популярный товар |

---

## Что происходит при создании

### Backend создаёт (в 1 транзакции):

1. **Product** - основная запись товара
   - name, sku (авто), barcode, description
   - category, unit, weight, volume
   - Генерируется slug автоматически

2. **ProductPricing** - цены товара
   - cost_price, sale_price, wholesale_price, tax_rate
   - Автоматически считается margin и profit

3. **ProductInventory** - настройки учёта
   - min_quantity, max_quantity, track_inventory
   - quantity = 0 (изначально)

4. **ProductBatch** - первая партия
   - batch_number (авто), initial_quantity
   - expiry_date, supplier, purchase_price
   - **Автоматически обновляет quantity в ProductInventory!**

5. **ProductBarcode** - штрихкод (если указан)
   - barcode, is_primary=true

---

## Ответ при успешном создании

```json
{
  "id": 123,
  "name": "Coca Cola 1.5л",
  "slug": "coca-cola-15l",
  "sku": "COCA-1.5L",
  "barcode": "4870123456789",
  "description": "Газированный напиток Кока-Кола 1.5 литра",
  "category": 1,
  "unit": 1,

  "pricing": {
    "cost_price": "8000.00",
    "sale_price": "12000.00",
    "wholesale_price": "10000.00",
    "tax_rate": "12.00",
    "margin": "50.00",
    "profit": "4000.00"
  },

  "inventory": {
    "quantity": "50.000",
    "min_quantity": "10.000",
    "max_quantity": "200.000",
    "track_inventory": true,
    "stock_status": "in_stock"
  },

  "batches": [
    {
      "id": 456,
      "batch_number": "BATCH-001-2024",
      "quantity": "50.000",
      "expiry_date": "2025-12-31",
      "supplier": 3
    }
  ],

  "is_active": true,
  "is_featured": false,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## UI Пример (React)

```jsx
import React, { useState, useEffect } from 'react';

function ProductCreateForm() {
  const [categories, setCategories] = useState([]);
  const [units, setUnits] = useState([]);
  const [suppliers, setSuppliers] = useState([]);

  const [formData, setFormData] = useState({
    // Основное
    name: '',
    category: '',
    unit: '',
    sku: '',
    barcode: '',
    description: '',

    // Цены
    cost_price: '',
    sale_price: '',
    wholesale_price: '',
    tax_rate: '0',

    // Количество
    initial_quantity: '',

    // Настройки
    min_quantity: '0',
    max_quantity: '',
    track_inventory: true,

    // Партия
    batch_number: '',
    expiry_date: '',
    supplier: '',

    // Дополнительно
    weight: '',
    volume: '',
    is_featured: false
  });

  // Загрузка справочников
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const tenantKey = localStorage.getItem('tenant_key');

    fetch('/api/products/categories/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-Key': tenantKey
      }
    }).then(r => r.json()).then(setCategories);

    fetch('/api/products/units/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-Key': tenantKey
      }
    }).then(r => r.json()).then(setUnits);

    fetch('/api/products/suppliers/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-Key': tenantKey
      }
    }).then(r => r.json()).then(setSuppliers);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const token = localStorage.getItem('access_token');
    const tenantKey = localStorage.getItem('tenant_key');

    try {
      const response = await fetch('/api/products/products/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'X-Tenant-Key': tenantKey
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const product = await response.json();
        alert(`Товар "${product.name}" создан! ID: ${product.id}`);
        window.location.href = '/products';
      } else {
        const errors = await response.json();
        console.error('Errors:', errors);
      }
    } catch (error) {
      alert('Ошибка создания товара');
    }
  };

  return (
    <form onSubmit={handleSubmit}>

      {/* СЕКЦИЯ 1: Основная информация */}
      <fieldset>
        <legend>📦 Основная информация</legend>

        <input
          placeholder="Название товара *"
          value={formData.name}
          onChange={(e) => setFormData({...formData, name: e.target.value})}
          required
        />

        <select
          value={formData.category}
          onChange={(e) => setFormData({...formData, category: e.target.value})}
          required
        >
          <option value="">Выберите категорию *</option>
          {categories.map(cat => (
            <option key={cat.id} value={cat.id}>{cat.name}</option>
          ))}
        </select>

        <select
          value={formData.unit}
          onChange={(e) => setFormData({...formData, unit: e.target.value})}
          required
        >
          <option value="">Единица измерения *</option>
          {units.map(unit => (
            <option key={unit.id} value={unit.id}>{unit.name}</option>
          ))}
        </select>

        <input
          placeholder="Артикул (если пусто - генерируется)"
          value={formData.sku}
          onChange={(e) => setFormData({...formData, sku: e.target.value})}
        />

        <input
          placeholder="Штрихкод"
          value={formData.barcode}
          onChange={(e) => setFormData({...formData, barcode: e.target.value})}
        />

        <textarea
          placeholder="Описание"
          value={formData.description}
          onChange={(e) => setFormData({...formData, description: e.target.value})}
        />
      </fieldset>

      {/* СЕКЦИЯ 2: Цены */}
      <fieldset>
        <legend>💰 Цены</legend>

        <input
          type="number"
          step="0.01"
          placeholder="Себестоимость *"
          value={formData.cost_price}
          onChange={(e) => setFormData({...formData, cost_price: e.target.value})}
          required
        />

        <input
          type="number"
          step="0.01"
          placeholder="Цена продажи *"
          value={formData.sale_price}
          onChange={(e) => setFormData({...formData, sale_price: e.target.value})}
          required
        />

        <input
          type="number"
          step="0.01"
          placeholder="Оптовая цена"
          value={formData.wholesale_price}
          onChange={(e) => setFormData({...formData, wholesale_price: e.target.value})}
        />

        <input
          type="number"
          step="0.01"
          placeholder="Налог (%)"
          value={formData.tax_rate}
          onChange={(e) => setFormData({...formData, tax_rate: e.target.value})}
        />
      </fieldset>

      {/* СЕКЦИЯ 3: Количество */}
      <fieldset>
        <legend>📊 Количество</legend>

        <input
          type="number"
          step="0.001"
          placeholder="Начальное количество *"
          value={formData.initial_quantity}
          onChange={(e) => setFormData({...formData, initial_quantity: e.target.value})}
          required
        />

        <input
          type="number"
          step="0.001"
          placeholder="Минимум для уведомлений"
          value={formData.min_quantity}
          onChange={(e) => setFormData({...formData, min_quantity: e.target.value})}
        />

        <input
          type="number"
          step="0.001"
          placeholder="Максимум"
          value={formData.max_quantity}
          onChange={(e) => setFormData({...formData, max_quantity: e.target.value})}
        />

        <label>
          <input
            type="checkbox"
            checked={formData.track_inventory}
            onChange={(e) => setFormData({...formData, track_inventory: e.target.checked})}
          />
          Вести учёт остатков
        </label>
      </fieldset>

      {/* СЕКЦИЯ 4: Партия (опционально) */}
      <details>
        <summary>📦 Информация о партии</summary>

        <input
          placeholder="Номер партии (генерируется автоматически)"
          value={formData.batch_number}
          onChange={(e) => setFormData({...formData, batch_number: e.target.value})}
        />

        <input
          type="date"
          placeholder="Срок годности"
          value={formData.expiry_date}
          onChange={(e) => setFormData({...formData, expiry_date: e.target.value})}
        />

        <select
          value={formData.supplier}
          onChange={(e) => setFormData({...formData, supplier: e.target.value})}
        >
          <option value="">Поставщик</option>
          {suppliers.map(sup => (
            <option key={sup.id} value={sup.id}>{sup.name}</option>
          ))}
        </select>
      </details>

      <button type="submit">Создать товар</button>
    </form>
  );
}

export default ProductCreateForm;
```

---

## Валидация

### ❌ Ошибки:

**1. Цена продажи меньше себестоимости:**
```json
{
  "sale_price": ["Цена продажи не может быть меньше себестоимости"]
}
```

**2. Дублирование артикула:**
```json
{
  "sku": ["Товар с таким артикулом уже существует"]
}
```

**3. Дублирование штрихкода:**
```json
{
  "barcode": ["Товар с таким штрихкодом уже существует"]
}
```

---

## Автоматическая генерация

### SKU (если не указан)
```
Название: "Coca Cola 1.5л"
→ SKU: "COCA-COLA-15L-A3F4B2C1"
```

### Номер партии (если не указан)
```
→ batch_number: "BATCH-D4E5F6G7"
```

### Slug (всегда генерируется)
```
Название: "Coca Cola 1.5л"
→ slug: "coca-cola-15l"
```

---

## Итого

✅ **Одна форма**
✅ **Один POST запрос**
✅ **Товар сразу готов к продаже!**

Никаких дополнительных шагов для создания партий или установки цен!
