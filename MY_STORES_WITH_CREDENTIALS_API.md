# 🏪 Получить все магазины с учетными данными - API Guide

## Обзор

Endpoint возвращает список ВСЕХ магазинов, где текущий пользователь является владельцем (owner), вместе с учетными данными staff аккаунта для каждого магазина.

**Особенности:**
- НЕ требует X-Tenant-Key (работает в public схеме)
- Требует только Authorization token
- Возвращает данные по всем магазинам пользователя одним запросом
- Включает staff credentials (username/password) для каждого магазина

---

## 🔗 Эндпоинт

```
GET /api/users/stores/my-stores-with-credentials/
```

---

## 📋 Headers (обязательные)

| Заголовок | Описание | Пример |
|-----------|----------|--------|
| `Authorization` | Bearer токен пользователя | `Bearer eyJhbGc...` |

**⚠️ Примечание:** X-Tenant-Key НЕ требуется! Endpoint работает для всех магазинов пользователя.

---

## 📥 Response Format

### Успешный ответ (200 OK)

```json
{
  "status": "success",
  "data": {
    "count": 2,
    "stores": [
      {
        "id": 2,
        "name": "Тестовый Магазин",
        "slug": "test_shop",
        "tenant_key": "test_shop_4dfa7a5a",
        "schema_name": "tenant_test_shop",
        "description": "Продуктовый магазин",
        "address": "ул. Тестовая, 1",
        "city": "Ташкент",
        "region": "Ташкентская область",
        "phone": "+998901111111",
        "email": "testshop@example.com",
        "legal_name": "ООО Тестовый Магазин",
        "tax_id": "123456789",
        "is_active": true,
        "created_at": "2025-11-19T17:06:04.926370Z",
        "staff_credentials": {
          "username": "test_shop_staff",
          "password": "12345678",
          "full_name": "Сотрудники Тестовый Магазин",
          "is_active": true,
          "note": "Общий аккаунт для всех сотрудников магазина"
        }
      },
      {
        "id": 5,
        "name": "Магазин №2",
        "slug": "shop_2",
        "tenant_key": "shop_2_abc123",
        "schema_name": "tenant_shop_2",
        "description": null,
        "address": "ул. Новая, 10",
        "city": "Самарканд",
        "region": null,
        "phone": "+998902222222",
        "email": null,
        "legal_name": null,
        "tax_id": null,
        "is_active": true,
        "created_at": "2025-11-20T10:30:00Z",
        "staff_credentials": {
          "username": "shop_2_staff",
          "password": "12345678",
          "full_name": "Сотрудники Магазин №2",
          "is_active": true,
          "note": "Общий аккаунт для всех сотрудников магазина"
        }
      }
    ]
  }
}
```

### Успешный ответ - нет магазинов (200 OK)

```json
{
  "status": "success",
  "data": {
    "count": 0,
    "stores": []
  }
}
```

### Staff credentials отсутствуют (200 OK с предупреждением)

Если staff user был удален или не был создан автоматически:

```json
{
  "status": "success",
  "data": {
    "count": 1,
    "stores": [
      {
        "id": 3,
        "name": "Проблемный Магазин",
        "slug": "problem_shop",
        "tenant_key": "problem_shop_xyz789",
        "schema_name": "tenant_problem_shop",
        "address": "ул. Проблемная, 1",
        "is_active": true,
        "created_at": "2025-11-20T12:00:00Z",
        "staff_credentials": null,
        "staff_credentials_missing": true,
        "staff_credentials_note": "Staff аккаунт не найден. Выполните: python manage.py create_staff_users --store problem_shop"
      }
    ]
  }
}
```

---

## 💡 Примеры использования

### 1. cURL - простой запрос

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "http://localhost:8000/api/users/stores/my-stores-with-credentials/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

### 2. JavaScript/TypeScript - функция получения магазинов

