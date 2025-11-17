# 🛍️ ERP v2 - Multi-Tenant POS System

Современная мультитенантная POS система с **схемной изоляцией данных** на уровне PostgreSQL и JWT-аутентификацией.

## 🌟 Ключевые особенности

- ✅ **Schema-based мультитенантность** - каждый магазин в отдельной PostgreSQL схеме
- ✅ **X-Tenant-Key header** - простая идентификация магазина без токенов
- ✅ **Один владелец → N магазинов** - гибкое управление несколькими бизнесами
- ✅ **RBAC система** - роли: владелец, менеджер, кассир, складчик
- ✅ **JWT аутентификация** - простые токены без tenant_id
- ✅ **Полная изоляция данных** - на уровне БД через PostgreSQL schemas
- ✅ **DRF + Swagger** - современное REST API с документацией
- ✅ **Готово для мобильных приложений** - простой X-Tenant-Key header

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd new_backend

# Создать виртуальное окружение
python3.13 -m venv venv

# Активировать
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка окружения

Скопируйте `.env.example` в `.env` и настройте:

```bash
cp .env.example .env
```

Для разработки можно использовать SQLite (уже настроено в `.env`).

Для продакшена настройте PostgreSQL:
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=erp_v2_db
DB_USER=postgres
DB_PASSWORD=ваш_пароль
DB_HOST=localhost
DB_PORT=5432
```

### 3. Миграции

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Запуск сервера

```bash
python manage.py runserver
```

Сервер запустится на `http://127.0.0.1:8000/`

---

## 📖 API Документация

- **Swagger UI:** http://127.0.0.1:8000/swagger/
- **ReDoc:** http://127.0.0.1:8000/redoc/

---

## 🔑 Аутентификация

### Регистрация владельца магазина

**Endpoint:** `POST /api/users/auth/register/`

#### Минимальный запрос:
```json
{
  "username": "owner1",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "Иван",
  "store_name": "Мой Магазин"
}
```

#### Полный запрос:
```json
{
  "username": "owner1",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "Иван",
  "last_name": "Иванов",
  "email": "ivan@example.com",
  "owner_phone": "+998901234567",
  "store_name": "Мой Магазин",
  "store_slug": "moy-magazin",
  "store_description": "Магазин одежды премиум класса",
  "store_address": "г. Ташкент, ул. Навои, 25",
  "store_phone": "+998901234567",
  "store_email": "info@mystore.uz"
}
```

#### Ответ:
```json
{
  "status": "success",
  "message": "Регистрация успешна",
  "data": {
    "user": {
      "id": 1,
      "username": "owner1",
      "email": "ivan@example.com",
      "full_name": "Иван Иванов"
    },
    "store": {
      "id": 1,
      "name": "Мой Магазин",
      "slug": "moy-magazin",
      "tenant_key": "moy-magazin_a4b3c2d1",
      "description": "Магазин одежды премиум класса"
    },
    "employee": {
      "role": "owner",
      "role_display": "Владелец",
      "permissions": ["view_all", "create_all", "update_all", "delete_all", ...]
    },
    "tokens": {
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
  }
}
```

**ВАЖНО:** Сохраните `tenant_key` для дальнейших запросов!

### Вход в систему

**Endpoint:** `POST /api/users/auth/login/`

```json
{
  "username": "owner1",
  "password": "SecurePass123!"
}
```

**Ответ:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "owner1",
    "email": "ivan@example.com",
    "full_name": "Иван Иванов"
  },
  "available_stores": [
    {
      "id": 1,
      "name": "Магазин Иванова",
      "slug": "magazin-ivanova",
      "tenant_key": "magazin-ivanova_a4b3c2d1",
      "role": "owner",
      "permissions": ["view_all", "create_all", ...]
    }
  ],
  "default_store": {
    "tenant_key": "magazin-ivanova_a4b3c2d1",
    "name": "Магазин Иванова",
    "role": "owner"
  }
}
```

**ВАЖНО:** Сохраните `tenant_key` для использования в заголовке `X-Tenant-Key`.

### Использование токенов

Для доступа к API добавьте **ДВА заголовка**:

```bash
Authorization: Bearer <ваш_access_token>
X-Tenant-Key: <tenant_key_магазина>
```

Пример запроса:
```bash
curl -X GET http://127.0.0.1:8000/api/users/auth/me/ \
  -H "Authorization: Bearer eyJ0eXAi..." \
  -H "X-Tenant-Key: magazin-ivanova_a4b3c2d1"
