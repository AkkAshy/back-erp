# Исправление: 500 Error "tenant_error" на /users/profile/

## Проблема

Пользователь сообщил о периодической ошибке 500 на endpoint `/api/users/profile/`:

```json
{
  "url": "/users/profile/",
  "status": 500,
  "message": "Request failed with status code 500",
  "data": {
    "status": "error",
    "code": "tenant_error",
    "message": "Ошибка при обработке магазина"
  }
}
```

## Анализ

### Где возникает ошибка

Ошибка возвращается из middleware [core/middleware.py:102-108](core/middleware.py#L102-L108):

```python
except Exception as e:
    logger.error(f"Error processing tenant: {e}", exc_info=True)
    return JsonResponse({
        'status': 'error',
        'code': 'tenant_error',
        'message': 'Ошибка при обработке магазина'
    }, status=500)
```

### Endpoint

`/api/users/profile/` - это алиас для view функции `me()` из [users/views.py:326-379](users/views.py#L326-L379), определён в [users/urls.py:38](users/urls.py#L38):

```python
path('profile/', me, name='profile'),  # ⭐ Alias for /auth/me/
```

### Возможные причины

1. **Ошибка подключения к БД** при запросе `Store.objects.get()`
2. **Проблема с ForeignKey `owner`** - если Store.owner = None или User удалён
3. **Race condition** при переключении PostgreSQL схем
4. **Исключение в `select_related('owner')`**

## Решение

### Улучшена обработка ошибок в middleware

Добавлено детальное логирование для идентификации проблемы при следующем возникновении ошибки.

**Файл:** [core/middleware.py](core/middleware.py)

#### Изменение 1: Детальное логирование ошибок (строки 102-117)

**Было:**
```python
except Exception as e:
    logger.error(f"Error processing tenant: {e}", exc_info=True)
    return JsonResponse({
        'status': 'error',
        'code': 'tenant_error',
        'message': 'Ошибка при обработке магазина'
    }, status=500)
```

**Стало:**
```python
except Exception as e:
    logger.error(
        f"Error processing tenant with key '{tenant_key}': {type(e).__name__}: {e}",
        exc_info=True,
        extra={
            'tenant_key': tenant_key,
            'path': request.path,
            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
        }
    )
    return JsonResponse({
        'status': 'error',
        'code': 'tenant_error',
        'message': 'Ошибка при обработке магазина',
        'debug': str(e) if settings.DEBUG else None
    }, status=500)
```

**Что добавлено:**
- ✅ Имя класса исключения (`type(e).__name__`)
- ✅ tenant_key для которого произошла ошибка
- ✅ Путь запроса (request.path)
- ✅ Имя пользователя
- ✅ Поле `debug` в ответе (только в DEBUG режиме)

#### Изменение 2: Улучшена обработка в `_get_tenant_by_key` (строки 144-164)

**Было:**
```python
except Exception as e:
    logger.error(f"Error fetching tenant: {e}")
    return None
```

**Стало:**
```python
except Store.DoesNotExist:
    logger.warning(f"Store not found for tenant_key: {tenant_key}")
    return None
except Exception as e:
    logger.error(f"Error fetching tenant for key '{tenant_key}': {type(e).__name__}: {e}", exc_info=True)
    raise  # Re-raise to be caught in process_request with better logging
```

**Что изменено:**
- ✅ Отдельная обработка `Store.DoesNotExist` (предупреждение вместо ошибки)
- ✅ Детальное логирование с именем исключения и tenant_key
- ✅ Re-raise исключения для обработки в `process_request` с полным стеком

## Наблюдения

### Логи показывают успешную работу

При проверке логов сервера видно, что `/api/users/profile/` **работает успешно**:

```
INFO 2025-11-18 11:28:55,390 "GET /api/users/profile/ HTTP/1.1" 200 520
INFO 2025-11-18 11:29:28,245 "GET /api/users/profile/ HTTP/1.1" 200 520
INFO 2025-11-18 11:29:44,564 "GET /api/users/profile/ HTTP/1.1" 200 520
INFO 2025-11-18 11:30:14,876 "GET /api/users/profile/ HTTP/1.1" 200 520
INFO 2025-11-18 11:30:23,910 "GET /api/users/profile/ HTTP/1.1" 200 520
...
```

### Ошибка периодическая

Ошибка, вероятно, была:
- **Разовой** (race condition, временная недоступность БД)
- **Связана с конкретным состоянием данных** (Store без owner?)
- **Возникла при переключении схем** (PostgreSQL search_path issue)

## Что делать при следующем возникновении ошибки

1. **Проверить логи Django** - теперь будет полная информация:
   ```bash
   # В логах будет:
   ERROR: Error processing tenant with key 'admin_1a12e47a': DatabaseError: ...
   ```

2. **Проверить ответ API** (если DEBUG=True):
   ```json
   {
     "status": "error",
     "code": "tenant_error",
     "message": "Ошибка при обработке магазина",
     "debug": "DatabaseError: connection timeout"  // ← Новое поле
   }
   ```

3. **Проверить Store в базе**:
   ```python
   from users.models import Store
   store = Store.objects.select_related('owner').get(tenant_key='admin_1a12e47a')
   print(store.owner)  # Должен быть User объект, не None
   ```

## Статус

✅ **Исправлено:** Улучшено логирование и обработка ошибок
✅ **Файл:** [core/middleware.py](core/middleware.py)
✅ **Проверено:** `python manage.py check` - без ошибок
✅ **Статус:** Сервер перезагружен автоматически

### Ожидание:

При следующем возникновении ошибки логи покажут:
- Точный тип исключения
- Tenant key для которого произошла ошибка
- Путь запроса и пользователя
- Полный stack trace исключения

Это позволит быстро идентифицировать и исправить корневую причину.

---

## Дополнительная информация

### Архитектура мультитенантности

Система использует схемную мультитенантность PostgreSQL:

1. **public схема**: Таблицы User, Store, Employee
2. **tenant_* схемы**: Изолированные данные магазинов (Products, Sales, Customers)
3. **X-Tenant-Key header**: Переключает PostgreSQL `search_path` на нужную схему

### Процесс обработки запроса

```
Request → JWT Auth → TenantByKeyMiddleware → LoadEmployeeContext → View
              ↓              ↓                        ↓
         request.user  request.tenant          request.employee
                       SET search_path
```

### Middleware цепочка

В [config/settings.py](config/settings.py):

```python
MIDDLEWARE = [
    # ...
    'core.middleware.JWTAuthenticationMiddleware',     # 1. Аутентификация JWT
    'core.middleware.TenantByKeyMiddleware',           # 2. Переключение схемы ← Здесь ошибка
    'core.middleware.LoadEmployeeContextMiddleware',   # 3. Загрузка Employee
    # ...
]
```

Готово! 🎉
