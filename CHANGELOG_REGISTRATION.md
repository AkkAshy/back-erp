# Изменения: Регистрация владельца в одном окне

## Что сделано

Реализована **полная регистрация владельца магазина в одном запросе**.

Теперь владелец заполняет одну большую форму и получает:
- ✅ Аккаунт пользователя
- ✅ Магазин с полными данными (адрес, город, ИНН и т.д.)
- ✅ Роль владельца
- ✅ JWT токены для входа

---

## Изменённые файлы

### 1. `users/models.py`

**Добавлены поля в модель Store:**

```python
city = models.CharField(max_length=100, blank=True, null=True)
region = models.CharField(max_length=100, blank=True, null=True)
legal_name = models.CharField(max_length=255, blank=True, null=True)
tax_id = models.CharField(max_length=50, blank=True, null=True)
```

**Зачем:**
- Полная информация о магазине сразу при регистрации
- Юридические данные для чеков и отчётов

---

### 2. `users/serializers.py`

**Расширен UserRegistrationSerializer:**

Добавлены поля:
```python
# Личные данные владельца
middle_name  # Отчество

# Данные магазина
store_city
store_region
store_legal_name
store_tax_id
```

**Обновлён метод create():**
```python
store = Store.objects.create(
    # ... существующие поля
    city=validated_data.get('store_city', ''),
    region=validated_data.get('store_region', ''),
    legal_name=validated_data.get('store_legal_name', ''),
    tax_id=validated_data.get('store_tax_id', ''),
)
```

**Обновлён StoreSerializer:**
```python
fields = [
    # ... существующие
    'city', 'region', 'legal_name', 'tax_id'
]
```

---

### 3. `users/views.py`

**Улучшена Swagger документация:**

- Полный пример запроса с всеми полями
- Описание обязательных и опциональных полей
- Примеры ошибок валидации

**Расширен response:**

```python
'store': {
    # ... существующие поля
    'city': store.city,
    'region': store.region,
    'legal_name': store.legal_name,
    'tax_id': store.tax_id
}
```

---

### 4. `customers/models.py`

**Заменено поле performed_by:**

Было:
```python
performed_by = models.CharField(max_length=200)
```

Стало:
```python
performed_by = models.ForeignKey(
    'users.Employee',
    on_delete=models.SET_NULL,
    null=True,
    related_name='customer_transactions'
)
```

---

### 5. `products/models.py`

**Заменено поле created_by в StockReservation:**

Было:
```python
created_by = models.CharField(max_length=100, blank=True)
```

Стало:
```python
created_by = models.ForeignKey(
    'users.Employee',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='stock_reservations'
)
```

---

### 6. `sales/models.py`

**Заменено поле performed_by в CashMovement:**

Было:
```python
performed_by = models.CharField(max_length=200)
```

Стало:
```python
performed_by = models.ForeignKey(
    'users.Employee',
    on_delete=models.SET_NULL,
    null=True,
    related_name='cash_movements'
)
```

---

## Созданные документы

### 1. `REGISTRATION_EXAMPLE.md`
- Полное описание API регистрации
- Структура запроса/ответа
- Примеры использования
- Описание всех полей

### 2. `REGISTRATION_FLOW.md`
- Описание потока регистрации
- Что происходит на backend
- Что делать на frontend после успеха

### 3. `FRONTEND_REGISTRATION_GUIDE.md`
- **Готовый код React компонента**
- CSS стили для формы
- Примеры обработки ошибок
- Инструкции по сохранению данных

---

## API Endpoint

```
POST /api/users/auth/register/
```

**Публичный** (без токена)

---

## Минимальный пример запроса

```json
{
  "first_name": "Иван",
  "owner_phone": "+998901234567",
  "username": "ivan_owner",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "store_name": "Супермаркет Азия",
  "store_address": "ул. Навои, д. 45",
  "store_phone": "+998712345678"
}
```

---

## Полный пример запроса

```json
{
  "first_name": "Иван",
  "last_name": "Петров",
  "middle_name": "Сергеевич",
  "owner_phone": "+998901234567",
  "email": "ivan@example.com",
  "username": "ivan_owner",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "store_name": "Супермаркет Азия",
  "store_address": "ул. Навои, д. 45",
  "store_city": "Ташкент",
  "store_region": "Ташкентская область",
  "store_phone": "+998712345678",
  "store_email": "info@asiamarket.uz",
  "store_legal_name": "ООО Супермаркет Азия",
  "store_tax_id": "123456789"
}
```

---

## Пример ответа

```json
{
  "status": "success",
  "message": "Регистрация успешна",
  "data": {
    "user": {
      "id": 1,
      "username": "ivan_owner",
      "full_name": "Петров Иван"
    },
    "store": {
      "id": 1,
      "name": "Супермаркет Азия",
      "slug": "asia_market",
      "tenant_key": "asia_market_a3f4b2c1",
      "city": "Ташкент",
      "region": "Ташкентская область",
      "legal_name": "ООО Супермаркет Азия",
      "tax_id": "123456789"
    },
    "employee": {
      "id": 1,
      "role": "owner",
      "phone": "+998901234567"
    },
    "tokens": {
      "access": "eyJ0eXAiOi...",
      "refresh": "eyJ0eXAiOi..."
    }
  }
}
```

---

## Миграции

**Необходимо выполнить:**

```bash
source venv/bin/activate
python manage.py makemigrations users customers products sales
python manage.py migrate
```

**Будут созданы миграции для:**
- `users.Store` - добавление city, region, legal_name, tax_id
- `customers.CustomerTransaction` - замена CharField на ForeignKey
- `products.StockReservation` - замена CharField на ForeignKey
- `sales.CashMovement` - замена CharField на ForeignKey

---

## Тестирование

### Через Swagger UI

1. Открыть `http://localhost:8000/swagger/`
2. Найти `POST /api/users/auth/register/`
3. Нажать "Try it out"
4. Заполнить пример данных
5. Execute

### Через cURL

```bash
curl -X POST http://localhost:8000/api/users/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Иван",
    "owner_phone": "+998901234567",
    "username": "ivan_owner",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "store_name": "Супермаркет Азия",
    "store_address": "ул. Навои, д. 45",
    "store_phone": "+998712345678"
  }'
```

### Через Postman

1. Создать новый POST запрос
2. URL: `http://localhost:8000/api/users/auth/register/`
3. Body → raw → JSON
4. Вставить пример JSON
5. Send

---

## Для фронтенда

Готовый React компонент находится в: **`FRONTEND_REGISTRATION_GUIDE.md`**

**Что нужно:**
1. Скопировать компонент из гайда
2. Добавить CSS стили
3. Настроить URL на свой API
4. Готово!

**Что сохранять после регистрации:**
```javascript
localStorage.setItem('access_token', result.data.tokens.access);
localStorage.setItem('refresh_token', result.data.tokens.refresh);
localStorage.setItem('tenant_key', result.data.store.tenant_key); // ВАЖНО!
```

**Использование в запросах:**
```javascript
headers: {
  'Authorization': `Bearer ${access_token}`,
  'X-Tenant-Key': tenant_key
}
```

---

## Итого

✅ Регистрация в одном запросе
✅ Все данные магазина сразу
✅ ForeignKey вместо CharField
✅ Swagger документация
✅ Готовый код для фронтенда

**Владелец не лазит по интерфейсу - заполнил одну форму и работает!**
