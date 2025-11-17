# 🚀 Quick Start - Продолжение разработки

Этот файл поможет быстро продолжить работу над проектом.

---

## 📋 Что уже готово

✅ **Схемная мультитенантность** - работает
✅ **JWT аутентификация** - работает
✅ **Управление сотрудниками** - работает
✅ **RBAC система** - работает
✅ **Middleware** - 3 кастомных middleware
✅ **API документация** - Swagger + ReDoc

---

## 🔥 Запуск проекта

### 1. Активировать виртуальное окружение

```bash
cd /Users/akkanat/Projects/erp_v2/new_backend
source venv/bin/activate  # для macOS/Linux
```

### 2. Запустить сервер

```bash
./venv/bin/python manage.py runserver
```

### 3. Открыть документацию

- Swagger: http://127.0.0.1:8000/swagger/
- ReDoc: http://127.0.0.1:8000/redoc/
- Admin: http://127.0.0.1:8000/admin/

---

## 🧪 Быстрое тестирование

### Регистрация владельца

```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testowner",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123",
    "first_name": "Ivan",
    "last_name": "Ivanov",
    "email": "ivan@example.com",
    "store_name": "Test Store",
    "store_slug": "test-store"
  }'
```

Сохрани из ответа:
- `access` token
- `tenant_key`

### Создание сотрудника

```bash
# Замени ACCESS_TOKEN и TENANT_KEY на свои значения
curl -X POST http://127.0.0.1:8000/api/users/employees/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "X-Tenant-Key: TENANT_KEY" \
  -d '{
    "username": "cashier1",
    "password": "CashierPass123",
    "first_name": "Petr",
    "last_name": "Petrov",
    "role": "cashier",
    "phone": "+998901234567"
  }'
```

### Вход сотрудником

```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cashier1",
    "password": "CashierPass123"
  }'
```

---

## 📁 Структура проекта

```
new_backend/
├── config/              # Django настройки
│   ├── settings.py     # MIDDLEWARE, INSTALLED_APPS
│   └── urls.py         # Главный routing
├── core/
│   ├── middleware.py   # 3 middleware: JWT, Tenant, Employee
│   ├── permissions.py  # RBAC permissions
│   └── schema_utils.py # SchemaManager
├── users/
│   ├── models.py       # Store, Employee
│   ├── views.py        # Auth, Employee, Store views
│   ├── serializers.py  # CreateEmployeeSerializer и др.
│   └── urls.py         # Users routing
├── PROJECT_STATUS.md   # 📊 Полный статус и roadmap
├── CHANGELOG.md        # 📝 История изменений
├── QUICKSTART.md       # 🚀 Этот файл
└── README.md           # 📚 Основная документация
```

---

## 🎯 Следующий шаг: Товары

### 1. Создать app

```bash
./venv/bin/python manage.py startapp products
```

### 2. Добавить в INSTALLED_APPS

```python
# config/settings.py
INSTALLED_APPS = [
    # ...
    'products.apps.ProductsConfig',
]
```

### 3. Создать модели

```python
# products/models.py
from django.db import models

class Category(models.Model):
    """Категория товаров (в tenant схеме!)"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'products_category'
        verbose_name = 'Категория'

class Product(models.Model):
    """Товар (в tenant схеме!)"""
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    # Цены
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Остаток
    quantity = models.IntegerField(default=0)
    min_quantity = models.IntegerField(default=0)

    # Изображение
    image = models.ImageField(upload_to='products/', blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products_product'
        verbose_name = 'Товар'
```

### 4. Создать сериализаторы

```python
# products/serializers.py
from rest_framework import serializers
from products.models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
```

### 5. Создать views

