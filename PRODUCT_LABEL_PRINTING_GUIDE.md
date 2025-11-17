# Печать этикеток для товаров

## Описание
Endpoint для получения данных для печати этикеток товаров с штрих-кодом, названием и ценой.

## GET /api/products/products/{id}/print-label/

### Возвращаемые данные
- **Название товара**
- **Цена продажи** (форматированная и числовая)
- **Штрих-код** (как base64 изображение PNG)
- **Артикул (SKU)**
- **Единица измерения**

### Query параметры

| Параметр | Тип | Обязательный | По умолчанию | Описание |
|----------|-----|--------------|--------------|----------|
| `quantity` | integer | Нет | 1 | Количество этикеток для печати |

---

## Примеры запросов

### cURL

#### Получить одну этикетку
```bash
curl -X GET "http://localhost:8000/api/products/products/5/print-label/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-Key: YOUR_TENANT_KEY"
```

#### Получить несколько этикеток
```bash
curl -X GET "http://localhost:8000/api/products/products/5/print-label/?quantity=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant-Key: YOUR_TENANT_KEY"
```

---

### JavaScript (Axios)

```javascript
import api from '@/utils/api';

// Получить данные для одной этикетки
const getProductLabel = async (productId) => {
  const response = await api.get(`/products/products/${productId}/print-label/`);
  return response.data;
};

// Получить данные для нескольких этикеток
const getProductLabels = async (productId, quantity) => {
  const response = await api.get(
    `/products/products/${productId}/print-label/?quantity=${quantity}`
  );
  return response.data;
};

// Использование
const labelData = await getProductLabel(5);
console.log(labelData);
```

---

## Успешный ответ (200 OK)

```json
{
  "status": "success",
  "data": {
    "product": {
      "id": 5,
      "name": "Coca-Cola 0.5л",
      "sku": "DRINK-001",
      "barcode": "1234567890123",
      "unit": "шт"
    },
    "price": {
      "sale_price": 5000.0,
      "formatted_price": "5,000.00",
      "currency": "сум"
    },
    "barcode_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "quantity": 1,
    "generated_at": "2025-11-17T18:30:45.123456+05:00"
  }
}
```

### Описание полей ответа

| Поле | Тип | Описание |
|------|-----|----------|
| `product.id` | integer | ID товара |
| `product.name` | string | Название товара |
| `product.sku` | string | Артикул товара |
| `product.barcode` | string | Штрих-код товара (может быть null) |
| `product.unit` | string | Единица измерения (шт, кг, л и т.д.) |
| `price.sale_price` | float | Цена продажи (число) |
| `price.formatted_price` | string | Цена продажи (форматированная строка) |
| `price.currency` | string | Валюта (по умолчанию "сум") |
| `barcode_image` | string | Изображение штрих-кода в формате data URL (base64) |
| `quantity` | integer | Количество этикеток для печати |
| `generated_at` | string | Дата и время генерации (ISO 8601) |

---

## Ошибки

### 400 Bad Request - У товара нет цены

```json
{
  "status": "error",
  "message": "У товара не указана цена"
}
```

### 404 Not Found - Товар не найден

```json
{
  "detail": "Not found."
}
```

---

## React компонент для печати этикеток

### Простой компонент с предпросмотром

