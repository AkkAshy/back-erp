# Изменения: Создание товара в одном окне

## Что сделано

Реализовано **полное создание товара в одном запросе**.

Теперь владелец заполняет одну форму и получает:
- ✅ Товар с полными данными
- ✅ Цены (себестоимость, продажная, оптовая, налог)
- ✅ Первая партия с количеством
- ✅ Настройки учёта остатков
- ✅ Штрихкод (если указан)

**Товар сразу готов к продаже!**

---

## Изменённые файлы

### 1. `products/serializers.py`

**Создан новый ProductCreateSerializer:**

Заменяет старый `ProductCreateUpdateSerializer` для создания.

```python
class ProductCreateSerializer(serializers.ModelSerializer):
    """
    Полное создание товара в одном запросе!

    Создаёт сразу:
    - Product
    - ProductPricing
    - ProductInventory
    - ProductBatch (первая партия)
    - ProductBarcode (если указан)
    """
```

**Добавлены поля:**
```python
# Основная информация
name, sku, barcode, description, category, unit

# Цены
cost_price, sale_price, wholesale_price, tax_rate

# Количество (первая партия)
initial_quantity  # Новое! Начальное количество

# Настройки учёта
min_quantity, max_quantity, track_inventory

# Партия
batch_number, expiry_date, supplier

# Дополнительно
weight, volume, is_featured
```

**Метод create():**
- Создаёт все связанные объекты в одной транзакции
- Автоматически генерирует SKU если не указан
- Автоматически генерирует номер партии
- Автоматически создаёт ProductBarcode если указан barcode

**Создан ProductUpdateSerializer:**

Отдельный сериализатор для обновления (без изменения количества).

---

### 2. `products/views.py`

**Обновлён ProductViewSet:**

```python
def get_serializer_class(self):
    if self.action == 'create':
        return ProductCreateSerializer  # Полное создание
    elif self.action in ['update', 'partial_update']:
        return ProductUpdateSerializer  # Обновление
    # ...
```

**Обновлён import:**
```python
from products.serializers import (
    # ...
    ProductCreateSerializer,  # Новый
    ProductUpdateSerializer,  # Новый
    # ...
)
```

---

## Созданные документы

### 1. `PRODUCT_CREATION_GUIDE.md`
- Полное описание API создания товара
- Минимальный и полный примеры запросов
- Описание всех полей с типами
- **Готовый React компонент!**
- Примеры ошибок валидации
- Что происходит при создании

### 2. `CHANGELOG_PRODUCT_CREATION.md`
- Этот файл - сводка изменений

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

## Минимальный пример запроса

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

**Результат:**
- Product создан
- ProductPricing создан
- ProductInventory создан с quantity=0
- ProductBatch создан с quantity=50 (автоматически обновляет ProductInventory.quantity=50)
- SKU и batch_number сгенерированы автоматически

---

## Полный пример запроса

```json
{
  "name": "Coca Cola 1.5л",
  "sku": "COCA-1.5L",
  "barcode": "4870123456789",
  "description": "Газированный напиток",
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

**Результат:**
- Всё то же самое
- Плюс ProductBarcode создан с barcode="4870123456789"
- Используются указанные SKU и batch_number

---

## Что происходит при создании

### В одной транзакции создаются:

1. **Product**
   - name, sku (авто), slug (авто), barcode, description
   - category, unit, weight, volume, is_featured

2. **ProductPricing**
   - cost_price, sale_price, wholesale_price, tax_rate
   - Автоматически вычисляет margin и profit

3. **ProductInventory**
   - min_quantity, max_quantity, track_inventory
   - quantity = 0 (изначально)

4. **ProductBatch**
   - batch_number (авто), initial_quantity
   - expiry_date, supplier
   - purchase_price = cost_price
   - **Обновляет ProductInventory.quantity через сигнал!**

5. **ProductBarcode** (опционально)
   - barcode, is_primary=true

---

## Автоматическая генерация

### SKU
```python
if not data.get('sku'):
    base_sku = slugify(data['name'])[:20]
    sku = f"{base_sku}-{uuid.uuid4().hex[:8]}"
    data['sku'] = sku.upper()
```

Пример: `"Coca Cola"` → `"COCA-COLA-A3F4B2C1"`

### Slug
```python
if not data.get('slug'):
    data['slug'] = slugify(data['name'])