```python
# products/views.py
from rest_framework import viewsets
from products.models import Product, Category
from products.serializers import ProductSerializer, CategorySerializer
from core.permissions import IsTenantUser, HasStorePermission

class ProductViewSet(viewsets.ModelViewSet):
    """Управление товарами"""
    serializer_class = ProductSerializer
    permission_classes = [IsTenantUser]

    def get_queryset(self):
        # Автоматически в tenant схеме!
        return Product.objects.select_related('category').all()

class CategoryViewSet(viewsets.ModelViewSet):
    """Управление категориями"""
    serializer_class = CategorySerializer
    permission_classes = [IsTenantUser]

    def get_queryset(self):
        return Category.objects.all()
```

### 6. Создать URLs

```python
# products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.views import ProductViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')

app_name = 'products'

urlpatterns = [
    path('', include(router.urls)),
]
```

### 7. Добавить в main urls

```python
# config/urls.py
urlpatterns = [
    # ...
    path('api/', include('products.urls')),
]
```

### 8. Создать миграции

```bash
./venv/bin/python manage.py makemigrations products
./venv/bin/python manage.py migrate
```

**ВАЖНО:** Для production с PostgreSQL нужно будет мигрировать все tenant схемы!

### 9. Тестировать

```bash
# Получить список товаров
curl -X GET http://127.0.0.1:8000/api/products/ \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "X-Tenant-Key: TENANT_KEY"

# Создать товар
curl -X POST http://127.0.0.1:8000/api/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "X-Tenant-Key: TENANT_KEY" \
  -d '{
    "name": "Товар 1",
    "sku": "PROD001",
    "cost_price": "100.00",
    "sale_price": "150.00",
    "quantity": 50
  }'
```

---

## 🔧 Полезные команды

### Django

```bash
# Создать миграции
./venv/bin/python manage.py makemigrations

# Применить миграции
./venv/bin/python manage.py migrate

# Создать суперпользователя
./venv/bin/python manage.py createsuperuser

# Django shell
./venv/bin/python manage.py shell

# Проверить проект
./venv/bin/python manage.py check
```

### База данных (SQLite)

```bash
# Открыть SQLite shell
sqlite3 db.sqlite3

# Посмотреть таблицы
.tables

# Посмотреть структуру таблицы
.schema users_store

# Выход
.quit
```

### PostgreSQL (production)

```bash
# Открыть psql
psql erp_v2_db

# Список схем
\dn

# Переключиться на схему
SET search_path TO tenant_test_store;

# Список таблиц
\dt

# Выход
\q
```

---

## 🐛 Частые проблемы

### 1. "employee": null в /api/users/auth/me/

**Причина:** JWTAuthenticationMiddleware не в MIDDLEWARE

**Решение:** Проверь config/settings.py:
```python
MIDDLEWARE = [
    # ...
    'core.middleware.JWTAuthenticationMiddleware',  # ДОЛЖЕН БЫТЬ!
    'core.middleware.TenantByKeyMiddleware',
    'core.middleware.LoadEmployeeContextMiddleware',
]
```

### 2. "Missing X-Tenant-Key header"

**Причина:** Забыл добавить заголовок

**Решение:** Всегда добавляй оба заголовка:
```
Authorization: Bearer <token>
X-Tenant-Key: <tenant_key>
```

### 3. "Вы не имеете доступа к данному магазину"

**Причина:** У пользователя нет Employee записи для этого магазина

**Решение:** Проверь что employee создан для нужного магазина

---

## 📚 Документация

- **PROJECT_STATUS.md** - полный статус, roadmap, что делать дальше
- **README.md** - основная документация проекта
- **API_EXAMPLES.md** - примеры API запросов на разных языках
- **CHANGELOG.md** - история изменений

---

## 🎯 Roadmap (кратко)

1. ✅ Мультитенантность
2. ✅ Аутентификация
3. ✅ Сотрудники
4. 🔲 **Товары** ← СЛЕДУЮЩЕЕ
5. 🔲 Продажи
6. 🔲 Клиенты
7. 🔲 Отчёты
8. 🔲 Mobile App

Подробный roadmap в [PROJECT_STATUS.md](PROJECT_STATUS.md)

---

**Готов продолжать? Начни с создания `products` app! 🚀**
