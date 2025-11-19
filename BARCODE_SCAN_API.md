# API для сканирования штрих-кода

## Endpoint

```
GET /api/products/products/scan_barcode/
```

## Описание

Endpoint для поиска товара по штрих-коду. Используется на кассе для быстрого добавления товаров при сканировании штрих-кода.

## Параметры запроса

### Query параметры:

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `barcode` | string | ✅ Да | Штрих-код товара для поиска |

## Примеры запросов

### 1. Успешный поиск товара

**Запрос:**
```bash
GET /api/products/products/scan_barcode/?barcode=4870123456789
Headers:
  Authorization: Bearer {token}
  X-Tenant-Key: {tenant_key}
```

**Ответ (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": 10,
    "name": "Молоко 3.2%",
    "description": "Свежее молоко 3.2% жирности",
    "sku": "PROD-001",
    "barcode": "4870123456789",
    "category": {
      "id": 2,
      "name": "Молочные продукты",
      "slug": "dairy"
    },
    "unit": {
      "id": 1,
      "name": "Литр",
      "short_name": "л"
    },
    "pricing": {
      "cost_price": 9000.00,
      "sale_price": 12000.00,
      "min_price": 10000.00,
      "tax_percent": 0.00
    },
    "inventory": {
      "quantity": 150.000,
      "reserved_quantity": 10.000,
      "available_quantity": 140.000,
      "min_quantity": 20.000,
      "max_quantity": 500.000,
      "track_inventory": true
    },
    "is_active": true,
    "is_featured": false,
    "main_image": "https://example.com/media/products/milk.jpg",
    "images": [
      {
        "id": 1,
        "image": "https://example.com/media/products/milk.jpg",
        "is_primary": true,
        "order": 0
      }
    ],
    "attributes": [],
    "created_at": "2025-11-17T10:00:00+05:00",
    "updated_at": "2025-11-18T15:30:00+05:00"
  }
}
```

### 2. Товар не найден

**Запрос:**
```bash
GET /api/products/products/scan_barcode/?barcode=9999999999999
```

**Ответ (404 Not Found):**
```json
{
  "status": "error",
  "message": "Товар с штрих-кодом \"9999999999999\" не найден",
  "code": "product_not_found",
  "barcode": "9999999999999"
}
```

### 3. Штрих-код не указан

**Запрос:**
```bash
GET /api/products/products/scan_barcode/
```

**Ответ (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Не указан штрих-код",
  "code": "barcode_required"
}
```

## Frontend примеры

### TypeScript сервис

```typescript
// services/products.ts
import api from '@/utils/api';

export interface Product {
  id: number;
  name: string;
  sku: string;
  barcode: string;
  pricing: {
    cost_price: number;
    sale_price: number;
    min_price: number;
    tax_percent: number;
  };
  inventory: {
    quantity: number;
    available_quantity: number;
    track_inventory: boolean;
  };
  unit: {
    id: number;
    name: string;
    short_name: string;
  };
  category: {
    id: number;
    name: string;
  };
  main_image?: string;
}

export interface ScanBarcodeResponse {
  status: 'success' | 'error';
  data?: Product;
  message?: string;
  code?: string;
  barcode?: string;
}

/**
 * Поиск товара по штрих-коду
 */
export const scanBarcode = async (barcode: string): Promise<Product> => {
  const response = await api.get<ScanBarcodeResponse>(
    '/products/products/scan_barcode/',
    {
      params: { barcode }
    }
  );

  if (response.data.status === 'success' && response.data.data) {
    return response.data.data;
  }

  throw new Error(response.data.message || 'Товар не найден');
};
```

### React компонент для сканирования

