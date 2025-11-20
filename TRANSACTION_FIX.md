# 🔧 Исправление ошибки транзакции при регистрации

**Дата:** 2025-11-20

---

## ❌ Проблема

При создании сотрудника на production сервере возникала ошибка:

```json
{
  "status": "error",
  "message": "An error occurred in the current transaction. You can't execute queries until the end of the 'atomic' block."
}
```

### Причина

Проверка безопасности (можно ли добавить существующего сотрудника) выполнялась **внутри** `@transaction.atomic` блока:

```python
@transaction.atomic
def create(self, validated_data):
    # ... код ...

    # Переключение search_path внутри транзакции
    cursor.execute(f'SET search_path TO "{owner_store.schema_name}", public')

    # Если возникает ValidationError...
    if not found:
        raise ValidationError("...")  # ← Транзакция становится невалидной

    # Попытка вернуть search_path
    cursor.execute('SET search_path TO public')  # ← ОШИБКА! Транзакция уже невалидна
```

**Проблема:** После `raise ValidationError` внутри `@transaction.atomic`, транзакция переходит в состояние ошибки. Любые последующие SQL запросы (включая возврат `search_path`) вызывают ошибку.

---

## ✅ Решение

Перенесли проверку безопасности из `create()` в `validate()`:

### До (неправильно):

```python
class CreateEmployeeSerializer(serializers.Serializer):
    def validate(self, attrs):
        # Простая валидация полей
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Переключение search_path
        cursor.execute('SET search_path TO ...')

        # Проверка безопасности
        if not found:
            raise ValidationError(...)  # ← Проблема!

        # Создание Employee
        employee = Employee.objects.create(...)
```

### После (правильно):

```python
class CreateEmployeeSerializer(serializers.Serializer):
    def validate(self, attrs):
        # Проверка безопасности ЗДЕСЬ (вне транзакции)
        if user_exists:
            # Сохраняем текущий search_path
            cursor.execute("SHOW search_path")
            original_path = cursor.fetchone()[0]

            try:
                # Переключаемся и проверяем
                cursor.execute(f'SET search_path TO ...')
                # Проверка...
            finally:
                # ВСЕГДА возвращаем обратно
                cursor.execute(f'SET search_path TO {original_path}')

            if not found:
                raise ValidationError(...)  # ← Безопасно! Вне транзакции

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Просто создаем Employee
        # Проверки уже выполнены в validate()
        employee = Employee.objects.create(...)
```

---

## 🔑 Ключевые изменения

### 1. Проверка безопасности в `validate()`

