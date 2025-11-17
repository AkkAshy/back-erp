# Диагностика проблемы с логином (401)

## Проблема
При логине получаете ошибку **401 Unauthorized**.

## Возможные причины

### 1. Неверный пароль
Самая очевидная причина.

### 2. Пользователя не существует
Проверьте что username правильный.

### 3. У пользователя нет Employee записи
После регистрации должна автоматически создаться запись Employee. Если её нет - логин не пройдет.

### 4. Магазин или Employee неактивен
Даже если Employee есть, но `is_active=False` или `store.is_active=False` - логин не пройдет.

---

## Как проверить через Django shell

### Шаг 1: Войти в Django shell
```bash
cd /Users/akkanat/Projects/erp_v2/new_backend
source venv/bin/activate
python manage.py shell
```

### Шаг 2: Проверить пользователя
```python
from django.contrib.auth.models import User
from users.models import Employee, Store

# Замените username на свой
username = 'testuser'

# Проверяем что пользователь существует
try:
    user = User.objects.get(username=username)
    print(f"✓ Пользователь найден: {user.username}")
    print(f"  - ID: {user.id}")
    print(f"  - Email: {user.email}")
    print(f"  - Активен: {user.is_active}")
except User.DoesNotExist:
    print("✗ Пользователь не найден!")
    exit()

# Проверяем пароль (опционально)
# print(f"  - Может войти: {user.check_password('YourPassword123!')}")
```

### Шаг 3: Проверить Employee записи
```python
# Проверяем Employee записи
employees = Employee.objects.filter(user=user)
print(f"\nEmployee записей: {employees.count()}")

for emp in employees:
    print(f"\n  Employee #{emp.id}:")
    print(f"    - Магазин: {emp.store.name}")
    print(f"    - Роль: {emp.role} ({emp.get_role_display()})")
    print(f"    - Активен: {emp.is_active}")
    print(f"    - Магазин активен: {emp.store.is_active}")
    print(f"    - Tenant key: {emp.store.tenant_key}")
```

### Шаг 4: Проверить активные Employee
```python
# Это то, что проверяет логин
active_employees = Employee.objects.filter(
    user=user,
    is_active=True,
    store__is_active=True
)

print(f"\nАктивных Employee (для логина): {active_employees.count()}")

if active_employees.count() == 0:
    print("✗ НЕТ АКТИВНЫХ EMPLOYEE - ЛОГИН НЕ ПРОЙДЕТ!")
    print("\nПричины:")
    if employees.count() == 0:
        print("  - Employee записи не существуют (не создались при регистрации)")
    else:
        for emp in employees:
            if not emp.is_active:
                print(f"  - Employee #{emp.id} неактивен")
            if not emp.store.is_active:
                print(f"  - Магазин '{emp.store.name}' неактивен")
else:
    print("✓ Есть активные Employee - логин должен работать")
```

---

## Как исправить

### Проблема 1: Employee не существует

Создайте Employee вручную:

```python
from users.models import Employee, Store
from django.contrib.auth.models import User

# Получаем пользователя
user = User.objects.get(username='testuser')

# Получаем магазин (или создаём тестовый)
try:
    store = Store.objects.first()
    if not store:
        store = Store.objects.create(
            name='Test Store',
            slug='test-store',
            owner=user,
            is_active=True
        )
        print(f"Создан магазин: {store.name}")
except:
    print("Ошибка при создании магазина")

# Создаём Employee
employee = Employee.objects.create(
    user=user,
    store=store,
    role='owner',
    is_active=True
)

print(f"✓ Создан Employee для {user.username} в магазине {store.name}")
print(f"  Tenant key: {store.tenant_key}")
```

### Проблема 2: Employee неактивен

```python
# Активируем всех Employee пользователя
Employee.objects.filter(user__username='testuser').update(is_active=True)
print("✓ Все Employee активированы")
```

### Проблема 3: Магазин неактивен

```python
# Активируем все магазины
Store.objects.all().update(is_active=True)
print("✓ Все магазины активированы")
```

---

## Быстрая проверка (одна команда)

```python
from django.contrib.auth.models import User
from users.models import Employee

username = 'testuser'  # Замените на свой

user = User.objects.filter(username=username).first()
if not user:
    print(f"✗ Пользователь '{username}' не найден")
else:
    active = Employee.objects.filter(user=user, is_active=True, store__is_active=True).count()
    if active > 0:
        print(f"✓ Логин должен работать для {username}")
        emp = Employee.objects.filter(user=user, is_active=True, store__is_active=True).first()
        print(f"  Магазин: {emp.store.name}")
        print(f"  Tenant key: {emp.store.tenant_key}")
    else:
        print(f"✗ Логин НЕ РАБОТАЕТ для {username}")
        print(f"  Всего Employee: {Employee.objects.filter(user=user).count()}")
        print(f"  Активных Employee: {active}")
```

---

## Проверка через API (альтернатива)

Если не хочешь использовать Django shell, можешь проверить через Admin:

1. Открой http://localhost:8000/admin/
2. Войди как superuser (или создай: `python manage.py createsuperuser`)
3. Перейди в **Users → Employees**
4. Найди своего пользователя
5. Проверь:
   - `is_active` = True ✓
   - `store.is_active` = True ✓

---

## Создание тестового пользователя (если ничего не помогло)

```python
from django.contrib.auth.models import User
from users.models import Store, Employee

# Удаляем старого пользователя (если нужно)
# User.objects.filter(username='testuser').delete()

# Создаём пользователя
user = User.objects.create_user(
    username='testuser',
    password='TestPass123!',
    first_name='Test',
    last_name='User',
    email='test@example.com',
    is_active=True
)

# Создаём магазин
store = Store.objects.create(
    name='Test Store',
    slug='test-store',
    owner=user,
    address='Test Address',
    phone='+998901234567',
    is_active=True
)

# Создаём Employee
employee = Employee.objects.create(
    user=user,
    store=store,
    role='owner',
    position='Владелец',
    phone='+998901234567',
    is_active=True
)

print(f"""
✓ Тестовый пользователь создан!

Username: {user.username}
Password: TestPass123!
Store: {store.name}
Tenant Key: {store.tenant_key}

Теперь можешь войти через:
POST /api/users/auth/login/
{
  "username": "testuser",
  "password": "TestPass123!"
}
""")
```

---

## Резюме

Логин не проходит (401) если:
1. ❌ Неверный username/password
2. ❌ Пользователя не существует
3. ❌ У пользователя нет Employee записи
4. ❌ Employee.is_active = False
5. ❌ Store.is_active = False

Логин проходит если:
- ✅ Пользователь существует
- ✅ Есть хотя бы один активный Employee
- ✅ Магазин Employee активен

После проверки попробуй войти снова!