```typescript
import { useState } from 'react';
import { scanBarcode } from '@/services/products';

export const BarcodeScanner = ({ onProductFound }) => {
  const [barcode, setBarcode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleScan = async () => {
    if (!barcode.trim()) {
      setError('Введите штрих-код');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const product = await scanBarcode(barcode);

      // Вызываем callback с найденным товаром
      onProductFound(product);

      // Очищаем поле ввода для следующего сканирования
      setBarcode('');

    } catch (err) {
      setError(err.message);
      console.error('Ошибка сканирования:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleScan();
    }
  };

  return (
    <div className="barcode-scanner">
      <div className="scanner-input">
        <input
          type="text"
          value={barcode}
          onChange={(e) => setBarcode(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Отсканируйте штрих-код..."
          autoFocus
          disabled={loading}
        />
        <button onClick={handleScan} disabled={loading || !barcode}>
          {loading ? 'Поиск...' : 'Найти'}
        </button>
      </div>

      {error && (
        <div className="scanner-error">
          ❌ {error}
        </div>
      )}
    </div>
  );
};
```

### Использование в компоненте продаж

```typescript
import { useState } from 'react';
import { BarcodeScanner } from './BarcodeScanner';
import { createSale } from '@/services/sales';

export const POSPage = () => {
  const [cart, setCart] = useState([]);

  const handleProductFound = (product) => {
    // Проверяем есть ли товар в корзине
    const existingItem = cart.find(item => item.product.id === product.id);

    if (existingItem) {
      // Увеличиваем количество
      setCart(cart.map(item =>
        item.product.id === product.id
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      // Добавляем новый товар
      setCart([...cart, {
        product,
        quantity: 1,
        price: product.pricing.sale_price
      }]);
    }

    // Звуковой сигнал успеха
    playBeep();
  };

  const handleCheckout = async () => {
    try {
      const saleData = {
        session: currentSession.id,
        items: cart.map(item => ({
          product: item.product.id,
          quantity: item.quantity,
          price: item.price
        })),
        payments: [
          {
            payment_method: 'cash',
            amount: calculateTotal()
          }
        ]
      };

      const sale = await createSale(saleData);
      alert(`Продажа ${sale.sale_number} успешно создана!`);
      setCart([]);
    } catch (error) {
      console.error('Ошибка создания продажи:', error);
      alert('Не удалось создать продажу');
    }
  };

  const calculateTotal = () => {
    return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  };

  const playBeep = () => {
    // Воспроизводим звук при успешном сканировании
    const audio = new Audio('/sounds/beep.mp3');
    audio.play();
  };

  return (
    <div className="pos-page">
      <div className="scanner-section">
        <h2>Сканер штрих-кода</h2>
        <BarcodeScanner onProductFound={handleProductFound} />
      </div>

      <div className="cart-section">
        <h2>Корзина ({cart.length})</h2>

        {cart.length === 0 ? (
          <p>Корзина пуста. Отсканируйте товары.</p>
        ) : (
          <>
            <table>
              <thead>
                <tr>
                  <th>Товар</th>
                  <th>Цена</th>
                  <th>Кол-во</th>
                  <th>Сумма</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {cart.map((item, index) => (
                  <tr key={index}>
                    <td>
                      <strong>{item.product.name}</strong>
                      <br />
                      <small>{item.product.barcode}</small>
                    </td>
                    <td>{item.price.toLocaleString()} сум</td>
                    <td>
                      <input
                        type="number"
                        value={item.quantity}
                        onChange={(e) => {
                          const newQty = parseFloat(e.target.value);
                          setCart(cart.map((cartItem, i) =>
                            i === index ? { ...cartItem, quantity: newQty } : cartItem
                          ));
                        }}
                        min="0.01"
                        step="0.01"
                      />
                      {item.product.unit.short_name}
                    </td>
                    <td>
                      {(item.price * item.quantity).toLocaleString()} сум
                    </td>
                    <td>
                      <button
                        onClick={() => setCart(cart.filter((_, i) => i !== index))}
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="cart-total">
              <h3>Итого: {calculateTotal().toLocaleString()} сум</h3>
              <button onClick={handleCheckout} className="checkout-btn">
                Оформить продажу
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
```

### Автоматическое сканирование с USB сканера

Большинство USB сканеров штрих-кода работают как клавиатура - они вводят символы и нажимают Enter.

