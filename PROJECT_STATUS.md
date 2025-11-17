# 🚀 ERP v2 - Статус проекта

**Дата последнего обновления:** 16 ноября 2025
**Версия:** 1.0.0 (MVP)

---

## ✅ Что уже реализовано

### 1. 🏗️ Схемная мультитенантность (Schema-based Multitenancy)

**Архитектура аналогична QRMenu проекту:**

- ✅ PostgreSQL схемы для изоляции данных магазинов
- ✅ `TenantByKeyMiddleware` - переключение схем по `X-Tenant-Key` header
- ✅ `public` схема для User, Store, Employee
- ✅ `tenant_{slug}` схемы для данных магазинов
- ✅ Автоматическое создание схем при регистрации магазина
- ✅ Полная изоляция данных на уровне PostgreSQL

**Файлы:**
- `core/middleware.py` - TenantByKeyMiddleware, JWTAuthenticationMiddleware, LoadEmployeeContextMiddleware
- `core/schema_utils.py` - SchemaManager для создания/удаления схем
- `users/models.py` - Store.tenant_key (уникальный ключ магазина)

### 2. 🔐 Аутентификация и авторизация

**JWT аутентификация без store_id в токене:**

- ✅ Регистрация владельца магазина (User + Store + Employee)
- ✅ Вход в систему (возвращает available_stores с tenant_key)
- ✅ JWT токены (refresh + access)
- ✅ X-Tenant-Key header для идентификации магазина
- ✅ JWTAuthenticationMiddleware для ранней аутентификации
- ✅ Обновление токенов

**Endpoints:**
- `POST /api/users/auth/register/` - регистрация
- `POST /api/users/auth/login/` - вход
- `POST /api/users/auth/token/refresh/` - обновление токена
- `GET /api/users/auth/me/` - информация о текущем пользователе
- `GET /api/users/auth/my-stores/` - список доступных магазинов
- `POST /api/users/auth/change-password/` - смена пароля (опционально)

**Файлы:**
- `users/views.py` - RegisterView, CustomTokenObtainPairView, me, my_stores, change_password
- `users/serializers.py` - UserRegistrationSerializer, CustomTokenObtainPairSerializer
- `core/middleware.py` - JWTAuthenticationMiddleware

### 3. 👥 Управление сотрудниками

**Создание и управление сотрудниками владельцем/менеджером:**

- ✅ Создание сотрудника (User + Employee) владельцем/менеджером
- ✅ Пароль возвращается в plaintext для владельца
- ✅ Сброс пароля сотрудника владельцем/менеджером
- ✅ Смена пароля сотрудником (опционально, не обязательно)
- ✅ Просмотр списка сотрудников
- ✅ Обновление данных сотрудника
- ✅ Удаление/деактивация сотрудника

**Endpoints:**
- `GET /api/users/employees/` - список сотрудников
- `POST /api/users/employees/` - создать сотрудника
- `GET /api/users/employees/{id}/` - детали сотрудника
- `PUT/PATCH /api/users/employees/{id}/` - обновить сотрудника
- `DELETE /api/users/employees/{id}/` - удалить сотрудника
- `POST /api/users/employees/{id}/reset-password/` - сбросить пароль

**Файлы:**
- `users/views.py` - EmployeeViewSet (create, reset_password)
- `users/serializers.py` - CreateEmployeeSerializer, EmployeeSerializer

### 4. 🛡️ RBAC система (Role-Based Access Control)

**4 роли с разными правами:**

- ✅ **Owner (владелец)** - полный доступ
- ✅ **Manager (менеджер)** - управление без удаления магазина
- ✅ **Cashier (кассир)** - работа с продажами и клиентами
- ✅ **Stockkeeper (складчик)** - управление товарами и складом

**Permissions:**
- ✅ `IsTenantUser` - проверка доступа к магазину
- ✅ `HasStorePermission` - проверка конкретных прав
- ✅ `IsOwnerOrManager` - только owner/manager
- ✅ `IsOwner` - только owner
- ✅ `CanManageEmployees` - управление сотрудниками
- ✅ `ReadOnly` - только чтение

**Файлы:**
- `core/permissions.py` - все permission классы
- `users/models.py` - Employee.Role, Employee.permissions

### 5. 🏪 Управление магазинами

**Store модель с мультитенантностью:**

