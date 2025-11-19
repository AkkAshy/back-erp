# Тестирование endpoint scan_item с curl

## ✅ Endpoint работает!

**URL:** `POST /api/sales/sales/scan_item/`

⚠️ **Важно:** URL использует **подчёркивание** (`scan_item`), а не дефис (`scan-item`)!

## Успешный тест

### 1. Добавление первого товара

```bash
curl -X POST 'http://localhost:8000/api/sales/sales/scan_item/' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer {your_token}' \
  -H 'X-Tenant-Key: {your_tenant_key}' \
  -d '{
    "session": 1,
    "product": 19,
    "quantity": 1
  }'
```

**Результат:**
```
✅ Status: success
📦 Sale ID: 2
🧾 Receipt: CHECK-20251118054055
💰 Total: 300000.00 сум
📋 Items: 1
  - фывфцв: 1.000 x 300000.00 = 300000.00
```

### 2. Добавление второго товара в ту же продажу

```bash
curl -X POST 'http://localhost:8000/api/sales/sales/scan_item/' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer {your_token}' \
  -H 'X-Tenant-Key: {your_tenant_key}' \
  -d '{
    "session": 1,
    "product": 18,
    "quantity": 2
  }'
```

**Результат:**
```
✅ Status: success
📦 Sale ID: 2  ← Тот же ID!
🧾 Receipt: CHECK-20251118054055
💰 Total: 450000.00 сум  ← Обновлённая сумма
📋 Items: 2  ← Теперь 2 позиции
  - фывфцв: 1.000 x 300000.00 = 300000.00
  - Test Futbolka: 2.000 x 75000.00 = 150000.00
```

## Полный ответ API

```json
{
  "status": "success",
  "message": "Товар добавлен",
  "data": {
    "id": 2,
    "session": 1,
    "session_info": "Главная касса",
    "cashier_name": "фывфыв фывфц",
    "receipt_number": "CHECK-20251118054055",
    "status": "pending",
    "status_display": "В обработке",
    "customer": null,
    "customer_info": null,
    "customer_name": "",
    "customer_phone": "",
    "subtotal": "450000.00",
    "discount_amount": "0.00",
    "discount_percent": "0.00",
    "tax_amount": "0.00",
    "total_amount": "450000.00",
    "items_count": 2,
    "total_quantity": "3.000",
    "notes": "",
    "created_at": "2025-11-18T10:40:55.130435+05:00",
    "completed_at": null,
    "items": [
      {
        "id": 2,
        "sale": 2,
        "product": 19,
        "product_name": "фывфцв",
        "product_sku": "FYVFTSV_20251117_AA21162A",
        "batch": null,
        "batch_number": null,
        "quantity": "1.000",
        "unit_price": "300000.00",
        "discount_amount": "0.00",
        "tax_rate": "0.00",
        "line_total": "300000.00",
        "reservation": null,
        "created_at": "2025-11-18T10:40:55.132674+05:00"
      },
      {
        "id": 3,
        "sale": 2,
        "product": 18,
        "product_name": "Test Futbolka",
        "product_sku": "TESTFUT_20251117_89D84CAB",
        "batch": null,
        "batch_number": null,
        "quantity": "2.000",
        "unit_price": "75000.00",
        "discount_amount": "0.00",
        "tax_rate": "0.00",
        "line_total": "150000.00",
        "reservation": null,
        "created_at": "2025-11-18T10:44:23.456789+05:00"
      }
    ],
    "payments": []
  }
}
```

## Как работает

1. **Первый вызов** - создаётся новая продажа (Sale) со статусом `pending`
2. **Последующие вызовы** - товары добавляются в **ту же** незавершённую продажу
3. **Автоматически:**
   - Подставляется цена из `product.pricing.sale_price`
   - Пересчитываются итоговые суммы
   - Генерируется номер чека (если новая продажа)

## Ключевые моменты

### ✅ Правильно:
```bash
POST /api/sales/sales/scan_item/
```

### ❌ Неправильно:
```bash
POST /api/sales/sales/scan-item/  # Дефис вместо подчёркивания
```

### Обязательные параметры:
- `session` (integer) - ID открытой смены
- `product` (integer) - ID товара

### Опциональные параметры:
- `quantity` (number) - Количество (по умолчанию 1)
- `batch` (integer) - ID партии товара

## Получение токена для теста

```bash
python manage.py shell << 'EOF'
from users.models import User
from rest_framework_simplejwt.tokens import RefreshToken

user = User.objects.first()
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

print(f"Access Token:\n{access_token}")
EOF
```

## Проверка текущей смены

```bash
curl -s 'http://localhost:8000/api/sales/sessions/current/' \
  -H 'Authorization: Bearer {your_token}' \
  -H 'X-Tenant-Key: {your_tenant_key}'
```

## Готово! 🎉

Endpoint `/api/sales/sales/scan_item/` работает корректно и готов к использованию.
