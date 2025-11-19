# Исправление ошибки валидации смены

## Проблема

**Ошибка:** "Iltimos, avval smenani oching!" (Пожалуйста, сначала откройте смену)

**Причина:** Валидация смены в сериализаторе пыталась обратиться к `session.status`, но когда в запросе приходил только ID смены (число), возникала ошибка, так как у числа нет атрибута `status`.

## Что было исправлено

### Файлы:
- [sales/serializers.py:239-258](sales/serializers.py#L239-L258) - SaleSerializer
- [sales/serializers.py:390-411](sales/serializers.py#L390-L411) - SaleCreateUpdateSerializer

### Изменения:

**До:**
```python
def validate(self, data):
    """Валидация продажи"""
    session = data.get('session')

    # Проверяем что смена открыта
    if session and session.status != 'open':  # ❌ Ошибка если session это ID
        raise serializers.ValidationError({
            'session': 'Смена закрыта, невозможно создать продажу'
        })
```

**После:**
```python
def validate(self, data):
    """Валидация продажи"""
    session = data.get('session')

    # Проверяем что смена открыта
    if session:
        # Если session это ID (число), получаем объект из базы
        if isinstance(session, int):
            try:
                session = CashierSession.objects.get(pk=session)
            except CashierSession.DoesNotExist:
                raise serializers.ValidationError({
                    'session': 'Смена не найдена'
                })

        # Проверяем статус смены
        if session.status != 'open':
            raise serializers.ValidationError({
                'session': 'Смена закрыта, невозможно создать продажу'
            })
```

## Как это работает

1. **Проверка типа:** Сначала проверяем, является ли `session` числом (ID)
2. **Загрузка объекта:** Если это ID, загружаем объект CashierSession из базы данных
3. **Валидация статуса:** Теперь можно безопасно проверить `session.status`

## Примеры использования

### 1. Правильное открытие смены

```bash
POST /api/services/sessions/open/
Headers:
  Authorization: Bearer {token}
  X-Tenant-Key: {tenant_key}

Body:
{
  "opening_balance": 100000
}
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Смена успешно открыта",
  "data": {
    "id": 5,
    "status": "open",
    "cashier_name": "Иван Петров",
    "opening_cash": 100000.00,
    "opened_at": "2025-11-18T10:00:00+05:00"
  }
}
```

### 2. Проверка текущей смены

```bash
GET /api/services/sessions/current/
```

**Ответ (если смена открыта):**
```json
{
  "status": "success",
  "data": {
    "id": 5,
    "status": "open",
    "cashier_name": "Иван Петров",
    "opening_cash": 100000.00,
    "opened_at": "2025-11-18T10:00:00+05:00"
  }
}
```

**Ответ (если смены нет):**
```json
{
  "status": "error",
  "message": "Нет открытой смены",
  "data": null
}
```

### 3. Создание продажи с открытой сменой

```bash
POST /api/services/sales/
Body:
{
  "session": 5,  // ✅ Теперь правильно валидируется
  "items": [
    {
      "product": 10,
      "quantity": 2,
      "price": 50000
    }
  ],
  "payments": [
    {
      "payment_method": "cash",
      "amount": 100000
    }
  ]
}
```

**Успешный ответ:**
```json
{
  "id": 123,
  "sale_number": "SALE-2025-00123",
  "session": 5,
  "status": "completed",
  "total_amount": 100000.00,
  "items": [...],
  "payments": [...]
}
```

### 4. Ошибки валидации

#### 4.1. Смена не найдена

**Запрос:**
```json
{
  "session": 999,  // ❌ Несуществующая смена
  "items": [...]
}
```

**Ответ:**
```json
{
  "session": ["Смена не найдена"]
}
```

#### 4.2. Смена закрыта

**Запрос:**
```json
{
  "session": 3,  // ❌ Эта смена уже закрыта
  "items": [...]
}
```

**Ответ:**
```json
{
  "session": ["Смена закрыта, невозможно создать продажу"]
}
```

#### 4.3. Нет открытой смены

Если вы пытаетесь создать продажу, но не указали session или смена закрыта:

**Решение:**
1. Проверьте наличие открытой смены: `GET /api/services/sessions/current/`
2. Если смены нет, откройте новую: `POST /api/services/sessions/open/`
3. Используйте ID открытой смены при создании продажи

## Frontend примеры

### Проверка смены перед продажей

```typescript
import { getCurrentSession, openSession } from '@/services/sessions';
import { createSale } from '@/services/sales';

async function handleCreateSale(saleData) {
  try {
    // 1. Проверяем наличие открытой смены
    let session;
    try {
      const sessionResponse = await getCurrentSession();
      session = sessionResponse.data;
    } catch (error) {
      // Нет открытой смены - открываем новую
      console.log('Нет открытой смены, открываем новую...');
      const openingBalance = prompt('Введите начальный баланс:');
      const openResponse = await openSession({
        opening_balance: parseFloat(openingBalance)
      });
      session = openResponse.data;
    }

    // 2. Создаём продажу с ID смены
    const sale = await createSale({
      session: session.id,
      items: saleData.items,
      payments: saleData.payments
    });

    console.log('Продажа создана:', sale);
    return sale;

  } catch (error) {
    if (error.response?.data?.session) {
      // Ошибка валидации смены
      alert(`Ошибка смены: ${error.response.data.session[0]}`);
    } else {
      console.error('Ошибка создания продажи:', error);
      alert('Не удалось создать продажу');
    }
  }
}
```

### React Hook для управления сменой

```typescript
import { useState, useEffect } from 'react';
import { getCurrentSession, openSession, closeSession } from '@/services/sessions';

export const useSession = () => {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Загрузка текущей смены
  const loadSession = async () => {
    try {
      setLoading(true);
      const response = await getCurrentSession();
      setSession(response.data);
      setError(null);
    } catch (err) {
      if (err.response?.status === 404) {
        // Смены нет - это нормально
        setSession(null);
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  // Открыть смену
  const open = async (openingBalance: number) => {
    try {
      setLoading(true);
      const response = await openSession({ opening_balance: openingBalance });
      setSession(response.data);
      setError(null);
      return response.data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Закрыть смену
  const close = async (actualCash: number) => {
    if (!session) return;

    try {
      setLoading(true);
      await closeSession(session.id, { actual_cash: actualCash });
      setSession(null);
      setError(null);
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSession();
  }, []);

  return {
    session,
    loading,
    error,
    isOpen: session?.status === 'open',
    open,
    close,
    reload: loadSession
  };
};
```

### Использование в компоненте продажи

```typescript
import { useSession } from '@/hooks/useSession';

export const CreateSalePage = () => {
  const { session, isOpen, loading, open } = useSession();
  const [items, setItems] = useState([]);
  const [payments, setPayments] = useState([]);

  const handleOpenSession = async () => {
    const balance = parseFloat(prompt('Начальный баланс:') || '0');
    try {
      await open(balance);
      alert('Смена успешно открыта!');
    } catch (error) {
      alert('Ошибка открытия смены');
    }
  };

  const handleCreateSale = async () => {
    if (!session || !isOpen) {
      alert('Сначала откройте смену!');
      return;
    }

    try {
      const sale = await createSale({
        session: session.id,  // ✅ Передаём ID смены
        items,
        payments
      });
      alert(`Продажа ${sale.sale_number} создана!`);
    } catch (error) {
      console.error('Ошибка:', error);
      alert('Ошибка создания продажи');
    }
  };

  if (loading) return <div>Загрузка...</div>;

  return (
    <div className="create-sale-page">
      {/* Статус смены */}
      <div className="session-status">
        {isOpen ? (
          <div className="session-open">
            ✅ Смена открыта: {session.cashier_name}
          </div>
        ) : (
          <div className="session-closed">
            ❌ Смена не открыта
            <button onClick={handleOpenSession}>Открыть смену</button>
          </div>
        )}
      </div>

      {/* Форма продажи */}
      <div className="sale-form">
        {/* ... товары, оплата ... */}

        <button
          onClick={handleCreateSale}
          disabled={!isOpen}
        >
          Создать продажу
        </button>
      </div>
    </div>
  );
};
```

## Проверка исправления

### 1. Проверить что Django запускается без ошибок

```bash
python manage.py check
```

**Ожидаемый результат:**
```
System check identified no issues (0 silenced).
```

### 2. Тестовый сценарий

1. **Открыть смену:**
   ```bash
   POST /api/services/sessions/open/
   Body: {"opening_balance": 100000}
   ```

2. **Проверить текущую смену:**
   ```bash
   GET /api/services/sessions/current/
   ```
   Должен вернуть открытую смену с `status: "open"`

3. **Создать продажу:**
   ```bash
   POST /api/services/sales/
   Body: {
     "session": 5,  // ID из шага 1
     "items": [{"product": 10, "quantity": 1, "price": 50000}],
     "payments": [{"payment_method": "cash", "amount": 50000}]
   }
   ```
   Должна успешно создаться без ошибки "Смена закрыта"

4. **Попробовать создать продажу с закрытой сменой:**
   - Сначала закрыть смену: `POST /api/services/sessions/{id}/close/`
   - Попробовать создать продажу с ID закрытой смены
   - Должна вернуться ошибка: `{"session": ["Смена закрыта, невозможно создать продажу"]}`

## Резюме

### Что исправлено:
- ✅ Добавлена проверка типа session перед обращением к атрибутам
- ✅ Правильная обработка случая когда session это ID (число)
- ✅ Улучшенные сообщения об ошибках (на русском языке)
- ✅ Исправление применено к обоим сериализаторам: `SaleSerializer` и `SaleCreateUpdateSerializer`

### Теперь работает:
- ✅ Создание продажи с указанием ID смены
- ✅ Проверка что смена открыта
- ✅ Понятные сообщения об ошибках
- ✅ Нет ошибки "Iltimos, avval smenani oching!" при открытой смене

### Рекомендации:
1. **Всегда проверяйте смену перед продажей** - используйте `GET /api/services/sessions/current/`
2. **Открывайте смену в начале работы** - `POST /api/services/sessions/open/`
3. **Закрывайте смену в конце дня** - `POST /api/services/sessions/{id}/close/`
4. **Используйте frontend hook** для автоматического управления сменой

Готово! 🎉