```typescript
import { useEffect, useRef } from 'react';

export const useBarcodeScanner = (onScan: (barcode: string) => void) => {
  const barcodeBuffer = useRef('');
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      // Игнорируем если фокус на input/textarea
      const target = event.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return;
      }

      // Enter означает конец сканирования
      if (event.key === 'Enter') {
        if (barcodeBuffer.current.length > 0) {
          onScan(barcodeBuffer.current);
          barcodeBuffer.current = '';
        }
        return;
      }

      // Добавляем символ в буфер
      barcodeBuffer.current += event.key;

      // Сбрасываем буфер через 100ms (сканеры вводят быстро)
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        barcodeBuffer.current = '';
      }, 100);
    };

    window.addEventListener('keypress', handleKeyPress);

    return () => {
      window.removeEventListener('keypress', handleKeyPress);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [onScan]);
};

// Использование:
export const POSWithAutoScan = () => {
  const [cart, setCart] = useState([]);

  const handleBarcodeScan = async (barcode: string) => {
    console.log('Отсканирован штрих-код:', barcode);

    try {
      const product = await scanBarcode(barcode);
      addToCart(product);
      playBeep();
    } catch (error) {
      console.error('Товар не найден:', error);
      playErrorSound();
    }
  };

  // Подключаем автосканирование
  useBarcodeScanner(handleBarcodeScan);

  // ... остальной код компонента
};
```

## Обработка ошибок

### Типичные ошибки и их обработка

```typescript
try {
  const product = await scanBarcode(barcode);
  // Успешно найден
  handleProductFound(product);

} catch (error) {
  if (error.response?.status === 404) {
    // Товар не найден
    showNotification('Товар с таким штрих-кодом не найден', 'warning');
    playErrorSound();

  } else if (error.response?.status === 400) {
    // Не указан штрих-код
    showNotification('Штрих-код не указан', 'error');

  } else {
    // Другая ошибка
    showNotification('Ошибка при поиске товара', 'error');
    console.error('Scan error:', error);
  }
}
```

## Особенности работы

### 1. Поиск только активных товаров
Endpoint возвращает только товары с `is_active=true`. Неактивные товары не будут найдены.

### 2. Полная информация о товаре
Возвращается полная информация включая:
- ✅ Цены (cost_price, sale_price, min_price)
- ✅ Остатки (quantity, available_quantity, reserved_quantity)
- ✅ Единицу измерения
- ✅ Категорию
- ✅ Изображения
- ✅ Атрибуты

### 3. Оптимизированный запрос
Используется `select_related` и `prefetch_related` для минимизации запросов к базе данных.

### 4. Уникальность штрих-кода
Каждый товар должен иметь уникальный штрих-код. Если найдено несколько товаров с одинаковым штрих-кодом, вернётся первый найденный.

## Интеграция со сканером

### Рекомендации по настройке USB сканера:

1. **Режим клавиатуры:** Большинство сканеров по умолчанию работают как клавиатура
2. **Суффикс Enter:** Настройте сканер добавлять Enter после штрих-кода
3. **Префикс:** Опционально можно добавить префикс для отличия от ввода с клавиатуры
4. **Скорость сканирования:** Сканеры вводят ~100+ символов в секунду

### Тестирование без сканера:
Для разработки можно использовать обычный input и вводить штрих-код вручную:

```typescript
<input
  type="text"
  placeholder="Введите штрих-код вручную"
  onKeyPress={(e) => {
    if (e.key === 'Enter') {
      handleBarcodeScan(e.currentTarget.value);
      e.currentTarget.value = '';
    }
  }}
/>
```

## Резюме

### Endpoint:
```
GET /api/products/products/scan_barcode/?barcode={barcode}
```

### Обязательные заголовки:
```
Authorization: Bearer {access_token}
X-Tenant-Key: {tenant_key}
```

### Ответы:
- **200 OK** - Товар найден
- **404 Not Found** - Товар не найден
- **400 Bad Request** - Штрих-код не указан

### Возможности:
- ✅ Быстрый поиск товара по штрих-коду
- ✅ Полная информация о товаре (цена, остатки, изображения)
- ✅ Оптимизированный запрос к базе данных
- ✅ Только активные товары
- ✅ Готово к интеграции с USB сканерами

Готово! 🎉
