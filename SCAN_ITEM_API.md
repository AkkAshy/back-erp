# API для сканирования товара на кассе

## Endpoint

```
POST /api/sales/sales/scan-item/
```

## Описание

Endpoint для сканирования и добавления товара в продажу на кассе.

**Особенности:**
- Автоматически создаёт новую продажу (черновик) если нет активной
- Добавляет товар в существующую незавершённую продажу
- Автоматически подставляет цену из pricing товара
- Пересчитывает итоговые суммы после добавления

## Параметры запроса

### Body параметры (JSON):

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `session` | integer | ✅ Да | ID открытой кассовой смены |
| `product` | integer | ✅ Да | ID товара для добавления |
| `quantity` | number | ❌ Нет | Количество товара (по умолчанию 1) |
| `batch` | integer | ❌ Нет | ID партии товара (опционально) |

## Примеры запросов

### 1. Добавление товара (простой случай)

**Запрос:**
```bash
POST /api/sales/sales/scan-item/
Headers:
  Authorization: Bearer {token}
  X-Tenant-Key: {tenant_key}
  Content-Type: application/json

Body:
{
  "session": 5,
  "product": 10,
  "quantity": 1
}
```

**Ответ (200 OK):**
```json
{
  "status": "success",
  "message": "Товар добавлен",
  "data": {
    "id": 123,
    "sale_number": "CHECK-20251118153045",
    "session": 5,
    "receipt_number": "CHECK-20251118153045",
    "status": "pending",
    "customer_name": "",
    "customer_phone": "",
    "subtotal": 12000.00,
    "discount_amount": 0.00,
    "discount_percent": 0.00,
    "tax_amount": 0.00,
    "total_amount": 12000.00,
    "items": [
      {
        "id": 456,
        "product": 10,
        "product_name": "Молоко 3.2%",
        "product_sku": "PROD-001",
        "batch": null,
        "quantity": 1.000,
        "unit_price": 12000.00,
        "discount_amount": 0.00,
        "line_total": 12000.00
      }
    ],
    "payments": [],
    "created_at": "2025-11-18T15:30:45+05:00",
    "completed_at": null
  }
}
```

### 2. Добавление товара с количеством

**Запрос:**
```bash
POST /api/sales/sales/scan-item/
Body:
{
  "session": 5,
  "product": 10,
  "quantity": 2.5
}
```

**Ответ:** Товар добавлен с количеством 2.5, `line_total` = 2.5 × 12000 = 30000

### 3. Добавление товара с указанием партии

**Запрос:**
```bash
POST /api/sales/sales/scan-item/
Body:
{
  "session": 5,
  "product": 10,
  "quantity": 1,
  "batch": 25
}
```

### 4. Последовательное добавление товаров

**Первый товар:**
```bash
POST /api/sales/sales/scan-item/
Body: {"session": 5, "product": 10, "quantity": 1}
```
Создаётся новая продажа с 1 позицией.

**Второй товар:**
```bash
POST /api/sales/sales/scan-item/
Body: {"session": 5, "product": 15, "quantity": 2}
```
Добавляется в **ту же** продажу (pending), теперь 2 позиции.

**Третий товар:**
```bash
POST /api/sales/sales/scan-item/
Body: {"session": 5, "product": 20, "quantity": 1}
```
Добавляется в **ту же** продажу, теперь 3 позиции.

## Ошибки

### 1. Смена не указана или товар не указан

**Запрос:**
```json
{
  "session": 5
  // product отсутствует
}
```

**Ответ (400 Bad Request):**
```json
{
  "error": "Укажите session и product"
}
```

### 2. Смена не найдена или закрыта

**Запрос:**
```json
{
  "session": 999,
  "product": 10
}
```

**Ответ (404 Not Found):**
```json
{
  "error": "Смена не найдена или закрыта"
}
```

### 3. Товар не найден

**Запрос:**
```json
{
  "session": 5,
  "product": 9999
}
```

**Ответ (404 Not Found):**
```json
{
  "error": "Товар не найден"
}
```

### 4. Партия не найдена

**Запрос:**
```json
{
  "session": 5,
  "product": 10,
  "batch": 9999
}
```

**Ответ (404 Not Found):**
```json
{
  "error": "Партия не найдена"
}
```

## Логика работы

### 1. Проверка смены
- Проверяется что смена существует и имеет статус `'open'`
- Если смена закрыта или не найдена → ошибка 404

### 2. Проверка товара
- Товар загружается с pricing для получения цены
- Если товар не найден → ошибка 404

### 3. Поиск или создание продажи
- Ищется последняя незавершённая продажа (`status='pending'`) для этой смены
- Если не найдена → создаётся новая продажа с автогенерированным номером чека

### 4. Добавление позиции
- Создаётся новая позиция `SaleItem` с указанным товаром и количеством
- Цена берётся из `product.pricing.sale_price` (или `cost_price` если sale_price нет)

### 5. Пересчёт сумм
- Вызывается `sale.calculate_totals()` для обновления итоговых сумм

## Frontend примеры

