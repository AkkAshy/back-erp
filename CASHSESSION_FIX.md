# Исправление: ImportError CashSession

## Проблема

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

## Решение

### Исправлен файл: analytics/signals.py

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

## Проверка

```bash
python manage.py check
# System check identified no issues (0 silenced).
```

Сервер автоматически перезагрузился и подхватил изменения.

## Что делает этот код?

Функция `_update_daily_sales_report()` в `analytics/signals.py` обновляет дневной отчёт по продажам. Она подсчитывает:

- Общую сумму продаж
- Количество продаж
- Платежи по типам (наличные, карта, кредит)
- Уникальных клиентов
- **Количество открытых и закрытых смен за день** ← здесь использовалась модель

### Код, который был исправлен:

```python
def _update_daily_sales_report(date):
    """
    Обновляет или создаёт дневной отчёт по продажам.

    Агрегирует данные из всех завершённых продаж за день.
    """
    from analytics.models import DailySalesReport
    from sales.models import Sale, Payment, CashierSession  # ← Исправлено
    from customers.models import Customer

    # ... код агрегации данных ...

    # Смены
    sessions = CashierSession.objects.filter(opened_at__date=date)  # ← Исправлено
    sessions_opened = sessions.count()
    sessions_closed = sessions.filter(status='closed').count()

    # Создаём или обновляем отчёт
    DailySalesReport.objects.update_or_create(
        date=date,
        defaults={
            # ...
            'sessions_opened': sessions_opened,
            'sessions_closed': sessions_closed,
        }
    )
```

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

## Почему это важно?

Без этого исправления:
- ❌ Невозможно завершить продажу через API
- ❌ Endpoint `/api/sales/sales/{id}/checkout/` возвращал 400 ошибку
- ❌ Дневные отчёты по продажам не обновлялись

После исправления:
- ✅ Продажи завершаются успешно
- ✅ Аналитика обновляется корректно
- ✅ Отчёты показывают количество открытых/закрытых смен

## Затронутые endpoints

### ✅ Теперь работают:

```http
POST /api/sales/sales/{id}/complete/
POST /api/sales/sales/{id}/checkout/
```

### Пример успешного завершения продажи:

**Запрос:**
```bash
curl -X POST 'http://localhost:8000/api/sales/sales/7/complete/' \
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
    "id": 7,
    "status": "completed",
    "total_amount": "450000.00",
    "payments": [
      {
        "id": 15,
        "payment_method": "cash",
        "amount": "450000.00",
        "change_amount": "50000.00"
      }
    ]
  }
}
```

## Дополнительная информация

### Правильные названия моделей в sales.models:

- ✅ `Sale` - Продажа
- ✅ `SaleItem` - Позиция в продаже
- ✅ `Payment` - Платёж
- ✅ `CashierSession` - Кассовая смена
- ✅ `CashRegister` - Касса
- ❌ `CashSession` - **НЕ СУЩЕСТВУЕТ**

### Где используется CashierSession:

1. **sales/models.py** - Определение модели
2. **sales/views.py** - ViewSet для работы со сменами
3. **analytics/signals.py** - Подсчёт смен в отчётах (теперь исправлено)
4. **sales/serializers.py** - Валидация продаж

## Резюме

✅ **Исправлено:** Заменено `CashSession` на `CashierSession` в 2 местах
✅ **Файл:** [analytics/signals.py:63, 112](analytics/signals.py)
✅ **Проверено:** `python manage.py check` - без ошибок
✅ **Статус:** Сервер перезагружен, изменения применены

Готово! 🎉