```typescript
// components/ProductLabelPrinter.tsx
import { useState } from 'react';
import api from '@/utils/api';

interface ProductLabelPrinterProps {
  productId: number;
  productName: string;
}

export const ProductLabelPrinter = ({ productId, productName }: ProductLabelPrinterProps) => {
  const [labelData, setLabelData] = useState<any>(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(false);

  const loadLabelData = async () => {
    try {
      setLoading(true);
      const response = await api.get(
        `/products/products/${productId}/print-label/?quantity=${quantity}`
      );
      setLabelData(response.data.data);
    } catch (error) {
      console.error('Ошибка загрузки этикетки:', error);
      alert('Не удалось загрузить данные этикетки');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    if (!labelData) return;

    // Открываем окно печати
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      alert('Не удалось открыть окно печати. Разрешите всплывающие окна.');
      return;
    }

    // Формируем HTML для печати
    const printContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Печать этикетки - ${labelData.product.name}</title>
        <style>
          @media print {
            @page {
              size: 58mm 40mm;
              margin: 2mm;
            }
            body {
              margin: 0;
              padding: 0;
            }
          }

          body {
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 5px;
          }

          .label {
            width: 54mm;
            height: 36mm;
            border: 1px solid #ccc;
            padding: 3mm;
            margin-bottom: 5mm;
            page-break-after: always;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: space-between;
          }

          .label:last-child {
            page-break-after: avoid;
          }

          .product-name {
            font-size: 12px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 2mm;
            max-height: 8mm;
            overflow: hidden;
          }

          .barcode {
            width: 100%;
            height: 15mm;
            object-fit: contain;
            margin: 2mm 0;
          }

          .price {
            font-size: 16px;
            font-weight: bold;
            text-align: center;
            margin-top: 2mm;
          }

          .sku {
            font-size: 8px;
            color: #666;
            text-align: center;
          }
        </style>
      </head>
      <body>
        ${Array(labelData.quantity).fill(0).map(() => `
          <div class="label">
            <div class="product-name">${labelData.product.name}</div>
            ${labelData.barcode_image
              ? `<img src="${labelData.barcode_image}" alt="Barcode" class="barcode" />`
              : `<div class="sku">SKU: ${labelData.product.sku}</div>`
            }
            <div class="price">${labelData.price.formatted_price} ${labelData.price.currency}</div>
          </div>
        `).join('')}
        <script>
          window.onload = () => {
            window.print();
            setTimeout(() => window.close(), 500);
          };
        </script>
      </body>
      </html>
    `;

    printWindow.document.write(printContent);
    printWindow.document.close();
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h3>Печать этикетки: {productName}</h3>

      <div style={{ marginBottom: '15px' }}>
        <label>
          Количество этикеток:
          <input
            type="number"
            min="1"
            max="100"
            value={quantity}
            onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
            style={{ marginLeft: '10px', padding: '5px', width: '80px' }}
          />
        </label>
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
        <button
          onClick={loadLabelData}
          disabled={loading}
          style={{
            padding: '10px 20px',
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Загрузка...' : 'Загрузить предпросмотр'}
        </button>

        {labelData && (
          <button
            onClick={handlePrint}
            style={{
              padding: '10px 20px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            🖨️ Печать
          </button>
        )}
      </div>

      {/* Предпросмотр */}
      {labelData && (
        <div
          style={{
            border: '2px dashed #007bff',
            padding: '15px',
            borderRadius: '8px',
            backgroundColor: '#f8f9fa'
          }}
        >
          <h4>Предпросмотр этикетки:</h4>
          <div
            style={{
              border: '1px solid #ccc',
              padding: '10px',
              backgroundColor: 'white',
              display: 'inline-block',
              textAlign: 'center'
            }}
          >
            <div style={{ fontWeight: 'bold', marginBottom: '10px' }}>
              {labelData.product.name}
            </div>
            {labelData.barcode_image && (
              <img
                src={labelData.barcode_image}
                alt="Barcode"
                style={{ maxWidth: '200px', height: 'auto' }}
              />
            )}
            <div style={{ fontSize: '20px', fontWeight: 'bold', marginTop: '10px' }}>
              {labelData.price.formatted_price} {labelData.price.currency}
            </div>
            <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
              SKU: {labelData.product.sku}
            </div>
          </div>
          <p style={{ marginTop: '10px', color: '#666' }}>
            Будет напечатано: {labelData.quantity} шт
          </p>
        </div>
      )}
    </div>
  );
};
```

### Использование в списке товаров

```typescript
// components/ProductList.tsx
import { useState } from 'react';
import { ProductLabelPrinter } from './ProductLabelPrinter';

export const ProductList = () => {
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState<any>(null);

  return (
    <div>
      <h2>Товары</h2>

      <table>
        <thead>
          <tr>
            <th>Название</th>
            <th>Артикул</th>
            <th>Цена</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product: any) => (
            <tr key={product.id}>
              <td>{product.name}</td>
              <td>{product.sku}</td>
              <td>{product.pricing?.sale_price}</td>
              <td>
                <button onClick={() => setSelectedProduct(product)}>
                  🖨️ Печать этикетки
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Модальное окно для печати */}
      {selectedProduct && (
        <>
          <div
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              backgroundColor: 'white',
              padding: '20px',
              boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
              zIndex: 1001,
              maxWidth: '600px',
              width: '90%'
            }}
          >
            <ProductLabelPrinter
              productId={selectedProduct.id}
              productName={selectedProduct.name}
            />
            <button
              onClick={() => setSelectedProduct(null)}
              style={{ marginTop: '15px', padding: '8px 16px' }}
            >
              Закрыть
            </button>
          </div>

          {/* Затемнение фона */}
          <div
            onClick={() => setSelectedProduct(null)}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0,0,0,0.5)',
              zIndex: 1000
            }}
          />
        </>
      )}
    </div>
  );
};
```

---

## Быстрая печать без предпросмотра

```typescript
// utils/printLabel.ts
import api from '@/utils/api';