```javascript
async function getMyStoresWithCredentials() {
  const token = localStorage.getItem('access_token');

  try {
    const response = await fetch('/api/users/stores/my-stores-with-credentials/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch stores');
    }

    const data = await response.json();

    console.log(`✅ Найдено магазинов: ${data.data.count}`);

    data.data.stores.forEach(store => {
      console.log(`📋 ${store.name}:`);
      console.log(`   Tenant Key: ${store.tenant_key}`);
      console.log(`   Staff Login: ${store.staff_credentials?.username}`);
      console.log(`   Staff Password: ${store.staff_credentials?.password}`);
    });

    return data.data.stores;
  } catch (error) {
    console.error('❌ Ошибка получения магазинов:', error);
    throw error;
  }
}

// Использование
const stores = await getMyStoresWithCredentials();
```

### 3. React Hook - useMyStores

```typescript
import { useState, useEffect } from 'react';
import { api } from './api';

interface StaffCredentials {
  username: string;
  password: string;
  full_name: string;
  is_active: boolean;
  note: string;
}

interface Store {
  id: number;
  name: string;
  slug: string;
  tenant_key: string;
  schema_name: string;
  description: string | null;
  address: string;
  city: string | null;
  region: string | null;
  phone: string;
  email: string | null;
  legal_name: string | null;
  tax_id: string | null;
  is_active: boolean;
  created_at: string;
  staff_credentials: StaffCredentials | null;
  staff_credentials_missing?: boolean;
  staff_credentials_note?: string;
}

export const useMyStores = () => {
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStores = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get('/users/stores/my-stores-with-credentials/');
      setStores(response.data.data.stores);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Ошибка загрузки магазинов');
      console.error('Error fetching stores:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStores();
  }, []);

  return { stores, loading, error, refetch: fetchStores };
};
```

### 4. React компонент - Список магазинов с credentials

```tsx
import { useMyStores } from './hooks/useMyStores';

export const StoreListWithCredentials = () => {
  const { stores, loading, error, refetch } = useMyStores();

  if (loading) {
    return <div>Загрузка магазинов...</div>;
  }

  if (error) {
    return (
      <div className="error">
        <p>Ошибка: {error}</p>
        <button onClick={refetch}>Повторить</button>
      </div>
    );
  }

  if (stores.length === 0) {
    return (
      <div className="empty-state">
        <h3>У вас пока нет магазинов</h3>
        <p>Создайте первый магазин, чтобы начать работу</p>
        <button onClick={() => window.location.href = '/stores/create'}>
          Создать магазин
        </button>
      </div>
    );
  }

  return (
    <div className="stores-list">
      <h2>Мои магазины ({stores.length})</h2>

      {stores.map(store => (
        <div key={store.id} className="store-card">
          <div className="store-header">
            <h3>{store.name}</h3>
            <span className={`status ${store.is_active ? 'active' : 'inactive'}`}>
              {store.is_active ? 'Активен' : 'Неактивен'}
            </span>
          </div>

          <div className="store-info">
            <div className="info-row">
              <label>Адрес:</label>
              <span>{store.address || '—'}</span>
            </div>
            <div className="info-row">
              <label>Телефон:</label>
              <span>{store.phone || '—'}</span>
            </div>
            <div className="info-row">
              <label>Tenant Key:</label>
              <code>{store.tenant_key}</code>
            </div>
          </div>

          <div className="staff-credentials">
            <h4>Учетные данные для сотрудников</h4>

            {store.staff_credentials ? (
              <>
                <div className="credential-row">
                  <label>Логин:</label>
                  <code>{store.staff_credentials.username}</code>
                  <button
                    onClick={() => navigator.clipboard.writeText(store.staff_credentials!.username)}
                  >
                    📋 Копировать
                  </button>
                </div>
                <div className="credential-row">
                  <label>Пароль:</label>
                  <code>{store.staff_credentials.password}</code>
                  <button
                    onClick={() => navigator.clipboard.writeText(store.staff_credentials!.password)}
                  >
                    📋 Копировать
                  </button>
                </div>
                <div className="credential-note">
                  <small>{store.staff_credentials.note}</small>
                </div>
              </>
            ) : (
              <div className="warning">
                <p>⚠️ Staff аккаунт не найден</p>
                {store.staff_credentials_note && (
                  <small>{store.staff_credentials_note}</small>
                )}
              </div>
            )}
          </div>

          <div className="store-actions">
            <button
              onClick={() => {
                localStorage.setItem('current_tenant_key', store.tenant_key);
                window.location.href = `/dashboard?store=${store.slug}`;
              }}
            >
              Открыть магазин
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};
```

