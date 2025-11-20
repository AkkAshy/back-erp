# 🚀 Quick Test - Мульти-магазинная аналитика

## Тестовый пользователь

```
Username: admin_testshop
Password: admin123
Владелец магазинов: 3 магазина
```

## 1. Получить токен

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin_testshop", "password": "admin123"}' | jq -r '.access')

echo "Token: $TOKEN"
```

## 2. Получить аналитику за месяц

```bash
curl "http://localhost:8000/api/users/stores/multi-store-analytics/?period=month" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 3. Получить аналитику за неделю

```bash
curl "http://localhost:8000/api/users/stores/multi-store-analytics/?period=week" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 4. Получить только общие итоги

```bash
curl "http://localhost:8000/api/users/stores/multi-store-analytics/?period=month" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.aggregated'
```

Ожидаемый результат:
```json
{
  "total_sales": 1227600000.0,
  "total_sales_count": 57,
  "total_discount": 0.0,
  "total_items_sold": 2088,
  "avg_sale_amount": 21536842.10
}
```

## 5. Получить список магазинов с продажами

```bash
curl "http://localhost:8000/api/users/stores/multi-store-analytics/?period=month" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.by_store[] | {name, total_sales, sales_count}'
```

Ожидаемый результат:
```json
{
  "name": "asdawd",
  "total_sales": 409200000,
  "sales_count": 19
}
{
  "name": "Новый Тестовый Магазин 2",
  "total_sales": 409200000,
  "sales_count": 19
}
{
  "name": "Тестовый Магазин",
  "total_sales": 409200000,
  "sales_count": 19
}
```

## 6. Кастомный период

```bash
curl "http://localhost:8000/api/users/stores/multi-store-analytics/?start_date=2025-11-01&end_date=2025-11-20" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.period'
```

## Полная команда (одной строкой)

```bash
# Получить токен и сразу запросить аналитику
TOKEN=$(curl -s -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin_testshop", "password": "admin123"}' | jq -r '.access') && \
curl "http://localhost:8000/api/users/stores/multi-store-analytics/?period=month" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Проверка

✅ Endpoint: `/api/users/stores/multi-store-analytics/`
✅ Метод: GET
✅ X-Tenant-Key: НЕ требуется
✅ Authorization: Требуется Bearer token
✅ Возвращает: Агрегированную аналитику по всем магазинам владельца

## Поддерживаемые периоды

- `period=today` - Сегодня
- `period=yesterday` - Вчера
- `period=week` - Последние 7 дней
- `period=month` - Последние 30 дней
- `start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Кастомный период

## Структура ответа

```json
{
  "status": "success",
  "data": {
    "total_stores": 3,           // Количество магазинов
    "period": {                  // Период аналитики
      "start_date": "2025-10-21",
      "end_date": "2025-11-20"
    },
    "aggregated": {              // ОБЩИЕ итоги
      "total_sales": 1227600000.0,
      "total_sales_count": 57,
      "total_discount": 0.0,
      "total_items_sold": 2088,
      "avg_sale_amount": 21536842.10
    },
    "by_store": [                // РАЗБИВКА по магазинам
      {
        "store_id": 9,
        "store_name": "asdawd",
        "store_slug": "asdawd",
        "tenant_key": "asdawd_8b43a536",
        "total_sales": 409200000.0,
        "sales_count": 19,
        "avg_sale": 21536842.10
      }
    ]
  }
}
```