- ✅ Создание магазина (автоматически при регистрации)
- ✅ Генерация tenant_key (slug_hash формат)
- ✅ Генерация schema_name (tenant_{slug})
- ✅ Автоматическое создание PostgreSQL схемы
- ✅ Просмотр списка своих магазинов
- ✅ Обновление информации о магазине

**Endpoints:**
- `GET /api/users/stores/` - мои магазины
- `POST /api/users/stores/` - создать магазин
- `GET /api/users/stores/{id}/` - детали магазина
- `PUT/PATCH /api/users/stores/{id}/` - обновить магазин
- `DELETE /api/users/stores/{id}/` - удалить магазин

**Файлы:**
- `users/models.py` - Store модель
- `users/views.py` - StoreViewSet
- `users/serializers.py` - StoreSerializer

### 6. 📚 Документация API

- ✅ Swagger UI доступен на `/swagger/`
- ✅ ReDoc доступен на `/redoc/`
- ✅ OpenAPI schema на `/swagger.json`
- ✅ Полная документация всех endpoints
- ✅ Примеры запросов и ответов

### 7. 🗄️ Модели базы данных

**Public схема (общие таблицы):**
- ✅ `auth_user` - Django User
- ✅ `users_store` - магазины (с tenant_key)
- ✅ `users_employee` - сотрудники (связь User + Store + роль)

**Tenant схемы (данные магазина):**
- 🔲 Products (товары) - **TODO**
- 🔲 Categories (категории) - **TODO**
- 🔲 Sales (продажи) - **TODO**
- 🔲 Customers (клиенты) - **TODO**
- 🔲 Inventory (инвентарь) - **TODO**

### 8. 🔧 Middleware

**3 кастомных middleware в правильном порядке:**

1. ✅ `JWTAuthenticationMiddleware` - JWT аутентификация
2. ✅ `TenantByKeyMiddleware` - переключение схем
3. ✅ `LoadEmployeeContextMiddleware` - загрузка контекста сотрудника

**Файлы:**
- `core/middleware.py`
- `config/settings.py` - MIDDLEWARE

### 9. 📦 Зависимости и конфигурация

- ✅ Django 5.1.4
- ✅ Django REST Framework 3.16.0
- ✅ djangorestframework-simplejwt 5.4.0
- ✅ drf-yasg (Swagger)
- ✅ django-cors-headers
- ✅ psycopg2-binary
- ✅ python-dotenv
- ✅ Pillow

**Файлы:**
- `requirements.txt`
- `config/settings.py`
- `.env` (SECRET_KEY, DATABASE_URL)

---

## 🔲 Что нужно сделать дальше

### Приоритет 1: Основной функционал

#### 1.1 Товары и категории (Products & Categories)

**Модели:**
```python
# products/models.py (в tenant схеме!)

class Category(models.Model):
    """Категория товаров (в tenant схеме)"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Метаданные для упорядочивания
    order = models.IntegerField(default=0)

class Product(models.Model):
    """Товар (в tenant схеме)"""
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True)  # Артикул
    barcode = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)

    # Цены
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)  # Себестоимость
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена продажи

    # Количество
    quantity = models.IntegerField(default=0)
    min_quantity = models.IntegerField(default=0)  # Минимальный остаток

    # Изображение
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    # Метаданные
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Endpoints:**
- `GET /api/products/` - список товаров (с фильтрами и поиском)
- `POST /api/products/` - создать товар
- `GET /api/products/{id}/` - детали товара
- `PUT/PATCH /api/products/{id}/` - обновить товар
- `DELETE /api/products/{id}/` - удалить товар
- `GET /api/categories/` - список категорий
- `POST /api/categories/` - создать категорию

**Permissions:**
- Owner, Manager, Stockkeeper - полный доступ
- Cashier - только просмотр

#### 1.2 Продажи (Sales)

**Модели:**
```python
# sales/models.py (в tenant схеме!)

