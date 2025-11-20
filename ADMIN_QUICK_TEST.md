# 🚀 Quick Test - Получение всех магазинов с credentials

## Тестовые данные

### Пользователь: admin_testshop
```
Username: admin_testshop
Password: admin123
Владелец магазина: "Тестовый Магазин"
```

## 1. Получить токен

```bash
curl -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin_testshop", "password": "admin123"}' | jq -r '.access'
```

## 2. Получить все магазины с credentials

```bash
TOKEN="<ваш_токен_из_шага_1>"

curl -X GET http://localhost:8000/api/users/stores/my-stores-with-credentials/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq
```

## Ожидаемый результат

```json
{
  "status": "success",
  "data": {
    "count": 1,
    "stores": [
      {
        "id": 2,
        "name": "Тестовый Магазин",
        "slug": "test_shop",
        "tenant_key": "test_shop_4dfa7a5a",
        "schema_name": "tenant_test_shop",
        "address": "ул. Тестовая, 1",
        "phone": "+998901111111",
        "is_active": true,
        "staff_credentials": {
          "username": "test_shop_staff",
          "password": "12345678",
          "full_name": "Сотрудники Тестовый Магазин",
          "is_active": true,
          "note": "Общий аккаунт для всех сотрудников магазина"
        }
      }
    ]
  }
}
```

## Полная команда (одной строкой)

```bash
# Получить токен и сразу использовать его
TOKEN=$(curl -s -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin_testshop", "password": "admin123"}' | jq -r '.access')

# Получить магазины
curl -X GET http://localhost:8000/api/users/stores/my-stores-with-credentials/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq
```

## Проверка

✅ Endpoint: `/api/users/stores/my-stores-with-credentials/`
✅ Метод: GET
✅ X-Tenant-Key: НЕ требуется
✅ Authorization: Требуется Bearer token
✅ Возвращает: Все магазины владельца + staff credentials для каждого