```

Пример: `"Coca Cola 1.5л"` → `"coca-cola-15l"`

### Номер партии
```python
if not batch_data['batch_number']:
    batch_data['batch_number'] = f"BATCH-{uuid.uuid4().hex[:8].upper()}"
```

Пример: `"BATCH-D4E5F6G7"`

---

## Тестирование

### Через Swagger UI

1. Открыть `http://localhost:8000/swagger/`
2. Авторизоваться (Authorize → Bearer token)
3. Найти `POST /api/products/products/`
4. Нажать "Try it out"
5. Вставить JSON пример
6. Execute

### Через cURL

```bash
curl -X POST http://localhost:8000/api/products/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -H "X-Tenant-Key: <tenant_key>" \
  -d '{
    "name": "Coca Cola 1.5л",
    "category": 1,
    "unit": 1,
    "cost_price": "8000.00",
    "sale_price": "12000.00",
    "initial_quantity": "50.000"
  }'
```

---

## Для фронтенда

Готовый React компонент находится в: **`PRODUCT_CREATION_GUIDE.md`**

**Что нужно:**
1. Скопировать компонент
2. Добавить стили
3. Настроить URL на свой API
4. Готово!

**Перед созданием товара нужно загрузить:**
- Категории: `GET /api/products/categories/`
- Единицы: `GET /api/products/units/`
- Поставщики: `GET /api/products/suppliers/` (опционально)

---

## Валидация

### На уровне сериализатора:

1. **Проверка уникальности SKU**
2. **Проверка уникальности штрихкода**
3. **Проверка: sale_price >= cost_price**
4. **Автоматическая генерация SKU и batch_number**

### Примеры ошибок:

```json
{
  "sku": ["Товар с таким артикулом уже существует"]
}
```

```json
{
  "barcode": ["Товар с таким штрихкодом уже существует"]
}
```

```json
{
  "sale_price": ["Цена продажи не может быть меньше себестоимости"]
}
```

---

## Обновление товара

Для обновления используется **отдельный сериализатор** `ProductUpdateSerializer`.

```
PATCH /api/products/products/{id}/
```

**Нельзя изменить:**
- initial_quantity (количество изменяется только через партии)

**Можно изменить:**
- Основные данные (name, description и т.д.)
- Цены
- Настройки учёта (min_quantity, max_quantity)

---

## Автоматическая генерация штрихкодов партий

**Новая функция!**

Каждая партия товара **автоматически получает уникальный штрихкод** при создании.

### Формат:
```
BATCH-{timestamp}-{random}
```

### Пример:
```
BATCH-20241215103045-A3F4B2C1
```

### Где используется:
- При приёмке товара (сканируем штрихкод партии)
- При продаже (FIFO/FEFO учёт)
- При инвентаризации (сканирование по партиям)
- При списании по сроку годности

### Изменения в модели ProductBatch:

**Добавлено поле:**
```python
barcode = models.CharField(
    max_length=100,
    blank=True,
    verbose_name='Штрихкод партии',
    help_text='Автоматически генерируется для каждой партии'
)
```

**Добавлен метод save():**
```python
def save(self, *args, **kwargs):
    if not self.barcode:
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        unique_part = uuid.uuid4().hex[:8].upper()
        self.barcode = f"BATCH-{timestamp}-{unique_part}"
    super().save(*args, **kwargs)
```

### Обновлён ProductBatchSerializer:

```python
fields = [
    'id', 'product', 'product_name', 'batch_number', 'barcode',  # barcode добавлен
    # ...
]
read_only_fields = ['id', 'barcode', 'received_at', 'updated_at']
```

Подробнее: **`BATCH_BARCODE_AUTO_GENERATION.md`**

---

## Миграции

**Требуется миграция!**

Добавлено новое поле `barcode` в модель `ProductBatch`:

```bash
python manage.py makemigrations products
python manage.py migrate
```

---

## Итого

✅ Полное создание товара в одном запросе
✅ Автоматическая генерация SKU и batch_number
✅ **Автоматическая генерация штрихкода для каждой партии**
✅ Товар сразу готов к продаже
✅ Готовый React компонент для фронтенда

**Владелец не лазит по интерфейсу - заполнил одну форму и работает!**