```

### Обновление токена

**Endpoint:** `POST /api/users/auth/token/refresh/`

```json
{
  "refresh": "ваш_refresh_token"
}
```

---

## 🏪 Управление магазинами

### Мои магазины

**Endpoint:** `GET /api/users/auth/my-stores/`

Возвращает список всех магазинов с их `tenant_key`.

### Переключение между магазинами

**НЕ требуется новый endpoint!** Просто меняйте значение заголовка `X-Tenant-Key`:

```python
# Магазин 1
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "X-Tenant-Key": "magazin1_a4b3c2d1"
}

# Магазин 2 - просто меняем tenant_key
headers["X-Tenant-Key"] = "magazin2_x7y8z9a0"
```

### Информация о текущем пользователе

**Endpoint:** `GET /api/users/auth/me/`

**Требует:** `X-Tenant-Key` в заголовке

Возвращает информацию о:
- Пользователе
- Текущем магазине (определяется по X-Tenant-Key)
- Роли и правах доступа в этом магазине

---

## 👥 Управление сотрудниками

### Создание сотрудника (Owner/Manager)

**Endpoint:** `POST /api/users/employees/`

**Headers:**
```
Authorization: Bearer <access_token>
X-Tenant-Key: <tenant_key>
```

**Request:**
```json
{
  "username": "cashier1",
  "password": "SecurePass123",
  "first_name": "Петр",
  "last_name": "Петров",
  "email": "petr@example.com",
  "role": "cashier",
  "phone": "+998901234567",
  "position": "Кассир"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Сотрудник успешно создан",
  "data": {
    "employee": {
      "id": 3,
      "full_name": "Петр Петров",
      "username": "cashier1",
      "email": "petr@example.com",
      "role": "cashier",
      "role_display": "Кассир",
      "phone": "+998901234567",
      "position": "Кассир",
      "is_active": true,
      "hired_at": "2025-11-16"
    },
    "credentials": {
      "username": "cashier1",
      "password": "SecurePass123"
    }
  }
}
```

**ВАЖНО:** Пароль возвращается в plaintext только владельцу/менеджеру при создании. Сохраните его для передачи сотруднику!

### Сброс пароля сотрудника (Owner/Manager)

**Endpoint:** `POST /api/users/employees/{id}/reset-password/`

**Request:**
```json
{
  "new_password": "NewSecurePass123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Пароль сотрудника успешно сброшен",
  "data": {
    "username": "cashier1",
    "new_password": "NewSecurePass123"
  }
}
```

### Смена пароля сотрудником (опционально)

**Endpoint:** `POST /api/users/auth/change-password/`

**Request:**
```json
{
  "old_password": "current_password",
  "new_password": "new_password_123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Пароль успешно изменен"
}
```

**Примечание:** Сотрудник НЕ ОБЯЗАН менять пароль. Это опциональная функция для дополнительной безопасности.

---

## 👥 Роли и права доступа

### Owner (Владелец)
- Полный доступ ко всему
- Управление сотрудниками
- Управление настройками магазина
- Просмотр аналитики

**Разрешения:**
```python
['view_all', 'create_all', 'update_all', 'delete_all',
 'manage_employees', 'manage_store', 'view_analytics',
 'manage_products', 'manage_sales', 'manage_customers']
```

### Manager (Менеджер)
- Управление товарами, продажами, клиентами
- Просмотр аналитики
- НЕ может управлять сотрудниками

**Разрешения:**
```python
['view_all', 'create_all', 'update_all',
 'manage_products', 'manage_sales', 'manage_customers',
 'view_analytics']
```

### Cashier (Кассир)
- Создание продаж
- Просмотр товаров
- Работа с клиентами

**Разрешения:**
```python
['view_products', 'create_sales', 'view_customers', 'create_customers']
```

### Stockkeeper (Складчик)
- Управление товарами
- Управление остатками
- Просмотр аналитики по складу

**Разрешения:**
```python
['view_products', 'create_products', 'update_products',
 'manage_inventory', 'view_analytics']
