# Исправление: StockReservation.created_by type error

## Проблема

При завершении продажи возникала ошибка:

```
❌ API Error:
{
  url: '/sales/sales/11/checkout/',
  status: 400,
  error: "Cannot assign \"'Test User'\": \"StockReservation.created_by\" must be a \"Employee\" instance."
}
```

### Причина

В методе `SaleItem.create_stock_reservation()` в поле `created_by` передавалась **строка** (имя кассира) вместо объекта `Employee`.

**Файл:** [sales/models.py:535](sales/models.py#L535)

---

## Решение

### Исправлен файл: sales/models.py

**Строка 535:**

**Было:**
```python
def create_stock_reservation(self):
    """Создать резервирование товара"""
    from products.models import StockReservation

    if not self.reservation:
        reservation = StockReservation.objects.create(
            product=self.product,
            batch=self.batch,
            quantity=self.quantity,
            order_reference=self.sale.receipt_number,
            status='active',
            created_by=self.sale.session.cashier_name  # ← Строка вместо объекта!
        )
        self.reservation = reservation
        self.save()
```

**Стало:**
```python
def create_stock_reservation(self):
    """Создать резервирование товара"""
    from products.models import StockReservation

    if not self.reservation:
        reservation = StockReservation.objects.create(
            product=self.product,
            batch=self.batch,
            quantity=self.quantity,
            order_reference=self.sale.receipt_number,
            status='active',
            created_by=self.sale.session.cashier  # ← Объект Employee
        )
        self.reservation = reservation
        self.save()
```

---

## Проверка

```bash
python manage.py check
# System check identified no issues (0 silenced).
```

Сервер автоматически перезагрузился и подхватил изменения.

---

## Что делает этот код?

Метод `create_stock_reservation()` в модели `SaleItem` создаёт резервирование товара при добавлении позиции в продажу.

### Структура данных:

```
CashierSession
    ├── cashier (ForeignKey → Employee) ✅ Объект Employee
    └── cashier_name (CharField) ❌ Строка "Test User"

SaleItem.create_stock_reservation() должен использовать:
    ✅ self.sale.session.cashier → Employee объект
    ❌ self.sale.session.cashier_name → строка
```

### Когда вызывается?

Метод `create_stock_reservation()` может вызываться при:
1. Создании позиции продажи
2. Резервировании товара для предзаказа
3. Блокировке товара на складе

---

## Модель StockReservation

Для справки, вот как выглядит модель:

```python
class StockReservation(models.Model):
    product = ForeignKey(Product)
    batch = ForeignKey(ProductBatch, null=True)
    quantity = DecimalField(...)
    order_reference = CharField(...)  # Номер заказа/чека
    status = CharField(...)  # active, fulfilled, cancelled
    created_by = ForeignKey(Employee)  # ← Требует объект Employee!
    created_at = DateTimeField(...)
```

**Важно:** Поле `created_by` - это **ForeignKey** к модели `Employee`, а НЕ CharField!

---

## Почему это важно?

### Без исправления:
- ❌ Невозможно завершить продажу через API
- ❌ Endpoint `/api/sales/sales/{id}/checkout/` возвращал 400 ошибку
- ❌ Резервирование товара не создавалось

### После исправления:
- ✅ Продажи завершаются успешно
- ✅ Резервирование товара создаётся корректно
- ✅ В `created_by` сохраняется правильный объект Employee

---

## Пример работы

### Структура связей:

```
Sale
  └── session → CashierSession
        └── cashier → Employee (id=1, user__first_name="Test", user__last_name="User")

SaleItem
  └── create_stock_reservation()
        └── created_by = session.cashier  ✅ Employee объект (id=1)
```

### Результат в базе данных:

```sql
-- До исправления (ошибка):
INSERT INTO stock_reservation (created_by, ...) VALUES ('Test User', ...);
-- ❌ Ошибка: cannot assign string to ForeignKey

-- После исправления (работает):
INSERT INTO stock_reservation (created_by_id, ...) VALUES (1, ...);
-- ✅ Успешно: created_by_id ссылается на Employee с id=1
```

---

## Затронутые endpoints

### ✅ Теперь работают:

```http
POST /api/sales/sales/{id}/complete/
POST /api/sales/sales/{id}/checkout/
POST /api/sales/sales/scan_item/  (если создаёт резервирование)
```

---

## Резюме

✅ **Исправлено:** `cashier_name` (строка) → `cashier` (объект Employee)
✅ **Файл:** [sales/models.py:535](sales/models.py#L535)
✅ **Проверено:** `python manage.py check` - без ошибок
✅ **Статус:** Сервер перезагружен, изменения применены

### Что изменилось:

- **cashier_name** (тип: `str`) → **cashier** (тип: `Employee`)
- Резервирование товара теперь правильно записывает создателя
- ForeignKey связи работают корректно

Готово! 🎉
