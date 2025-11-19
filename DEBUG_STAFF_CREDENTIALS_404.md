# Отладка ошибки 404 для /api/users/stores/staff-credentials/

## Возможные причины 404

### 1. Staff user не существует для магазина

Endpoint возвращает 404 если staff user не найден в базе данных.

**Проверка:**
```bash
# Замените на ваш admin token
ADMIN_TOKEN="ваш_токен"

curl -X GET "https://back-erp-gules.vercel.app/api/users/stores/staff-credentials/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a" \
  -v
```

**Если ответ:**
```json
{
  "status": "error",
  "code": "not_found",
  "message": "Общий аккаунт для магазина \"Тестовый Магазин\" не найден"
}
```

**Решение:** Staff user должен быть создан автоматически при создании магазина через signal. Проверьте:

1. Существует ли user с username `test_shop_staff`:
   ```bash
   # Через Django shell
   python manage.py shell
   >>> from django.contrib.auth.models import User
   >>> User.objects.filter(username__endswith='_staff')
   ```

2. Если не существует - создайте вручную:
   ```python
   from django.contrib.auth.models import User
   from users.models import Store, Employee

   # Получите ваш магазин
   store = Store.objects.get(slug='test_shop')

   # Создайте staff user
   staff_user = User.objects.create_user(
       username=f"{store.slug}_staff",
       password="12345678",
       first_name="Сотрудники",
       last_name=store.name,
       is_active=True
   )

   # Создайте Employee запись для staff
   Employee.objects.create(
       user=staff_user,
       store=store,
       role=Employee.Role.STAFF,
       is_active=True
   )

   print(f"✅ Создан staff user: {staff_user.username}")
   ```

### 2. URL неправильный

**Проверьте:**
- Обязателен trailing slash в конце: `/staff-credentials/`
- Полный URL: `https://back-erp-gules.vercel.app/api/users/stores/staff-credentials/`

### 3. Приложение не перезагружено после деплоя

Если вы обновили код, но приложение не перезапущено - изменения не применены.

**Для Vercel:**
- Сделайте новый push в git
- Vercel автоматически пересоздаст deployment

### 4. Права доступа

Endpoint доступен только владельцу магазина.

**Проверка:**
```bash
# Убедитесь что токен принадлежит владельцу магазина
# Логин как admin_testshop, НЕ как test_shop_staff

curl -X POST "https://back-erp-gules.vercel.app/api/users/auth/login/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a" \
  -d '{
    "username": "admin_testshop",
    "password": "admin12345"
  }'
```

Используйте полученный `access` токен для запроса staff-credentials.

### 5. Проверка существующих URL

Список всех доступных URL для stores:
```bash
# Должны быть:
GET    /api/users/stores/
POST   /api/users/stores/
GET    /api/users/stores/{id}/
PUT    /api/users/stores/{id}/
PATCH  /api/users/stores/{id}/
DELETE /api/users/stores/{id}/
GET    /api/users/stores/staff-credentials/  # ← Этот должен существовать!
```

## Полный тест

```bash
# 1. Логин как владелец
RESPONSE=$(curl -s -X POST "https://back-erp-gules.vercel.app/api/users/auth/login/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a" \
  -d '{"username": "admin_testshop", "password": "admin12345"}')

echo "Login response:"
echo $RESPONSE | python3 -m json.tool

# Извлекаем токен
TOKEN=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")

echo -e "\n\nToken: $TOKEN"

# 2. Запрос staff credentials
echo -e "\n\nStaff credentials:"
curl -s -X GET "https://back-erp-gules.vercel.app/api/users/stores/staff-credentials/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a" | python3 -m json.tool
```

## Ожидаемый успешный ответ

```json
{
  "status": "success",
  "data": {
    "username": "test_shop_staff",
    "password": "12345678",
    "full_name": "Сотрудники Тестовый Магазин",
    "is_active": true,
    "store_name": "Тестовый Магазин",
    "tenant_key": "test_shop_4dfa7a5a",
    "note": "Общий аккаунт для всех сотрудников магазина. Используйте его для входа кассиров."
  }
}
```

## Если всё равно 404

1. Проверьте логи сервера
2. Убедитесь что код задеплоен (commit `db7910d` или новее)
3. Проверьте что signal выполнился при создании магазина
4. Создайте staff user вручную (см. выше)

---

**Дата создания:** 2025-11-20