```

---

## 🏗️ Архитектура мультитенантности (Schema-based)

**Архитектура аналогична QRMenu проекту:**

### Как работает

1. **При регистрации:**
   - Создается магазин с уникальным `tenant_key` (например: `magazin-ivanova_a4b3c2d1`)
   - Создается PostgreSQL схема `tenant_{slug}`
   - Все таблицы магазина изолированы в этой схеме

2. **При входе:**
   - JWT токен **НЕ содержит** `store_id`
   - Возвращается список доступных магазинов с их `tenant_key`
   - Клиент выбирает магазин и сохраняет его `tenant_key`

3. **При запросах к API:**
   - Клиент добавляет заголовок: `X-Tenant-Key: magazin-ivanova_a4b3c2d1`
   - `TenantByKeyMiddleware` извлекает `tenant_key` из заголовка
   - Находит магазин в `public.users_store` по `tenant_key`
   - Переключает `search_path` на схему магазина: `SET search_path TO tenant_{slug}, public`
   - Все ORM запросы теперь работают только в схеме этого магазина

4. **Изоляция данных:**
   - **public схема**: хранит User, Store, Employee (общие таблицы)
   - **tenant_* схемы**: хранят Products, Sales, Customers (данные магазина)
   - Полная изоляция на уровне PostgreSQL - магазины не видят данные друг друга

### Переключение между магазинами

**НЕ требуется новый токен!** Просто меняйте `X-Tenant-Key`:

```python
# Работа с магазином 1
headers = {
    "Authorization": f"Bearer {access_token}",
    "X-Tenant-Key": "magazin1_a4b3c2d1"
}
response = requests.get("/api/products/", headers=headers)

# Переключение на магазин 2
headers["X-Tenant-Key"] = "magazin2_x7y8z9a0"
response = requests.get("/api/products/", headers=headers)  # Другие товары!
```

### Преимущества схемной архитектуры

- ✅ **Безопасность**: Полная изоляция данных на уровне БД
- ✅ **Производительность**: Нет лишних WHERE фильтров, PostgreSQL работает только с нужной схемой
- ✅ **Простота для клиента**: Один токен для всех магазинов, легко переключаться
- ✅ **Масштабируемость**: Легко мигрировать отдельные схемы на другие серверы БД
- ✅ **Резервное копирование**: Можно бэкапить схемы магазинов независимо

---

## 📁 Структура проекта

```
new_backend/
├── config/              # Настройки Django
│   ├── settings.py     # Главный конфиг
│   ├── urls.py         # URL routing
│   └── wsgi.py
├── core/               # Ядро системы
│   ├── middleware.py   # TenantMiddleware, DatabaseRoutingMiddleware
│   ├── permissions.py  # Custom permissions для RBAC
│   ├── exceptions.py   # Custom exception handler
│   └── schema_utils.py # Утилиты для PostgreSQL схем
├── users/              # Пользователи и магазины
│   ├── models.py       # Store, Employee
│   ├── serializers.py  # Регистрация, JWT токены
│   ├── views.py        # Auth endpoints
│   ├── urls.py         # URL routing
│   └── admin.py        # Django admin
├── manage.py
├── requirements.txt
├── .env                # Переменные окружения
└── README.md
```

---

## 🔧 Разработка

### Создание нового приложения

```bash
python manage.py startapp inventory
```

### Использование Tenant Context

```python
from core.permissions import IsTenantUser, HasStorePermission

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsTenantUser]

    def get_queryset(self):
        # request.tenant_id автоматически установлен middleware
        return Product.objects.filter(store_id=self.request.tenant_id)
```

### Проверка прав доступа

```python
class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [HasStorePermission]
    required_permissions = ['manage_products']  # Требуемые права
```

---

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest

# С coverage
pytest --cov=. --cov-report=html

# Только для users app
pytest users/tests.py
```

---

## 🚢 Развертывание в продакшене

### 1. PostgreSQL

```bash
# Создание БД
createdb erp_v2_db

# Настройка .env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=erp_v2_db
DB_USER=erp_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
```

### 2. Gunicorn

```bash
# Установка
pip install gunicorn

# Запуск
gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120
```

### 3. Nginx

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/new_backend/staticfiles/;
    }

    location /media/ {
        alias /path/to/new_backend/media/;
    }
}
```

### 4. Celery (фоновые задачи)

```bash
# Worker
celery -A config worker -l info