### TypeScript сервис

```typescript
// services/sales.ts
import api from '@/utils/api';

export interface ScanItemRequest {
  session: number;
  product: number;
  quantity?: number;
  batch?: number;
}

export interface ScanItemResponse {
  status: 'success' | 'error';
  message: string;
  data?: Sale;
  error?: string;
}

/**
 * Сканировать товар и добавить в продажу
 */
export const scanItem = async (data: ScanItemRequest) => {
  const response = await api.post<ScanItemResponse>(
    '/sales/sales/scan-item/',
    data
  );

  if (response.data.status === 'success') {
    return response.data.data;
  }

  throw new Error(response.data.error || response.data.message);
};
```

### React компонент POS кассы

```typescript
import { useState, useEffect } from 'react';
import { scanItem } from '@/services/sales';
import { scanBarcode } from '@/services/products';
import { useSession } from '@/hooks/useSession';

export const POSCashier = () => {
  const { session, isOpen } = useSession();
  const [currentSale, setCurrentSale] = useState(null);
  const [barcodeInput, setBarcodeInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleBarcodeScan = async (barcode: string) => {
    if (!session || !isOpen) {
      alert('Откройте смену перед началом работы!');
      return;
    }

    try {
      setLoading(true);

      // 1. Найти товар по штрих-коду
      const product = await scanBarcode(barcode);

      // 2. Добавить товар в продажу
      const sale = await scanItem({
        session: session.id,
        product: product.id,
        quantity: 1
      });

      // 3. Обновить текущую продажу
      setCurrentSale(sale);

      // Очистить поле ввода
      setBarcodeInput('');

      // Звуковой сигнал
      playBeep();

    } catch (error) {
      console.error('Ошибка сканирования:', error);
      alert(error.message);
      playErrorSound();
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && barcodeInput.trim()) {
      handleBarcodeScan(barcodeInput.trim());
    }
  };

  const calculateTotal = () => {
    return currentSale?.total_amount || 0;
  };

  const handleCheckout = () => {
    // Перейти к оплате
    if (currentSale) {
      // Навигация к странице оплаты
      window.location.href = `/checkout/${currentSale.id}`;
    }
  };

  const handleCancelSale = async () => {
    if (currentSale && confirm('Отменить текущую продажу?')) {
      // Логика отмены продажи
      setCurrentSale(null);
    }
  };

  return (
    <div className="pos-cashier">
      {/* Статус смены */}
      <div className="session-info">
        {isOpen ? (
          <span className="session-open">
            ✅ Смена открыта: {session.cashier_name}
          </span>
        ) : (
          <span className="session-closed">
            ❌ Откройте смену для начала работы
          </span>
        )}
      </div>

      {/* Сканер */}
      <div className="scanner-section">
        <input
          type="text"
          value={barcodeInput}
          onChange={(e) => setBarcodeInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Отсканируйте штрих-код..."
          disabled={!isOpen || loading}
          autoFocus
        />
        {loading && <span>Добавление...</span>}
      </div>

      {/* Текущая продажа */}
      {currentSale && (
        <div className="current-sale">
          <div className="sale-header">
            <h3>Чек: {currentSale.receipt_number}</h3>
            <button onClick={handleCancelSale} className="btn-cancel">
              Отменить
            </button>
          </div>

          {/* Товары */}
          <table className="items-table">
            <thead>
              <tr>
                <th>Товар</th>
                <th>Цена</th>
                <th>Кол-во</th>
                <th>Сумма</th>
              </tr>
            </thead>
            <tbody>
              {currentSale.items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <strong>{item.product_name}</strong>
                    <br />
                    <small>{item.product_sku}</small>
                  </td>
                  <td>{item.unit_price.toLocaleString()} сум</td>
                  <td>{item.quantity}</td>
                  <td>{item.line_total.toLocaleString()} сум</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Итого */}
          <div className="sale-total">
            <div className="total-row">
              <span>Подытог:</span>
              <strong>{currentSale.subtotal.toLocaleString()} сум</strong>
            </div>
            {currentSale.discount_amount > 0 && (
              <div className="total-row discount">
                <span>Скидка:</span>
                <strong>-{currentSale.discount_amount.toLocaleString()} сум</strong>
              </div>
            )}
            <div className="total-row grand-total">
              <span>ИТОГО:</span>
              <strong>{currentSale.total_amount.toLocaleString()} сум</strong>
            </div>
          </div>

          {/* Кнопка оформления */}
          <button
            onClick={handleCheckout}
            className="btn-checkout"
            disabled={!currentSale.items.length}
          >
            Оформить ({currentSale.items.length} поз.)
          </button>
        </div>
      )}

      {/* Если нет текущей продажи */}
      {!currentSale && isOpen && (
        <div className="no-sale">
          <p>Отсканируйте товар для начала продажи</p>
        </div>
      )}
    </div>
  );
};

// Звуковые сигналы
const playBeep = () => {
  const audio = new Audio('/sounds/beep.mp3');
  audio.play();
};

const playErrorSound = () => {
  const audio = new Audio('/sounds/error.mp3');
  audio.play();
};
```

