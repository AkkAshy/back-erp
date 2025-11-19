# 🔐 Получение учетных данных общего staff аккаунта

## Обзор

Эндпоинт для получения логина и пароля общего аккаунта сотрудников магазина. Доступен только владельцу магазина.

---

## 🔗 Эндпоинт

```
GET /api/users/stores/staff-credentials/
```

**Магазин определяется автоматически из заголовка `X-Tenant-Key`**

---

## 📋 Headers (обязательные)

| Заголовок | Описание | Пример |
|-----------|----------|--------|
| `Authorization` | Bearer токен владельца | `Bearer eyJhbGc...` |
| `X-Tenant-Key` | Ключ магазина | `test_shop_4dfa7a5a` |

---

## 📤 Response Format

### Успешный ответ (200 OK)

```json
{
  "status": "success",
  "data": {
    "username": "test_shop_staff",
    "password": "12345678",
    "full_name": "Сотрудники Тестовый Магазин",
    "is_active": true,
    "store_name": "Тестовый Магазин",
    "tenant_key": "test_shop_4dfa7a5a",
    "note": "Общий аккаунт для всех сотрудников магазина. Используйте его для входа кассиров."
  }
}
```

### Ошибка: не владелец (403 Forbidden)

```json
{
  "status": "error",
  "code": "forbidden",
  "message": "Только владелец магазина может просматривать учетные данные"
}
```

### Ошибка: аккаунт не найден (404 Not Found)

```json
{
  "status": "error",
  "code": "not_found",
  "message": "Общий аккаунт для магазина \"Тестовый Магазин\" не найден. Возможно, он был удален."
}
```

---

## 📊 Поля Response

| Поле | Тип | Описание |
|------|-----|----------|
| `username` | string | Логин общего аккаунта (формат: `{slug}_staff`) |
| `password` | string | Пароль (по умолчанию: `12345678`) |
| `full_name` | string | Полное имя аккаунта |
| `is_active` | boolean | Активен ли аккаунт |
| `store_name` | string | Название магазина |
| `tenant_key` | string | Ключ магазина (тот же что в X-Tenant-Key) |
| `note` | string | Подсказка по использованию |

---

## 💡 Примеры использования

### 1. Получить учетные данные для своего магазина

```bash
curl -X GET "http://localhost:8000/api/users/stores/staff-credentials/" \
  -H "Authorization: Bearer $OWNER_TOKEN" \
  -H "X-Tenant-Key: test_shop_4dfa7a5a"
```

**Ответ:**
```json
{
  "status": "success",
  "data": {
    "username": "test_shop_staff",
    "password": "12345678",
    "full_name": "Сотрудники Тестовый Магазин",
    "is_active": true,
    "store_name": "Тестовый Магазин",
    "tenant_key": "test_shop_4dfa7a5a",
    "note": "Общий аккаунт для всех сотрудников магазина. Используйте его для входа кассиров."
  }
}
```

### 2. JavaScript пример

```javascript
async function getStaffCredentials() {
  try {
    // Магазин определяется автоматически из X-Tenant-Key заголовка
    const response = await api.get('/users/stores/staff-credentials/');

    const { username, password, store_name, tenant_key, note } = response.data.data;

    console.log('Учетные данные для сотрудников:');
    console.log(`Логин: ${username}`);
    console.log(`Пароль: ${password}`);
    console.log(`Примечание: ${note}`);

    return response.data.data;
  } catch (error) {
    if (error.response?.status === 403) {
      console.error('Доступ запрещен: только владелец может просматривать учетные данные');
    } else if (error.response?.status === 404) {
      console.error('Общий аккаунт не найден');
    }
    throw error;
  }
}

// Использование (без параметров!)
const credentials = await getStaffCredentials();
```

### 3. React компонент - Отображение учетных данных

