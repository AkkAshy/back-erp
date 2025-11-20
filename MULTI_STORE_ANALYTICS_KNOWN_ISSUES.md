# ⚠️ Известные проблемы - Мульти-магазинная аналитика

## Проблема #1: Одинаковые данные для всех магазинов

### Описание
При запросе аналитики все магазины показывают одинаковые данные:

```json
{
  "by_store": [
    {
      "store_name": "asdawd",
      "total_sales": 409200000.0,
      "sales_count": 19
    },
    {
      "store_name": "test_shop",
      "total_sales": 409200000.0,  // ❌ Одинаково!
      "sales_count": 19               // ❌ Одинаково!
    }
  ]
}
```

### Причина
Таблицы аналитики (`analytics_daily_sales`) находятся в **public** схеме, а не в tenant-specific схемах. Все магазины читают данные из одной таблицы.

### Диагностика
```bash
python manage.py shell << 'EOF'
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE tablename LIKE 'analytics%'
    """)
    for schema, table in cursor.fetchall():
        print(f"{schema}.{table}")
EOF
```

**Текущий вывод:**
```
public.analytics_daily_sales
public.analytics_product_performance
public.analytics_customer
public.analytics_inventory_snapshot
```

**Ожидаемый вывод:**
```
tenant_test_shop.analytics_daily_sales
tenant_asdawd.analytics_daily_sales
tenant_magazin_2.analytics_daily_sales
...
```

### Решение

#### Вариант 1: Применить миграции к tenant схемам (рекомендуется)

Нужно создать management command для применения миграций к существующим tenant схемам:

```python
# users/management/commands/migrate_tenant_schemas.py

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from users.models import Store

class Command(BaseCommand):
    help = 'Применяет миграции ко всем tenant схемам'

    def handle(self, *args, **options):
        stores = Store.objects.filter(is_active=True)

        for store in stores:
            self.stdout.write(f"\n📦 Применение миграций к {store.schema_name}...")

            try:
                # Переключаемся на tenant схему
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{store.schema_name}", public')

                # Применяем миграции
                call_command('migrate', verbosity=1, interactive=False)

                self.stdout.write(self.style.SUCCESS(
                    f'✅ Миграции применены к {store.name}'
                ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'❌ Ошибка для {store.name}: {e}'
                ))

            finally:
                # Возвращаем схему обратно
                with connection.cursor() as cursor:
                    cursor.execute('SET search_path TO public')
```

**Использование:**
```bash
python manage.py migrate_tenant_schemas
```

#### Вариант 2: Временное решение - Отключить мульти-магазинную аналитику

Добавить предупреждение в ответ API:

```python
return Response({
    'status': 'success',
    'warning': 'Аналитика работает в режиме single-tenant. Данные могут быть неточными.',
    'data': {
        ...
    }
})
```

---

## Проблема #2: Ошибка с дефисами в schema_name

### Описание
```json
{
  "status": "error",
  "code": "tenant_error",
  "message": "Ошибка при обработке магазина",
  "debug": "syntax error at or near \"-\"\nLINE 1: SET search_path TO tenant_novyj-testovyj-magazin-2, public"
}
```

### Причина
PostgreSQL не принимает дефисы в именах схем без кавычек. Slug магазина генерируется с дефисами (например: `novyj-testovyj-magazin-2`), и schema_name создается как `tenant_{slug}`.

### Решение

✅ **Исправлено в коммите от 2025-11-20**

**Изменения:**

1. **users/models.py (строка 173-176):**
```python
# Было:
self.schema_name = f"tenant_{self.slug}"

# Стало:
safe_slug = self.slug.replace('-', '_')
self.schema_name = f"tenant_{safe_slug}"
```

2. **Миграция существующих магазинов:**
```bash
python manage.py shell << 'EOF'
from users.models import Store

stores = Store.objects.filter(schema_name__contains='-')
for store in stores:
    safe_slug = store.slug.replace('-', '_')
    store.schema_name = f"tenant_{safe_slug}"
    store.save()
    print(f"✅ Обновлен: {store.name}")
EOF
```

**Результат:**
- `tenant_novyj-testovyj-magazin-2` → `tenant_novyj_testovyj_magazin_2` ✅
- Ошибки больше нет ✅

---

## Проверка статуса

### 1. Проверить схемы магазинов

```bash
python manage.py shell << 'EOF'
from users.models import Store

for store in Store.objects.filter(is_active=True):
    print(f"{store.name}:")
    print(f"  slug: {store.slug}")
    print(f"  schema: {store.schema_name}")
    print(f"  has hyphens: {'-' in store.schema_name}")
    print()
EOF
```

### 2. Проверить наличие таблиц в tenant схемах

```bash
python manage.py shell << 'EOF'
from django.db import connection
from users.models import Store

for store in Store.objects.filter(is_active=True):
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = '{store.schema_name}'
            AND tablename LIKE 'analytics%'
        """)

        tables = cursor.fetchall()
        print(f"{store.name} ({store.schema_name}):")
        if tables:
            for (table,) in tables:
                print(f"  ✅ {table}")
        else:
            print(f"  ❌ Нет таблиц аналитики")
        print()
EOF
```

---

## Рекомендации

1. **Немедленно:**
   - ✅ Исправлены дефисы в schema_name
   - ⚠️ Документировать текущее поведение

2. **В ближайшее время:**
   - 🔧 Создать management command для миграций tenant схем
   - 🔧 Применить миграции ко всем существующим схемам
   - ✅ Проверить что аналитика работает корректно

3. **В будущем:**
   - 📝 Автоматически применять миграции при создании нового магазина
   - 📝 Добавить тесты для проверки tenant-isolation

---

## Временное решение (пока не исправлено)

Если аналитика показывает одинаковые данные, используйте аналитику для каждого магазина отдельно с X-Tenant-Key:

```bash
# Вместо multi-store analytics
curl "/api/users/stores/multi-store-analytics/?period=month" \
  -H "Authorization: Bearer $TOKEN"

# Используйте для каждого магазина:
curl "/api/analytics/daily-sales-reports/?period=month" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a"

curl "/api/analytics/daily-sales-reports/?period=month" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Key: asdawd_8b43a536"
```

---

**Дата создания:** 2025-11-20
**Статус:** Проблема #1 требует исправления, Проблема #2 исправлена