export const quickPrintLabel = async (productId: number, quantity: number = 1) => {
  try {
    // Получаем данные этикетки
    const response = await api.get(
      `/products/products/${productId}/print-label/?quantity=${quantity}`
    );
    const labelData = response.data.data;

    // Формируем HTML для печати
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      throw new Error('Не удалось открыть окно печати');
    }

    const printContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Печать этикетки</title>
        <style>
          @media print {
            @page { size: 58mm 40mm; margin: 2mm; }
            body { margin: 0; padding: 0; }
          }
          .label {
            width: 54mm;
            height: 36mm;
            padding: 3mm;
            text-align: center;
            page-break-after: always;
          }
          .name { font-size: 12px; font-weight: bold; margin-bottom: 2mm; }
          .barcode { width: 100%; height: 15mm; }
          .price { font-size: 16px; font-weight: bold; margin-top: 2mm; }
        </style>
      </head>
      <body>
        ${Array(labelData.quantity).fill(0).map(() => `
          <div class="label">
            <div class="name">${labelData.product.name}</div>
            ${labelData.barcode_image
              ? `<img src="${labelData.barcode_image}" class="barcode" />`
              : ''
            }
            <div class="price">${labelData.price.formatted_price} ${labelData.price.currency}</div>
          </div>
        `).join('')}
        <script>
          window.onload = () => {
            window.print();
            setTimeout(() => window.close(), 500);
          };
        </script>
      </body>
      </html>
    `;

    printWindow.document.write(printContent);
    printWindow.document.close();

  } catch (error) {
    console.error('Ошибка печати:', error);
    throw error;
  }
};

// Использование
import { quickPrintLabel } from '@/utils/printLabel';

<button onClick={() => quickPrintLabel(productId, 5)}>
  Печать 5 этикеток
</button>
```

---

## Размеры этикеток

### Стандартные размеры

| Размер | Ширина | Высота | Применение |
|--------|--------|--------|------------|
| Малая | 40mm | 30mm | Мелкие товары |
| Средняя | 58mm | 40mm | Стандарт (рекомендуется) |
| Большая | 100mm | 50mm | Крупные товары |

Размер можно настроить в CSS:
```css
@page {
  size: 58mm 40mm; /* Ширина x Высота */
  margin: 2mm;
}
```

---

## Поддерживаемые типы штрих-кодов

Endpoint автоматически использует **Code128** для генерации штрих-кодов.

Другие поддерживаемые форматы (можно настроить в коде):
- EAN13
- EAN8
- UPC-A
- Code39
- Code128 (по умолчанию)

---

## Резюме

### Endpoint
```
GET /api/products/products/{id}/print-label/?quantity=N
```

### Возвращает
- Название товара
- Цену
- Штрих-код (base64 PNG)
- Артикул
- Единицу измерения

### Использование
1. Получить данные через API
2. Отобразить предпросмотр (опционально)
3. Открыть окно печати с HTML
4. Напечатать N этикеток

Готово! 🖨️