### Интеграция с USB сканером

```typescript
import { useEffect, useRef } from 'react';

/**
 * Hook для автоматического сканирования с USB сканера штрих-кода
 */
export const useBarcodeScannerAuto = (
  onScan: (barcode: string) => void,
  enabled: boolean = true
) => {
  const barcodeBuffer = useRef('');
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (!enabled) return;

    const handleKeyPress = (event: KeyboardEvent) => {
      // Игнорируем если фокус на input/textarea (кроме автофокуса на сканере)
      const target = event.target as HTMLElement;
      const isScannerInput = target.classList.contains('barcode-scanner-input');

      if (!isScannerInput && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) {
        return;
      }

      // Enter означает конец штрих-кода
      if (event.key === 'Enter') {
        if (barcodeBuffer.current.length > 0) {
          onScan(barcodeBuffer.current);
          barcodeBuffer.current = '';
        }
        event.preventDefault();
        return;
      }

      // Добавляем символ в буфер
      if (event.key.length === 1) {
        barcodeBuffer.current += event.key;

        // Сбрасываем буфер через 100ms
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }

        timeoutRef.current = setTimeout(() => {
          barcodeBuffer.current = '';
        }, 100);
      }
    };

    window.addEventListener('keypress', handleKeyPress);

    return () => {
      window.removeEventListener('keypress', handleKeyPress);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [onScan, enabled]);
};

// Использование:
export const POSWithAutoScan = () => {
  const { session, isOpen } = useSession();
  const [currentSale, setCurrentSale] = useState(null);

  const handleAutoScan = async (barcode: string) => {
    console.log('Автоматически отсканирован:', barcode);

    if (!session || !isOpen) {
      playErrorSound();
      return;
    }

    try {
      // Поиск товара
      const product = await scanBarcode(barcode);

      // Добавление в продажу
      const sale = await scanItem({
        session: session.id,
        product: product.id,
        quantity: 1
      });

      setCurrentSale(sale);
      playBeep();

    } catch (error) {
      console.error('Ошибка:', error);
      playErrorSound();
      alert(error.message);
    }
  };

  // Подключаем автосканирование
  useBarcodeScannerAuto(handleAutoScan, isOpen);

  // ... остальной код
};
```

## Комбинированный workflow

### Полный процесс продажи с сканированием:

1. **Открытие смены:**
   ```typescript
   POST /api/sales/sessions/open/
   Body: { "opening_balance": 100000 }
   ```

2. **Сканирование товаров:**
   ```typescript
   // Товар 1
   POST /api/sales/sales/scan-item/
   Body: { "session": 5, "product": 10, "quantity": 1 }

   // Товар 2
   POST /api/sales/sales/scan-item/
   Body: { "session": 5, "product": 15, "quantity": 2 }

   // Товар 3
   POST /api/sales/sales/scan-item/
   Body: { "session": 5, "product": 20, "quantity": 1 }
   ```

3. **Оформление продажи:**
   ```typescript
   POST /api/sales/sales/{sale_id}/complete/
   Body: {
     "payments": [
       {
         "payment_method": "cash",
         "amount": 50000,
         "received_amount": 100000
       }
     ]
   }
   ```

4. **Закрытие смены:**
   ```typescript
   POST /api/sales/sessions/{session_id}/close/
   Body: { "actual_cash": 150000 }
   ```

## Особенности

### 1. Автоматическое создание продажи
Если нет незавершённой продажи, endpoint автоматически создаёт новую с:
- Автогенерированным номером чека: `CHECK-{timestamp}`
- Статусом `pending`
- Привязкой к текущей смене

### 2. Повторное добавление того же товара
Каждый вызов создаёт **новую позицию** в продаже. Если нужно объединить одинаковые товары, делайте это на frontend.

### 3. Цена товара
Цена берётся автоматически из `product.pricing.sale_price`. Если нужна другая цена, используйте endpoint `add_item` с явным указанием `unit_price`.

### 4. Пересчёт сумм
После каждого добавления автоматически пересчитываются:
- `subtotal` - сумма всех позиций
- `total_amount` - итоговая сумма с учётом скидок

## Резюме

### Endpoint:
```
POST /api/sales/sales/scan-item/
```

### Обязательные параметры:
- `session` (integer) - ID открытой смены
- `product` (integer) - ID товара

### Опциональные параметры:
- `quantity` (number) - Количество (по умолчанию 1)
- `batch` (integer) - ID партии товара

### Ответы:
- **200 OK** - Товар добавлен успешно
- **400 Bad Request** - Не указаны обязательные параметры
- **404 Not Found** - Смена, товар или партия не найдены

### Возможности:
- ✅ Автоматическое создание новой продажи
- ✅ Добавление товара в существующую продажу
- ✅ Автоматическое определение цены
- ✅ Пересчёт итоговых сумм
- ✅ Поддержка партий товара
- ✅ Готово к интеграции с USB сканерами

Готово! 🎉
