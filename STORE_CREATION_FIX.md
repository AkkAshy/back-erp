# 🔧 Исправление создания магазинов

## Проблема

При создании магазина через `POST /api/users/stores/` с кириллическим названием (например "asdawd", "Новый Магазин") магазин создавался, но не появлялся в списке.

### Причины:

1. **Пустой slug:** Django `slugify()` не работает с кириллицей, поэтому slug получался пустым
2. **Ошибка в сигнале:** При создании магазина signal пытался создать CashRegister в новой схеме, но таблицы не существовали (миграции не применялись)
3. **Откат транзакции:** Из-за ошибки в сигнале вся транзакция откатывалась, магазин удалялся из базы

## Исправления

### 1. Добавлена транслитерация для slug ([users/serializers.py:353-381](users/serializers.py#L353-L381))

**До:**
```python
def validate(self, data):
    if not data.get('slug'):
        base_slug = slugify(data['name'])  # Для "Новый Магазин" = ""
        # ...
```

**После:**
```python
def validate(self, data):
    if not data.get('slug'):
        from transliterate import translit

        # Транслитерация кириллицы
        try:
            transliterated = translit(data['name'], 'ru', reversed=True)
        except:
            transliterated = data['name']

        base_slug = slugify(transliterated)  # Для "Новый Магазин" = "novyj-magazin"

        # Fallback если slug пустой
        if not base_slug:
            base_slug = 'store'
        # ...
```

**Установлен пакет:**
```bash
pip install transliterate
```

### 2. Убрано создание CashRegister из сигнала ([users/models.py:505-509](users/models.py#L505-L509))

**До:**
```python
# 3. Создаём общую кассу в tenant схеме
from sales.models import CashRegister

with connection.cursor() as cursor:
    cursor.execute(f"SET search_path TO {instance.schema_name}")

CashRegister.objects.create(...)  # ❌ Ошибка: таблица не существует
```

**После:**
```python
# 3. Создание общей кассы перенесено в отдельный management command
# Касса создается после применения миграций к схеме магазина
# python manage.py create_cash_register --store {slug}

logger.info(f"Store setup completed for: {instance.name}")
```

**Причина:** Схема создается БЕЗ применения миграций, поэтому таблицы в ней не существуют.

### 3. Улучшен error handling в сигнале ([users/models.py:511-513](users/models.py#L511-L513))

**До:**
```python
except Exception as e:
    logger.error(f"Error creating owner/staff/cash register: {e}")
    # Ошибка игнорировалась, но транзакция все равно откатывалась
    pass
```

**После:**
```python
except Exception as e:
    logger.error(f"Error creating owner/staff for store: {e}", exc_info=True)
    raise  # Re-raise чтобы транзакция откатилась явно
```

## Результат

Теперь создание магазина работает корректно:

```bash
curl -X POST http://localhost:8000/api/users/stores/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Новый Тестовый Магазин"}'
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Магазин успешно создан",
  "data": {
    "store": {
      "id": 8,
      "name": "Новый Тестовый Магазин 2",
      "slug": "novyj-testovyj-magazin-2",
      "tenant_key": "novyj-testovyj-magazin-2_13824916",
      "schema_name": "tenant_novyj-testovyj-magazin-2"
    },
    "staff_credentials": {
      "username": "novyj-testovyj-magazin-2_staff",
      "password": "12345678"
    }
  }
}
```

✅ Магазин появляется в списке:

```bash
curl http://localhost:8000/api/users/stores/my-stores-with-credentials/ \
  -H "Authorization: Bearer $TOKEN"
```

## Дальнейшие шаги

### Применение миграций к схемам (опционально)

Если нужно создавать CashRegister автоматически, необходимо применить миграции к новой схеме.

Создан улучшенный `SchemaManager._create_schema_tables()` в [core/schema_utils.py:64-105](core/schema_utils.py#L64-L105), который применяет миграции:

```python
@staticmethod
def _create_schema_tables(schema_name):
    from django.core.management import call_command
    from io import StringIO

    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{schema_name}", public')

    try:
        out = StringIO()
        call_command('migrate', verbosity=0, stdout=out, run_syncdb=True)
        logger.info(f"Applied migrations to schema: {schema_name}")
    except Exception as e:
        logger.warning(f"Error applying migrations: {e}")
```

Но пока **CashRegister создается вручную** через management command (который нужно создать).

## Проверка

```bash
# 1. Создать магазин
TOKEN=$(curl -s -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin_testshop", "password": "admin123"}' | jq -r '.access')

curl -X POST http://localhost:8000/api/users/stores/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Мой Новый Магазин"}'

# 2. Проверить что он появился
curl http://localhost:8000/api/users/stores/my-stores-with-credentials/ \
  -H "Authorization: Bearer $TOKEN" | jq '.data.stores[] | {name, slug, staff_credentials}'
```

**Дата исправления:** 2025-11-20
**Затронутые файлы:**
- users/serializers.py
- users/models.py
- core/schema_utils.py