### 5. React компонент - Выбор магазина при входе

```tsx
import { useState } from 'react';
import { useMyStores } from './hooks/useMyStores';

export const StoreSelector = ({ onStoreSelect }) => {
  const { stores, loading } = useMyStores();
  const [selectedStore, setSelectedStore] = useState<number | null>(null);

  const handleSelect = (store: Store) => {
    setSelectedStore(store.id);

    // Сохраняем выбранный магазин
    localStorage.setItem('current_tenant_key', store.tenant_key);
    localStorage.setItem('current_store_name', store.name);

    // Уведомляем родительский компонент
    onStoreSelect(store);
  };

  if (loading) {
    return <div>Загрузка...</div>;
  }

  return (
    <div className="store-selector">
      <h2>Выберите магазин</h2>

      <div className="stores-grid">
        {stores.map(store => (
          <div
            key={store.id}
            className={`store-option ${selectedStore === store.id ? 'selected' : ''}`}
            onClick={() => handleSelect(store)}
          >
            <h3>{store.name}</h3>
            <p className="store-address">{store.address}</p>
            <p className="store-city">{store.city}</p>

            <div className="store-meta">
              <span className="created-date">
                Создан: {new Date(store.created_at).toLocaleDateString('ru-RU')}
              </span>
            </div>
          </div>
        ))}
      </div>

      {stores.length === 0 && (
        <div className="no-stores">
          <p>У вас еще нет магазинов</p>
          <button onClick={() => window.location.href = '/stores/create'}>
            Создать первый магазин
          </button>
        </div>
      )}
    </div>
  );
};
```

---

## 🔍 Логика работы

1. **Аутентификация:**
   - Проверяется Bearer token
   - Пользователь должен быть авторизован

2. **Получение магазинов:**
   - Запрос: `Store.objects.filter(owner=request.user, is_active=True)`
   - Сортировка: по дате создания (новые первыми)

3. **Для каждого магазина:**
   - Формируются данные магазина
   - Ищется staff user: `{slug}_staff`
   - Если найден - добавляются credentials
   - Если не найден - возвращается `null` + предупреждение

4. **Ответ:**
   - Количество магазинов (`count`)
   - Массив магазинов со всеми данными

---

## 🎯 Use Cases

### 1. Выбор магазина после входа

```javascript
// После логина показываем список магазинов
async function handlePostLogin() {
  const stores = await getMyStoresWithCredentials();

  if (stores.length === 0) {
    // Нет магазинов - предлагаем создать
    showCreateStoreDialog();
  } else if (stores.length === 1) {
    // Один магазин - автоматически выбираем
    selectStore(stores[0]);
  } else {
    // Несколько магазинов - показываем выбор
    showStoreSelector(stores);
  }
}

function selectStore(store) {
  localStorage.setItem('current_tenant_key', store.tenant_key);
  localStorage.setItem('current_store_name', store.name);

  // Перенаправляем в dashboard
  window.location.href = '/dashboard';
}
```

### 2. Админ-панель владельца сети