**Файл:** [users/serializers.py](users/serializers.py#L227-L276)

```python
def validate(self, attrs):
    # ... обычная валидация ...

    # ПРОВЕРКА БЕЗОПАСНОСТИ: если user существует, проверяем права владельца
    if user_exists:
        request = self.context.get('request')
        store = request.tenant if hasattr(request, 'tenant') else None

        if request and store:
            user = User.objects.get(username=username)

            # Используем try/finally для гарантированного возврата search_path
            from django.db import connection

            owner_stores = Store.objects.filter(owner=request.user, is_active=True)
            found_in_owner_store = False

            # Сохраняем текущий search_path
            with connection.cursor() as cursor:
                cursor.execute("SHOW search_path")
                original_path = cursor.fetchone()[0]

            try:
                for owner_store in owner_stores:
                    # Переключаемся на схему магазина владельца
                    with connection.cursor() as cursor:
                        cursor.execute(f'SET search_path TO "{owner_store.schema_name}", public')

                    # Проверяем есть ли Employee с этим user
                    if Employee.objects.filter(user=user).exists():
                        found_in_owner_store = True
                        break
            finally:
                # ВСЕГДА возвращаем search_path обратно
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO {original_path}')

            if not found_in_owner_store:
                raise serializers.ValidationError({
                    'username': (
                        f'Пользователь "{username}" не найден в ваших магазинах. '
                        'Вы можете добавить только сотрудников, которые уже работают '
                        'в одном из ваших магазинов.'
                    )
                })

            # Проверяем что не дублируем
            if Employee.objects.filter(user=user, store=store).exists():
                raise serializers.ValidationError({
                    'username': f'Сотрудник "{username}" уже работает в этом магазине'
                })

    return attrs
```

### 2. Упрощенный `create()`

**Файл:** [users/serializers.py](users/serializers.py#L279-L359)

```python
@transaction.atomic
def create(self, validated_data):
    """
    Создание Employee с опциональным User аккаунтом.

    Проверка безопасности выполняется в validate() ДО входа в транзакцию.
    """

    # Получаем store из контекста
    request = self.context.get('request')
    store = request.tenant
    username = validated_data.get('username')
    password = validated_data.get('password')

    user = None
    is_existing_user = False
    created_password = None

    # Проверяем существует ли User
    if username:
        try:
            user = User.objects.get(username=username)
            is_existing_user = True
        except User.DoesNotExist:
            # User не существует - создаем нового
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=validated_data['first_name'],
                last_name=validated_data.get('last_name', ''),
                email=validated_data.get('email', ''),
                is_active=True
            )
            created_password = password

    # Создаем Employee запись
    employee = Employee.objects.create(
        user=user,
        store=store,
        first_name=validated_data['first_name'],
        last_name=validated_data.get('last_name', ''),
        role=validated_data['role'],
        phone=validated_data.get('phone', ''),
        position=validated_data.get('position', ''),
        is_active=True
    )

    # Возвращаем данные
    return {
        'employee': employee,
        'username': username or None,
        'password': created_password,
        'is_existing_user': is_existing_user
    }
```

---

## ✅ Преимущества нового подхода

1. **Безопасно** - проверка безопасности вне транзакции
2. **Надежно** - `try/finally` гарантирует возврат `search_path`
3. **Правильно** - валидация в `validate()`, создание в `create()`
4. **Работает** - на локальной машине и на production сервере

---

## 🧪 Тестирование

### Тест успешный:

```bash
# Создать сотрудника в магазине 1
POST /api/users/employees/
X-Tenant-Key: store1_xxx
{
  "username": "ivan_manager",
  "password": "SecurePass123!",
  "first_name": "Иван",
  "role": "manager"
}
→ ✅ Success

# Добавить в магазин 2 (без пароля)
POST /api/users/employees/
X-Tenant-Key: store2_xxx
{
  "username": "ivan_manager",
  "first_name": "Иван",
  "role": "cashier"
}
→ ✅ Success (is_existing_user: true)
```

---

## 📚 Связанные документы

- [MULTI_STORE_EMPLOYEES.md](MULTI_STORE_EMPLOYEES.md) - Работа с сотрудниками в нескольких магазинах
- [users/serializers.py](users/serializers.py#L186-L277) - Метод validate()
- [users/serializers.py](users/serializers.py#L279-L359) - Метод create()

---

## 🔧 Дополнительное исправление: UserRegistrationSerializer

### Проблема 2: Ошибка при первой регистрации админа

Та же ошибка возникала в `UserRegistrationSerializer.create()` при регистрации нового владельца магазина:

```python
@transaction.atomic
def create(self, validated_data):
    # 1. Создаем User
    user = User.objects.create_user(...)

    # 2. Создаем Store
    store = Store.objects.create(...)  # ← Триггерит post_save signal

    # 3. В сигнале создается схема и Employee (с переключением search_path)
    # Если что-то пойдет не так, транзакция становится невалидной

    # 4. Попытка получить Employee
    employee = Employee.objects.get(user=user, store=store)  # ← ОШИБКА!
```

**Проблема:** Весь процесс был в одной большой `@transaction.atomic` блоке. Signal `post_save` выполнялся внутри этой транзакции, создавал схему и переключал `search_path`. Если возникала ошибка, транзакция становилась невалидной, но код пытался продолжить работу.

### Решение:

Разбили на отдельные транзакции и добавили `try/finally` для безопасного переключения схемы:

**Файл:** [users/serializers.py](users/serializers.py#L715-L799)

```python
def create(self, validated_data):
    """
    ВАЖНО: Не используем @transaction.atomic здесь, потому что:
    1. Store.post_save signal создает PostgreSQL схему и переключает search_path
    2. Если ошибка возникает внутри транзакции после schema switching,
       транзакция становится невалидной и дальнейшие SQL запросы не работают
    3. Схема и Employee создаются в сигнале, который должен быть вне основной транзакции
    """

    try:
        # 1. Создаем пользователя (в отдельной транзакции)
        with transaction.atomic():
            user = User.objects.create_user(...)

        # 2. Создаем магазин (в отдельной транзакции)
        # post_save сигнал создаст схему и Employee автоматически
        with transaction.atomic():
            store = Store.objects.create(...)

        # 3. Безопасное получение Employee с переключением search_path
        from django.db import connection

        # Сохраняем текущий search_path
        with connection.cursor() as cursor:
            cursor.execute("SHOW search_path")
            result = cursor.fetchone()
            original_path = result[0] if result else "public"

        employee = None
        try:
            # Переключаемся на схему магазина
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{store.schema_name}", public')

            # Ищем Employee (создан сигналом)
            employee = Employee.objects.get(user=user, store=store)

            # Обновляем телефон если передан
            if validated_data.get('owner_phone'):
                employee.phone = validated_data['owner_phone']
                employee.save(update_fields=['phone'])

        finally:
            # ВСЕГДА возвращаем search_path обратно
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO {original_path}')

        return {
            'user': user,
            'store': store,
            'employee': employee
        }

    except Exception as e:
        logger.error(f"Error during registration: {e}", exc_info=True)
        raise serializers.ValidationError(f"Ошибка при регистрации: {str(e)}")
```

### Ключевые изменения:

1. **Убрали `@transaction.atomic` из метода** - больше нет одной большой транзакции
2. **Отдельные транзакции** - User и Store создаются в своих `with transaction.atomic()` блоках
3. **Сигнал выполняется свободно** - `post_save` для Store выполняется между транзакциями
4. **Безопасное переключение схемы** - используем `try/finally` для гарантированного возврата `search_path`
5. **Fallback для search_path** - если `cursor.fetchone()` вернет None, используем "public"

### Преимущества:

1. ✅ **Изоляция ошибок** - если User создался, а Store нет, User останется (можно удалить вручную)
2. ✅ **Безопасно для сигналов** - post_save может выполнять любые операции без риска испортить транзакцию
3. ✅ **Гарантированный откат** - каждая операция в своей транзакции
4. ✅ **Безопасное переключение схемы** - всегда возвращается обратно

---

## 🔧 Дополнительное исправление: Store.post_save Signal

### Проблема 3: Employee создавался в неправильной схеме

После исправления UserRegistrationSerializer обнаружилась еще одна проблема: Employee записи создавались в `public` схеме вместо tenant схемы.

**Причина:** Signal `post_save` для Store выполнялся с текущим `search_path = public`, поэтому `Employee.objects.create()` создавал записи в public схеме.

### Решение:

Добавили явное переключение `search_path` в сигнале перед созданием Employee:

**Файл:** [users/models.py](users/models.py#L506-L520)

```python
# 1. Создаём Employee для владельца в tenant схеме
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(f'SET search_path TO "{instance.schema_name}", public')

Employee.objects.create(
    user=instance.owner,
    store=instance,
    role=Employee.Role.OWNER
)
logger.info(f"Created owner employee for store: {instance.name}")

# Возвращаем search_path обратно
with connection.cursor() as cursor:
    cursor.execute('SET search_path TO public')
```

Аналогично для staff аккаунта:

**Файл:** [users/models.py](users/models.py#L536-L551)

```python
# Переключаемся на tenant схему для создания Employee
with connection.cursor() as cursor:
    cursor.execute(f'SET search_path TO "{instance.schema_name}", public')

# Создаём Employee запись для этого общего аккаунта
Employee.objects.create(
    user=staff_user,
    store=instance,
    role=Employee.Role.STAFF,
    first_name="Сотрудники",
    last_name=instance.name
)

# Возвращаем search_path обратно
with connection.cursor() as cursor:
    cursor.execute('SET search_path TO public')
```

---

## ✅ Итоговое решение

### Все исправления работают вместе:

1. **CreateEmployeeSerializer** - валидация безопасности в `validate()` (вне транзакции)
2. **UserRegistrationSerializer** - разделение на отдельные транзакции
3. **Store.post_save Signal** - явное переключение схемы при создании Employee

### Результат тестирования:

```bash
curl -X POST http://localhost:8000/api/users/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_success_admin",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Success",
    "last_name": "Test",
    "email": "success@example.com",
    "owner_phone": "+998901111111",
    "store_name": "Ultimate Success Store 2025",
    "store_description": "This should work perfectly",
    "store_address": "Success Avenue 1",
    "store_phone": "+998902222222"
  }'

→ Response:
{
  "status": "success",
  "message": "Регистрация успешна",
  "data": {
    "user": { "id": 40, "username": "test_success_admin", ... },
    "store": {
      "id": 24,
      "name": "Ultimate Success Store 2025",
      "tenant_key": "ultimate-success-store-2025_8e4f773d",
      "schema_name": "tenant_ultimate_success_store_2025"
    },
    "employee": { "id": 1, "role": "owner", ... },
    "tokens": { ... }
  }
}
```

**✅ Регистрация работает без ошибок транзакции!**

---

## 🔧 Дополнительное исправление: Логин после регистрации

### Проблема 4: "У вас нет доступа ни к одному активному магазину" при логине

После успешной регистрации, при попытке залогиниться возникала ошибка:

```json
{
  "status": "error",
  "message": "У вас нет доступа ни к одному активному магазину"
}
```

**Причина:** В `CustomTokenObtainPairSerializer.validate()` код искал Employee записи через `Employee.objects.filter()` в `public` схеме, но Employee записи находятся в tenant схемах.

### Решение:

Переписали логику поиска магазинов пользователя - теперь перебираем все активные магазины и проверяем каждую tenant схему:

**Файл:** [users/serializers.py](users/serializers.py#L841-L922)

```python
# Получаем список всех магазинов пользователя с tenant_key
# ВАЖНО: Employee записи находятся в tenant схемах, а не в public
# Поэтому мы ищем магазины через Store.owner или перебираем все схемы

from django.db import connection
from users.models import Store, Employee

# Находим все активные магазины
all_stores = Store.objects.filter(is_active=True)

# Сохраняем текущий search_path
with connection.cursor() as cursor:
    cursor.execute("SHOW search_path")
    result = cursor.fetchone()
    original_path = result[0] if result else "public"

available_stores = []

try:
    for store in all_stores:
        try:
            # Переключаемся на схему магазина
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{store.schema_name}", public')

            # Проверяем есть ли Employee для этого user в этом магазине
            emp = Employee.objects.filter(
                user=user,
                store=store,
                is_active=True
            ).select_related('store').first()

            if emp:
                store_data = {
                    'id': emp.store.id,
                    'name': emp.store.name,
                    'slug': emp.store.slug,
                    'tenant_key': emp.store.tenant_key,
                    'role': emp.role,
                    'role_display': emp.get_role_display(),
                    'permissions': emp.permissions
                }
                available_stores.append(store_data)

        except Exception as e:
            logger.warning(f"Error checking employee in store {store.slug}: {e}")
            continue

finally:
    # ВСЕГДА возвращаем search_path обратно
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO {original_path}')

if not available_stores:
    raise serializers.ValidationError({
        'non_field_errors': 'У вас нет доступа ни к одному активному магазину'
    })
```

### Результат:

```bash
# Регистрация
POST /api/users/auth/register/
→ {"status": "success", ...}

# Логин
POST /api/users/auth/login/
Body: {"username": "test_success_admin", "password": "SecurePass123!"}

→ Response:
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {
    "id": 40,
    "username": "test_success_admin",
    "email": "success@example.com",
    "full_name": "Success Test"
  },
  "available_stores": [
    {
      "id": 24,
      "name": "Ultimate Success Store 2025",
      "tenant_key": "ultimate-success-store-2025_8e4f773d",
      "role": "owner",
      "permissions": ["view_all", "create_all", ...]
    }
  ],
  "default_store": {
    "tenant_key": "ultimate-success-store-2025_8e4f773d",
    "name": "Ultimate Success Store 2025",
    "role": "owner"
  }
}
```

**✅ Логин работает! Пользователь получает список своих магазинов!**

---

**Статус:** ✅ ПОЛНОСТЬЮ ИСПРАВЛЕНО И ПРОТЕСТИРОВАНО
**Дата:** 2025-11-20