# Beat (для периодических задач)
celery -A config beat -l info
```

### 5. Redis

```bash
# Установка
brew install redis  # Mac
sudo apt install redis  # Ubuntu

# Запуск
redis-server
```

---

## 📞 API Endpoints

### Аутентификация

| Метод | Endpoint | Описание | Auth | X-Tenant-Key |
|-------|----------|----------|------|--------------|
| POST | `/api/users/auth/register/` | Регистрация владельца (возвращает tenant_key) | ❌ | ❌ |
| POST | `/api/users/auth/login/` | Вход (возвращает available_stores с tenant_key) | ❌ | ❌ |
| POST | `/api/users/auth/token/refresh/` | Обновить access токен | ❌ | ❌ |
| GET | `/api/users/auth/me/` | Информация о текущем пользователе | ✅ | ✅ |
| GET | `/api/users/auth/my-stores/` | Список доступных магазинов | ✅ | ❌ |
| POST | `/api/users/auth/change-password/` | Сменить свой пароль (опционально) | ✅ | ❌ |

### Управление магазинами

| Метод | Endpoint | Описание | Auth | X-Tenant-Key |
|-------|----------|----------|------|--------------|
| GET | `/api/users/stores/` | Список моих магазинов | ✅ | ❌ |
| POST | `/api/users/stores/` | Создать новый магазин | ✅ | ❌ |
| GET | `/api/users/stores/{id}/` | Детали магазина | ✅ | ❌ |
| PUT/PATCH | `/api/users/stores/{id}/` | Обновить магазин | ✅ | ❌ |
| DELETE | `/api/users/stores/{id}/` | Удалить магазин | ✅ | ❌ |

### Управление сотрудниками

| Метод | Endpoint | Описание | Auth | X-Tenant-Key | Роль |
|-------|----------|----------|------|--------------|------|
| GET | `/api/users/employees/` | Список сотрудников магазина | ✅ | ✅ | Owner/Manager |
| POST | `/api/users/employees/` | Создать сотрудника | ✅ | ✅ | Owner/Manager |
| GET | `/api/users/employees/{id}/` | Детали сотрудника | ✅ | ✅ | Owner/Manager |
| PUT/PATCH | `/api/users/employees/{id}/` | Обновить сотрудника | ✅ | ✅ | Owner/Manager |
| DELETE | `/api/users/employees/{id}/` | Удалить сотрудника | ✅ | ✅ | Owner/Manager |
| POST | `/api/users/employees/{id}/reset-password/` | Сбросить пароль сотрудника | ✅ | ✅ | Owner/Manager |

**Примечание:**
- ❌ = не требуется
- ✅ = обязательно
- X-Tenant-Key = заголовок для идентификации магазина

---

## 🐛 Troubleshooting

### Ошибка: "SECRET_KEY must not be empty"
Создайте файл `.env` с `SECRET_KEY`

### Ошибка: "No module named 'core'"
Убедитесь, что `core` добавлен в `INSTALLED_APPS`

### Ошибка при регистрации: "Slug already exists"
Используйте другой `store_slug` или не указывайте его (сгенерируется автоматически)

### PostgreSQL schema не создается
Проверьте настройки БД в `.env` и права пользователя на создание схем

---

## 📚 Технологии

- **Django** 5.1.4
- **Django REST Framework** 3.16.0
- **djangorestframework-simplejwt** 5.5.0 - JWT аутентификация
- **drf-yasg** 1.21.10 - Swagger документация
- **Celery** 5.4.0 - Фоновые задачи
- **Redis** 5.2.1 - Кэширование и очереди
- **PostgreSQL** - База данных (опционально, для продакшена)
- **Pillow** 11.2.1 - Обработка изображений

---

## 🎯 Следующие шаги

1. ✅ **Модуль пользователей** - готов
2. 📦 **Inventory** - управление товарами, категории, остатки
3. 💰 **Sales** - продажи, транзакции, кассовые смены
4. 👥 **Customers** - CRM, программы лояльности
5. 📊 **Analytics** - отчеты, аналитика, дашборды
6. 📱 **Mobile API** - оптимизация для мобильных приложений

---

## 🤝 Вклад в проект

1. Fork проекта
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменений (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

---

**Разработано с ❤️ для ERP v2**