```javascript
// Показываем владельцу все его магазины с credentials
async function renderAdminDashboard() {
  const stores = await getMyStoresWithCredentials();

  const dashboard = {
    totalStores: stores.length,
    activeStores: stores.filter(s => s.is_active).length,
    stores: stores.map(store => ({
      name: store.name,
      address: store.address,
      tenant_key: store.tenant_key,
      staff_username: store.staff_credentials?.username,
      staff_password: store.staff_credentials?.password,
      hasMissingCredentials: store.staff_credentials_missing || false
    }))
  };

  return dashboard;
}
```

### 3. Экспорт credentials в PDF/CSV

```javascript
// Генерируем PDF с credentials для всех магазинов
async function exportCredentialsToPDF() {
  const stores = await getMyStoresWithCredentials();

  const data = stores.map(store => ({
    'Магазин': store.name,
    'Адрес': store.address,
    'Tenant Key': store.tenant_key,
    'Staff Username': store.staff_credentials?.username || 'Отсутствует',
    'Staff Password': store.staff_credentials?.password || 'Отсутствует'
  }));

  // Используем библиотеку для генерации PDF
  generatePDF(data, 'Учетные данные магазинов.pdf');
}
```

### 4. Проверка отсутствующих credentials

```javascript
// Находим магазины с отсутствующими credentials
async function checkMissingCredentials() {
  const stores = await getMyStoresWithCredentials();

  const missingCredentials = stores.filter(
    store => store.staff_credentials_missing
  );

  if (missingCredentials.length > 0) {
    console.warn('⚠️ Магазины без staff credentials:');
    missingCredentials.forEach(store => {
      console.log(`  - ${store.name}: ${store.staff_credentials_note}`);
    });

    // Показываем предупреждение пользователю
    showWarning(
      `У ${missingCredentials.length} магазинов отсутствуют staff credentials. ` +
      `Обратитесь к системному администратору.`
    );
  }
}
```

---

## ⚠️ Важные замечания

1. **Только owner:**
   - Endpoint возвращает магазины только где пользователь является владельцем (owner)
   - Сотрудники магазинов не увидят магазины в этом списке

2. **Tenant Key НЕ требуется:**
   - Endpoint работает в public схеме
   - X-Tenant-Key заголовок не нужен
   - Возвращает данные по ВСЕМ магазинам пользователя

3. **Staff Credentials:**
   - Пароль всегда стандартный: `12345678`
   - Username: `{slug}_staff`
   - Если staff user отсутствует - поле будет `null`

4. **Активные магазины:**
   - Возвращаются только активные магазины (`is_active=True`)
   - Неактивные магазины не показываются

5. **Безопасность:**
   - Credentials показываются только владельцу магазина
   - Требуется валидный JWT токен
   - Чувствительная информация - используйте HTTPS

---

## 🔐 Требования

- **Аутентификация:** Bearer token (JWT) владельца магазина
- **НЕ требуется:** X-Tenant-Key
- **Права:** Пользователь должен быть владельцем хотя бы одного магазина

---

## 📝 Связанные эндпоинты

- `POST /api/users/stores/` - Создать новый магазин
- `GET /api/users/stores/` - Список магазинов (без credentials)
- `GET /api/users/stores/staff-credentials/` - Получить credentials одного магазина (требует X-Tenant-Key)
- `POST /api/users/auth/register/` - Регистрация (создает первый магазин)

---

## 🐛 Troubleshooting

### Пустой список магазинов (count: 0)

**Причина:** Пользователь не является владельцем ни одного магазина

**Решение:**
1. Создайте магазин через `POST /api/users/stores/`
2. Или зарегистрируйтесь заново - первый магазин создается автоматически

### staff_credentials: null

**Причина:** Staff user был удален или не был создан

**Решение:**
```bash
# Создать staff users для всех магазинов
python manage.py create_staff_users

# Или для конкретного магазина
python manage.py create_staff_users --store {slug}
```

### 401 Unauthorized

**Причина:** JWT token истек или недействителен

**Решение:**
```bash
# Получите новый токен
curl -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

---

**Дата создания:** 2025-11-20
**Версия API:** 1.0