```jsx
import { useState, useEffect } from 'react';
import { api } from './api';

function StaffCredentials() {
  const [credentials, setCredentials] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState({ username: false, password: false });

  useEffect(() => {
    async function loadCredentials() {
      try {
        // Магазин определяется автоматически из X-Tenant-Key
        const response = await api.get('/users/stores/staff-credentials/');
        setCredentials(response.data.data);
      } catch (err) {
        setError(err.response?.data?.message || 'Ошибка загрузки');
      } finally {
        setLoading(false);
      }
    }
    loadCredentials();
  }, []);

  const copyToClipboard = async (text, field) => {
    await navigator.clipboard.writeText(text);
    setCopied({ ...copied, [field]: true });
    setTimeout(() => setCopied({ ...copied, [field]: false }), 2000);
  };

  if (loading) return <div>Загрузка...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!credentials) return null;

  return (
    <div className="staff-credentials">
      <h3>🔐 Учетные данные общего аккаунта</h3>

      <div className="credential-item">
        <label>Логин:</label>
        <div className="credential-value">
          <code>{credentials.username}</code>
          <button onClick={() => copyToClipboard(credentials.username, 'username')}>
            {copied.username ? '✓ Скопировано' : '📋 Копировать'}
          </button>
        </div>
      </div>

      <div className="credential-item">
        <label>Пароль:</label>
        <div className="credential-value">
          <code>{credentials.password}</code>
          <button onClick={() => copyToClipboard(credentials.password, 'password')}>
            {copied.password ? '✓ Скопировано' : '📋 Копировать'}
          </button>
        </div>
      </div>

      <div className="credential-note">
        <p><strong>Имя:</strong> {credentials.full_name}</p>
        <p><strong>Статус:</strong> {credentials.is_active ? '✅ Активен' : '❌ Неактивен'}</p>
        <p className="note-text">ℹ️ {credentials.note}</p>
      </div>

      <div className="warning">
        ⚠️ <strong>Важно:</strong> Эти учетные данные предназначены для всех кассиров и сотрудников.
        Не изменяйте пароль без уведомления персонала!
      </div>
    </div>
  );
}
```

### 4. Vue компонент

```vue
<template>
  <div class="staff-credentials" v-if="credentials">
    <h3>🔐 Учетные данные общего аккаунта</h3>

    <div class="credentials-box">
      <div class="credential-row">
        <span class="label">Логин:</span>
        <div class="value-group">
          <code>{{ credentials.username }}</code>
          <button @click="copy(credentials.username, 'username')" class="copy-btn">
            {{ copied.username ? '✓' : '📋' }}
          </button>
        </div>
      </div>

      <div class="credential-row">
        <span class="label">Пароль:</span>
        <div class="value-group">
          <code>{{ credentials.password }}</code>
          <button @click="copy(credentials.password, 'password')" class="copy-btn">
            {{ copied.password ? '✓' : '📋' }}
          </button>
        </div>
      </div>

      <div class="info">
        <p><strong>Имя:</strong> {{ credentials.full_name }}</p>
        <p><strong>Статус:</strong>
          <span :class="credentials.is_active ? 'active' : 'inactive'">
            {{ credentials.is_active ? 'Активен' : 'Неактивен' }}
          </span>
        </p>
      </div>

      <div class="note">
        {{ credentials.note }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    storeId: {
      type: Number,
      required: true
    }
  },

  data() {
    return {
      credentials: null,
      copied: {
        username: false,
        password: false
      }
    };
  },

  async mounted() {
    await this.loadCredentials();
  },

  methods: {
    async loadCredentials() {
      try {
        const response = await this.$api.get(`/users/stores/${this.storeId}/staff-credentials/`);
        this.credentials = response.data.data;
      } catch (error) {
        if (error.response?.status === 403) {
          this.$toast.error('Только владелец может просматривать учетные данные');
        } else {
          this.$toast.error('Ошибка загрузки учетных данных');
        }
      }
    },

    async copy(text, field) {
      try {
        await navigator.clipboard.writeText(text);
        this.copied[field] = true;
        setTimeout(() => {
          this.copied[field] = false;
        }, 2000);
      } catch (error) {
        console.error('Failed to copy:', error);
      }
    }
  }
};
</script>

<style scoped>
.staff-credentials {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
}

.credentials-box {
  background: white;
  border-radius: 6px;
  padding: 15px;
  border: 1px solid #dee2e6;
}

.credential-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #e9ecef;
}

.value-group {
  display: flex;
  gap: 10px;
  align-items: center;
}

code {
  background: #e9ecef;
  padding: 5px 10px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}

.copy-btn {
  padding: 5px 10px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.copy-btn:hover {
  background: #0056b3;
}

.note {
  margin-top: 15px;
  padding: 10px;
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  border-radius: 4px;
}

.active {
  color: #28a745;
}

.inactive {
  color: #dc3545;
}
</style>
```