class Sale(models.Model):
    """Продажа"""
    sale_number = models.CharField(max_length=50, unique=True)  # Номер чека
    customer = models.ForeignKey('Customer', null=True, blank=True, on_delete=models.SET_NULL)
    cashier = models.ForeignKey('users.Employee', on_delete=models.PROTECT)

    # Суммы
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)  # Подитог
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)  # Итого

    # Оплата
    PAYMENT_METHODS = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
        ('transfer', 'Перевод'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Статус
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('completed', 'Завершена'),
        ('refunded', 'Возврат'),
        ('cancelled', 'Отменена'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

class SaleItem(models.Model):
    """Позиция в продаже"""
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена на момент продажи
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
```

**Endpoints:**
- `POST /api/sales/` - создать продажу (кассир)
- `GET /api/sales/` - список продаж (с фильтрами по дате, кассиру)
- `GET /api/sales/{id}/` - детали продажи
- `POST /api/sales/{id}/refund/` - возврат продажи
- `GET /api/sales/stats/` - статистика продаж

**Permissions:**
- Owner, Manager - полный доступ + статистика
- Cashier - создание продаж, просмотр своих продаж

#### 1.3 Клиенты (Customers)

**Модель:**
```python
# customers/models.py (в tenant схеме!)

class Customer(models.Model):
    """Клиент (в tenant схеме)"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=13)  # +998XXXXXXXXX
    email = models.EmailField(blank=True)

    # Программа лояльности
    loyalty_points = models.IntegerField(default=0)
    discount_percent = models.IntegerField(default=0)

    # Статистика
    total_purchases = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_sales_count = models.IntegerField(default=0)

    # Метаданные
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
```

**Endpoints:**
- `GET /api/customers/` - список клиентов
- `POST /api/customers/` - создать клиента
- `GET /api/customers/{id}/` - детали клиента
- `PUT/PATCH /api/customers/{id}/` - обновить клиента
- `GET /api/customers/{id}/sales/` - продажи клиента

### Приоритет 2: Дополнительный функционал

#### 2.1 Отчёты и аналитика

**Endpoints:**
- `GET /api/reports/sales/` - отчёт по продажам (день/неделя/месяц)
- `GET /api/reports/products/` - отчёт по товарам (популярные/неликвид)
- `GET /api/reports/cashiers/` - отчёт по кассирам
- `GET /api/reports/profit/` - отчёт по прибыли

**Permissions:**
- Owner, Manager - полный доступ

#### 2.2 Инвентаризация

**Endpoints:**
- `POST /api/inventory/check/` - начать инвентаризацию
- `PUT /api/inventory/check/{id}/` - обновить результаты
- `POST /api/inventory/check/{id}/complete/` - завершить инвентаризацию

#### 2.3 Поставщики

**Модель:**
```python
class Supplier(models.Model):
    """Поставщик"""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=13)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
```

#### 2.4 Закупки

**Модель:**
```python
class Purchase(models.Model):
    """Закупка товара"""
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Приоритет 3: Frontend интеграция

#### 3.1 Примеры клиентского кода

**Python:**
```python
# examples/python_client.py
class ERPClient:
    def __init__(self, base_url, access_token, tenant_key):
        self.base_url = base_url
        self.access_token = access_token
        self.tenant_key = tenant_key

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Tenant-Key": self.tenant_key
        }

    def get_products(self):
        return requests.get(
            f"{self.base_url}/api/products/",
            headers=self._headers()
        ).json()
```

**React/TypeScript:**
```typescript
// examples/react_client.ts
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'X-Tenant-Key': tenantKey
  }
});
```

#### 3.2 WebSocket для реального времени (опционально)

- Django Channels
- Real-time обновления продаж
- Уведомления о низких остатках

---

## 🚀 Как продолжить разработку

### 1. Создать новое Django app для товаров

```bash
./venv/bin/python manage.py startapp products
```

**Добавить в `INSTALLED_APPS`:**
```python
INSTALLED_APPS = [
    # ...
    'products.apps.ProductsConfig',
]
```

### 2. Создать модели в products/models.py

```python
from django.db import models

class Category(models.Model):
    # ... (см. выше)

    class Meta:
        db_table = 'products_category'  # Будет в tenant схеме!
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

class Product(models.Model):
    # ... (см. выше)

    class Meta:
        db_table = 'products_product'  # Будет в tenant схеме!
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
```

### 3. Создать миграции

```bash
./venv/bin/python manage.py makemigrations products
```

**ВАЖНО:** Миграции нужно применить ко ВСЕМ схемам:

```python
# core/management/commands/migrate_all_schemas.py
from django.core.management.base import BaseCommand
from users.models import Store
from core.schema_utils import SchemaManager

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Мигрируем public
        call_command('migrate')

        # Мигрируем все tenant схемы
        for store in Store.objects.filter(is_active=True):
            SchemaManager.migrate_schema(store.schema_name)
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
    serializer_class = ProductSerializer
    permission_classes = [IsTenantUser]

    def get_queryset(self):
        # Запрос уже в tenant схеме благодаря middleware!
        return Product.objects.all()
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

### 7. Добавить в main urls.py

```python
# config/urls.py
urlpatterns = [
    # ...
    path('api/products/', include('products.urls')),
]
```

---

## 🔍 Важные моменты

### Tenant-aware модели

**Все модели для данных магазина должны быть в tenant схеме:**
- Products, Categories, Sales, Customers, Inventory

**В public схеме только:**
- User, Store, Employee (общие для всех)

### Миграции

**Для tenant моделей:**
```bash
# 1. Создать миграции
./venv/bin/python manage.py makemigrations products

# 2. Применить к public (создаст файлы миграций)
./venv/bin/python manage.py migrate products

# 3. Применить ко всем tenant схемам
./venv/bin/python manage.py migrate_all_schemas
```

### Permissions

**Проверяйте права доступа в views:**
```python
permission_classes = [IsTenantUser, HasStorePermission]
required_permissions = ['manage_products']
```

### Тестирование

**Всегда тестируйте с X-Tenant-Key:**
```bash
curl -X GET http://127.0.0.1:8000/api/products/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-Key: YOUR_TENANT_KEY"
```

---

## 📝 Полезные команды

```bash
# Запуск сервера
./venv/bin/python manage.py runserver

# Создать миграции
./venv/bin/python manage.py makemigrations

# Применить миграции
./venv/bin/python manage.py migrate

# Создать суперпользователя
./venv/bin/python manage.py createsuperuser

# Собрать статику
./venv/bin/python manage.py collectstatic

# Django shell
./venv/bin/python manage.py shell

# Проверить схему БД
./venv/bin/python manage.py dbshell
# \dn - список схем
# \dt - список таблиц
# SET search_path TO tenant_magazin1; - переключиться на схему
```

---

## 📚 Документация

- **Swagger UI:** http://127.0.0.1:8000/swagger/
- **ReDoc:** http://127.0.0.1:8000/redoc/
- **Admin:** http://127.0.0.1:8000/admin/

---

## 🐛 Известные проблемы

### 1. Employee не загружается

**Проблема:** `request.employee = None` в LoadEmployeeContextMiddleware

**Решение:** Добавлен JWTAuthenticationMiddleware ПЕРЕД LoadEmployeeContextMiddleware

### 2. tenant_id vs tenant

**Проблема:** Старый код использовал `request.tenant_id`

**Решение:** Обновлены permissions для использования `request.tenant`

---

## 🎯 Roadmap

- [x] Базовая мультитенантность
- [x] Аутентификация JWT
- [x] Управление сотрудниками
- [x] RBAC система
- [ ] Товары и категории
- [ ] Продажи
- [ ] Клиенты
- [ ] Отчёты
- [ ] Инвентаризация
- [ ] Поставщики и закупки
- [ ] Mobile App (React Native)
- [ ] Desktop App (Electron)
- [ ] WebSocket real-time
- [ ] Печать чеков
- [ ] Интеграция с кассой
- [ ] Backup и restore

---

## 👨‍💻 Для разработчика

**Текущие файлы проекта:**

```
new_backend/
├── config/
│   ├── settings.py          # Настройки (MIDDLEWARE, INSTALLED_APPS)
│   ├── urls.py              # Главный URL конфиг
│   └── wsgi.py
├── core/
│   ├── middleware.py        # 3 middleware (JWT, Tenant, Employee)
│   ├── permissions.py       # RBAC permissions
│   ├── schema_utils.py      # SchemaManager
│   └── exceptions.py        # Custom exceptions
├── users/
│   ├── models.py            # User, Store, Employee
│   ├── views.py             # Auth + Employee + Store views
│   ├── serializers.py       # Все сериализаторы
│   ├── urls.py              # URLs для users app
│   └── signals.py           # Post-save signals
├── db.sqlite3               # SQLite БД (для разработки)
├── requirements.txt         # Зависимости
├── .env                     # SECRET_KEY, DATABASE_URL
├── README.md                # Основная документация
├── API_EXAMPLES.md          # Примеры API запросов
└── PROJECT_STATUS.md        # Этот файл
```

**Следующий шаг:** Создать `products` app и реализовать товары + категории.

---

**Удачи в разработке! 🚀**
