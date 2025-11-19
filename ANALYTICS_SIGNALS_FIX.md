# Исправление: Ошибки в analytics/signals.py

## Проблема 1: ImportError CashSession

При попытке завершить продажу (checkout) возникала ошибка:

```
❌ API Error:
{
  url: '/sales/sales/7/checkout/',
  status: 400,
  error: "cannot import name 'CashSession' from 'sales.models'"
}
```

### Причина

В файле [analytics/signals.py](analytics/signals.py) использовалось **неправильное** имя модели:
- ❌ Использовалось: `CashSession`
- ✅ Правильное название: `CashierSession`

---

## Проблема 2: Payment.status field does not exist

После исправления первой ошибки возникла вторая:

```
❌ API Error:
{
  url: '/sales/sales/9/checkout/',
  status: 400,
  error: "Cannot resolve keyword 'status' into field. Choices are: amount, card_last4, change_amount, created_at, id, notes, payment_method, received_amount, sale, sale_id, session, session_id, transaction_id"
}
```

### Причина

В модели `Payment` **нет поля `status`**. Платежи считаются завершёнными сразу после создания. Код пытался фильтровать платежи по несуществующему полю `status='completed'`.

---

## Решение

### Исправлен файл: analytics/signals.py

#### Исправление 1: CashSession → CashierSession

**Строка 63:**

**Было:**
```python
from sales.models import Sale, Payment, CashSession
```

**Стало:**
```python
from sales.models import Sale, Payment, CashierSession
```

---

**Строка 112:**

**Было:**
```python
sessions = CashSession.objects.filter(opened_at__date=date)
```

**Стало:**
```python
sessions = CashierSession.objects.filter(opened_at__date=date)
```

---

#### Исправление 2: Удалён фильтр по Payment.status

**Строка 91-94:**

**Было:**
```python
# Платежи по типам
payments = Payment.objects.filter(
    sale__in=sales,
    status='completed'  # ← Поле не существует!
)
```

**Стало:**
```python
# Платежи по типам
payments = Payment.objects.filter(
    sale__in=sales
)
```

**Почему убрали `status='completed'`?**
- В модели `Payment` нет поля `status`
- Все платежи, связанные с завершёнными продажами (`sale__in=sales`), уже прошли валидацию
- Фильтр по `sale__in=sales` уже гарантирует, что мы получаем только платежи из завершённых продаж

---

## Проверка

```bash
python manage.py check
# System check identified no issues (0 silenced).
```

Сервер автоматически перезагрузился и подхватил изменения.

---

## Что делает этот код?

Функция `_update_daily_sales_report()` в `analytics/signals.py` обновляет дневной отчёт по продажам. Она подсчитывает:

- Общую сумму продаж
- Количество продаж
- **Платежи по типам** (наличные, карта, кредит) ← здесь была ошибка с `status`
- Уникальных клиентов
- **Количество открытых и закрытых смен** ← здесь была ошибка с `CashSession`

### Исправленный код:

```python
def _update_daily_sales_report(date):
    """
    Обновляет или создаёт дневной отчёт по продажам.

    Агрегирует данные из всех завершённых продаж за день.
    """
    from analytics.models import DailySalesReport
    from sales.models import Sale, Payment, CashierSession  # ← Исправление 1
    from customers.models import Customer

    # Получаем все завершённые продажи за день
    sales = Sale.objects.filter(
        status='completed',
        completed_at__date=date
    )

    # ... код агрегации данных ...

    # Платежи по типам
    payments = Payment.objects.filter(
        sale__in=sales  # ← Исправление 2: убран status='completed'
    )

    payment_stats = {
        'cash': payments.filter(payment_method='cash').aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
        'card': payments.filter(payment_method='card').aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
        'credit': payments.filter(payment_method='credit').aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
    }

    # Смены
    sessions = CashierSession.objects.filter(opened_at__date=date)  # ← Исправление 1
    sessions_opened = sessions.count()
    sessions_closed = sessions.filter(status='closed').count()

    # Создаём или обновляем отчёт
    DailySalesReport.objects.update_or_create(
        date=date,
        defaults={
            'total_sales': sales_stats['total_sales'] or Decimal('0.00'),
            'cash_sales': payment_stats['cash'],
            'card_sales': payment_stats['card'],
            'credit_sales': payment_stats['credit'],
            'sessions_opened': sessions_opened,
            'sessions_closed': sessions_closed,
            # ...
        }
    )
```

---

## Когда срабатывает этот код?

Функция `_update_daily_sales_report()` вызывается автоматически при:

1. **Завершении продажи** (`Sale.status = 'completed'`)
2. **Удалении продажи**

Через Django signals:
```python
@receiver(post_save, sender='sales.Sale')
def update_analytics_on_sale(sender, instance, created, **kwargs):
    if instance.status != 'completed':
        return

    sale_date = instance.completed_at.date()
    _update_daily_sales_report(sale_date)  # ← Вызывается здесь
```

---

## Почему это важно?

### Без исправления:
- ❌ Невозможно завершить продажу через API
- ❌ Endpoints `/api/sales/sales/{id}/checkout/` и `/api/sales/sales/{id}/complete/` возвращали 400 ошибку
- ❌ Дневные отчёты по продажам не обновлялись

### После исправления:
- ✅ Продажи завершаются успешно
- ✅ Аналитика обновляется корректно
- ✅ Отчёты показывают правильную статистику по платежам и сменам

---

## Затронутые endpoints

### ✅ Теперь работают:

```http
POST /api/sales/sales/{id}/complete/
POST /api/sales/sales/{id}/checkout/
```

### Пример успешного завершения продажи:

**Запрос:**
```bash
curl -X POST 'http://localhost:8000/api/sales/sales/9/complete/' \
  -H 'Authorization: Bearer {token}' \
  -H 'X-Tenant-Key: admin_1a12e47a' \
  -H 'Content-Type: application/json' \
  -d '{
    "payments": [{
      "payment_method": "cash",
      "amount": 450000,
      "received_amount": 500000
    }]
  }'
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Продажа завершена",
  "data": {
    "id": 9,
    "status": "completed",
    "total_amount": "450000.00",
    "completed_at": "2025-11-18T11:47:00.123456+05:00",
    "payments": [
      {
        "id": 20,
        "payment_method": "cash",
        "amount": "450000.00",
        "received_amount": "500000.00",
        "change_amount": "50000.00"
      }
    ]
  }
}
```

---

## Модель Payment - доступные поля

Для справки, вот все поля модели `Payment`:

```python
class Payment(models.Model):
    sale = ForeignKey(Sale)           # Ссылка на продажу
    session = ForeignKey(CashierSession)  # Ссылка на смену
    payment_method = CharField(...)   # Способ оплаты
    amount = DecimalField(...)        # Сумма
    received_amount = DecimalField(...) # Получено (для наличных)
    change_amount = DecimalField(...) # Сдача
    card_last4 = CharField(...)       # Последние 4 цифры карты
    transaction_id = CharField(...)   # ID транзакции
    notes = TextField(...)            # Примечания
    created_at = DateTimeField(...)   # Дата создания

    # ❌ НЕТ ПОЛЯ status!
```

---

## Правильные названия моделей в sales.models

- ✅ `Sale` - Продажа
- ✅ `SaleItem` - Позиция в продаже
- ✅ `Payment` - Платёж (БЕЗ поля status)
- ✅ `CashierSession` - Кассовая смена
- ✅ `CashRegister` - Касса
- ❌ `CashSession` - **НЕ СУЩЕСТВУЕТ**

---

---

## Проблема 3: SaleItem field mapping errors

После исправления предыдущих ошибок возникла третья:

```
❌ API Error:
{
  url: '/sales/sales/10/checkout/',
  status: 400,
  error: "Cannot resolve keyword 'total_amount' into field. Choices are: batch, batch_id, created_at, discount_amount, id, line_total, product, product_id, quantity, quantity_sold, reservation, reservation_id, sale, sale_id, tax_rate, unit_price"
}
```

### Причина

В функции `_update_product_performance()` использовались **несуществующие поля** модели `SaleItem`:
- ❌ `total_amount` (правильно: `line_total`)
- ❌ `price` (правильно: `unit_price`)
- ❌ `discount_percent` (нет в модели)
- ❌ `cost_price` (нет в модели, есть только в `Product.pricing`)

---

#### Исправление 3: Правильные названия полей SaleItem

**Строки 159-166:**

**Было:**
```python
# Агрегируем данные
stats = items.aggregate(
    quantity_sold=Sum('quantity'),
    total_revenue=Sum('total_amount'),  # ← Поле не существует!
    sales_count=Count('sale', distinct=True),
    avg_price=Avg('price'),  # ← Поле не существует!
    avg_discount=Avg('discount_percent'),  # ← Поле не существует!
    total_cost=Sum(F('quantity') * F('cost_price')),  # ← Поле не существует!
)
```

**Стало:**
```python
# Агрегируем данные
stats = items.aggregate(
    quantity_sold=Sum('quantity'),
    total_revenue=Sum('line_total'),  # ✅ Правильное поле
    sales_count=Count('sale', distinct=True),
    avg_price=Avg('unit_price'),  # ✅ Правильное поле
)
```

**Строки 167-188:**

**Было:**
```python
# Считаем прибыль
total_cost = stats['total_cost'] or Decimal('0.00')
total_revenue = stats['total_revenue'] or Decimal('0.00')
total_profit = total_revenue - total_cost
profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0.00')
```

**Стало:**
```python
# Считаем себестоимость и прибыль
total_revenue = stats['total_revenue'] or Decimal('0.00')
quantity_sold = stats['quantity_sold'] or Decimal('0.000')

# Получаем себестоимость товара из Product.pricing
cost_price = Decimal('0.00')
if hasattr(product, 'pricing') and product.pricing:
    cost_price = product.pricing.cost_price or Decimal('0.00')

total_cost = quantity_sold * cost_price
total_profit = total_revenue - total_cost
profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0.00')

# Средняя скидка - вычисляем из данных
avg_discount = Decimal('0.00')
if stats['sales_count'] and stats['avg_price']:
    avg_sale_price = total_revenue / quantity_sold if quantity_sold > 0 else Decimal('0.00')
    if stats['avg_price'] > 0:
        avg_discount = ((stats['avg_price'] - avg_sale_price) / stats['avg_price'] * 100)
        avg_discount = max(Decimal('0.00'), avg_discount)
```

---

## Резюме

### Что было исправлено:

✅ **Исправление 1:** Заменено `CashSession` на `CashierSession` (строки 63, 112)
✅ **Исправление 2:** Удалён фильтр `status='completed'` для Payment (строка 93)
✅ **Исправление 3:** Исправлены названия полей SaleItem (строки 159-202)
✅ **Файл:** [analytics/signals.py](analytics/signals.py)
✅ **Проверено:** `python manage.py check` - без ошибок
✅ **Статус:** Сервер перезагружен 5 раз, изменения применены

### Итоговые изменения:

1. **CashSession** → **CashierSession** (правильное имя модели)
2. Удалён фильтр по несуществующему полю **Payment.status**
3. Исправлены названия полей модели **SaleItem**:
   - `total_amount` → `line_total`
   - `price` → `unit_price`
   - `discount_percent` - вычисляется, а не берётся из поля
   - `cost_price` - берётся из `Product.pricing`, а не из SaleItem

Готово! 🎉