---

## 🔍 Логика работы

1. **Проверка владельца:**
   - Эндпоинт доступен только владельцу магазина (`store.owner == request.user`)
   - Другие сотрудники получат ошибку 403

2. **Формат username:**
   - Автоматически формируется как `{store.slug}_staff`
   - Например: `test_shop_staff`, `my_store_staff`

3. **Стандартный пароль:**
   - По умолчанию: `12345678`
   - ⚠️ В будущем может быть добавлена возможность изменения

4. **Автоматическое создание:**
   - Аккаунт создается автоматически при создании магазина (post_save signal)
   - Если аккаунт был удален вручную, эндпоинт вернет 404

---

## ⚠️ Важные замечания

1. **Безопасность:**
   - Учетные данные видны ТОЛЬКО владельцу магазина
   - Не передавайте эти данные третьим лицам
   - Используйте HTTPS в production

2. **Общий аккаунт:**
   - Этот аккаунт используется ВСЕМИ кассирами и сотрудниками
   - Каждый кассир выбирает себя из списка при создании продажи
   - Не изменяйте пароль без уведомления всего персонала

3. **Изменение пароля:**
   - В текущей версии пароль жестко закодирован (`12345678`)
   - Для изменения пароля используйте стандартный функционал Django Admin
   - После изменения пароля сообщите всем сотрудникам

4. **Формат аккаунта:**
   - Username: `{slug}_staff`
   - Password: `12345678` (стандартный)
   - Role: `STAFF`
   - Не имеет связи с конкретным Employee

---

## 🔐 Требования

- **Аутентификация:** Bearer token (JWT)
- **Заголовок:** `X-Tenant-Key` с ключом магазина
- **Права:** Только владелец магазина (`store.owner`)

---

## 🎯 Use Cases

### Для владельца
- Получить учетные данные для передачи новым сотрудникам
- Проверить актуальность учетных данных
- Убедиться что аккаунт активен

### Для фронтенда
- Отображение учетных данных в настройках магазина
- Кнопка "Копировать" для удобства
- Печать инструкции для сотрудников
- QR-код с учетными данными

---

## 📱 Интеграция с UI

### Генерация QR-кода

```javascript
import QRCode from 'qrcode';

async function generateStaffQR(storeId) {
  const response = await api.get(`/users/stores/${storeId}/staff-credentials/`);
  const { username, password } = response.data.data;

  const text = `Учетные данные магазина\nЛогин: ${username}\nПароль: ${password}`;

  const qrCodeUrl = await QRCode.toDataURL(text);
  return qrCodeUrl;
}
```

### Печать инструкции

```javascript
function printStaffInstructions(credentials) {
  const printWindow = window.open('', '', 'width=600,height=400');

  printWindow.document.write(`
    <html>
      <head>
        <title>Инструкция для сотрудников</title>
        <style>
          body { font-family: Arial; padding: 20px; }
          .box { border: 2px solid #000; padding: 15px; margin: 20px 0; }
          code { background: #f0f0f0; padding: 5px; }
        </style>
      </head>
      <body>
        <h1>Инструкция для входа в систему</h1>

        <div class="box">
          <h2>Учетные данные:</h2>
          <p><strong>Логин:</strong> <code>${credentials.username}</code></p>
          <p><strong>Пароль:</strong> <code>${credentials.password}</code></p>
        </div>

        <div class="box">
          <h2>Порядок работы:</h2>
          <ol>
            <li>Откройте сайт POS-системы</li>
            <li>Введите логин и пароль выше</li>
            <li>Выберите свое имя из списка кассиров</li>
            <li>Откройте смену (если еще не открыта)</li>
            <li>Начните работу</li>
          </ol>
        </div>

        <p><em>Примечание: ${credentials.note}</em></p>
      </body>
    </html>
  `);

  printWindow.document.close();
  printWindow.print();
}
```

---

## 📝 Связанные эндпоинты

- `POST /api/users/auth/login/` - Вход с полученными учетными данными
- `GET /api/users/employees/cashiers/` - Список кассиров для выбора
- `GET /api/users/stores/` - Список магазинов владельца

---

**Дата создания:** 2025-11-19
**Версия API:** 1.0
