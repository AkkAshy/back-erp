# Быстрый тест для Print Label endpoint

## Проблема: "Страница не найдена" (404)

Если вы получаете ошибку 404, проверьте следующее:

### 1. Правильный URL

Endpoint находится здесь:
```
GET /api/products/products/{product_id}/print-label/
```

**Важно:** Обратите внимание на `/products/products/` (дважды "products")!

#### ❌ Неправильно:
```
GET /api/products/print-label/       ← НЕ РАБОТАЕТ
GET /api/products/{id}/print-label/  ← НЕ РАБОТАЕТ
```

#### ✅ Правильно:
```
GET /api/products/products/1/print-label/
GET /api/products/products/123/print-label/
```

---

## 2. Проверка URL в браузере/Postman

### Базовый URL:
```
http://localhost:8000/api/products/products/1/print-label/
```

Замените `1` на ID вашего товара.

---

## 3. Обязательные заголовки

Не забудьте добавить:
```
Authorization: Bearer {ваш_access_token}
X-Tenant-Key: {ваш_tenant_key}
```

---

## 4. Пример cURL для тестирования

```bash
# Сначала получите access_token и tenant_key
# Затем:

curl -X GET "http://localhost:8000/api/products/products/1/print-label/" \
  -H "Authorization: Bearer ВАШ_ACCESS_TOKEN" \
  -H "X-Tenant-Key: ВАШ_TENANT_KEY"
```

---

## 5. Frontend (Axios)

```typescript
// Правильный вызов
const response = await api.get(`/products/products/${productId}/print-label/`);
//                                       ^^^^^^^^^^ дважды "products"!

// НЕ ПРАВИЛЬНО:
// const response = await api.get(`/products/${productId}/print-label/`);
```

---

## 6. Проверка что товар существует

Перед вызовом print-label, убедитесь что товар с таким ID существует:

```bash
GET /api/products/products/1/

# Должен вернуть данные товара
```

---

## 7. Возможные ошибки

### 404 Not Found - "Страница не найдена"
**Причина:** Неправильный URL
**Решение:** Используйте `/api/products/products/{id}/print-label/` (не `/api/products/print-label/`)

### 403 Forbidden - "Заголовок X-Tenant-Key обязателен"
**Причина:** Отсутствует X-Tenant-Key
**Решение:** Добавьте заголовок `X-Tenant-Key`

### 401 Unauthorized
**Причина:** Отсутствует или неверный токен
**Решение:** Добавьте правильный `Authorization: Bearer {token}`

### 400 Bad Request - "У товара не указана цена"
**Причина:** У товара нет pricing записи
**Решение:** Добавьте цену товару через админку или API

---

## 8. Быстрый тест в браузере

1. Войдите в систему через фронтенд
2. Откройте DevTools (F12) → Console
3. Выполните:

```javascript
// Получите productId из списка товаров
const productId = 1; // замените на существующий ID

// Вызовите API
fetch(`http://localhost:8000/api/products/products/${productId}/print-label/`, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'X-Tenant-Key': localStorage.getItem('tenant_key')
  }
})
.then(r => r.json())
.then(data => console.log(data));
```

---

## 9. Ожидаемый ответ (успех)

```json
{
  "status": "success",
  "data": {
    "product": {
      "id": 1,
      "name": "Молоко",
      "sku": "MLK-001",
      "barcode": "4870012345678",
      "unit": "л"
    },
    "price": {
      "sale_price": 12000.0,
      "formatted_price": "12,000.00",
      "currency": "сум"
    },
    "barcode_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEU...",
    "quantity": 1,
    "generated_at": "2025-11-17T19:20:00.000000+05:00"
  }
}
```

---

## 10. Резюме

### Чек-лист:
- [ ] URL правильный: `/api/products/products/{id}/print-label/` (дважды "products")
- [ ] ID товара существует
- [ ] Добавлен заголовок `Authorization`
- [ ] Добавлен заголовок `X-Tenant-Key`
- [ ] У товара есть цена (pricing)
- [ ] Сервер запущен (`python manage.py runserver`)

### Правильный URL еще раз:
```
http://localhost:8000/api/products/products/{PRODUCT_ID}/print-label/
                                    ^^^^^^^^
                                    дважды!
```

Если всё еще получаете 404, проверьте:
1. Сервер запущен? (`lsof -ti:8000` должен показать процесс)
2. URL точно такой: `/api/products/products/1/print-label/`?
3. Перезагрузили сервер после добавления endpoint?

---

**Сервер перезапущен ✅**

Endpoint должен работать сейчас!
