# Гайд: Печать штрихкодов партий на фронтенде

## Описание

Каждая партия товара имеет уникальный штрихкод в формате:
```
BATCH-20241215103045-A3F4B2C1
```

Этот штрихкод можно использовать для:
- 📄 Печати этикеток
- 📱 Сканирования при приёмке
- 📊 Инвентаризации
- 🔄 FIFO/FEFO учёта

---

## Библиотеки для генерации штрихкодов

### React (рекомендуется)

#### 1. **react-barcode** (простая, популярная)

**Установка:**
```bash
npm install react-barcode
```

**Использование:**
```jsx
import React from 'react';
import Barcode from 'react-barcode';

function BatchLabel({ batch }) {
  return (
    <div className="batch-label">
      <h3>{batch.product_name}</h3>
      <p>Партия: {batch.batch_number}</p>

      {/* Генерация штрихкода */}
      <Barcode
        value={batch.barcode}
        format="CODE128"
        width={2}
        height={60}
        displayValue={true}
        fontSize={14}
      />

      <p>Срок годности: {batch.expiry_date}</p>
      <p>Количество: {batch.quantity} шт</p>
    </div>
  );
}

export default BatchLabel;
```

#### 2. **JsBarcode** (больше настроек)

**Установка:**
```bash
npm install jsbarcode
```

**Использование:**
```jsx
import React, { useEffect, useRef } from 'react';
import JsBarcode from 'jsbarcode';

function BatchLabel({ batch }) {
  const barcodeRef = useRef(null);

  useEffect(() => {
    if (barcodeRef.current) {
      JsBarcode(barcodeRef.current, batch.barcode, {
        format: 'CODE128',
        width: 2,
        height: 60,
        displayValue: true,
        fontSize: 14,
        margin: 10
      });
    }
  }, [batch.barcode]);

  return (
    <div className="batch-label">
      <h3>{batch.product_name}</h3>
      <p>Партия: {batch.batch_number}</p>

      {/* SVG элемент для штрихкода */}
      <svg ref={barcodeRef}></svg>

      <p>Срок годности: {batch.expiry_date}</p>
      <p>Количество: {batch.quantity} шт</p>
    </div>
  );
}

export default BatchLabel;
```

---

## Полный пример: Компонент для печати этикетки

```jsx
import React, { useState, useEffect } from 'react';
import Barcode from 'react-barcode';
import './BatchLabel.css';

function BatchLabelPrint({ batchId }) {
  const [batch, setBatch] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Загружаем данные партии
    const token = localStorage.getItem('access_token');
    const tenantKey = localStorage.getItem('tenant_key');

    fetch(`http://localhost:8000/api/products/batches/${batchId}/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-Key': tenantKey
      }
    })
      .then(r => r.json())
      .then(data => {
        setBatch(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error loading batch:', err);
        setLoading(false);
      });
  }, [batchId]);

  const handlePrint = () => {
    window.print();
  };

  if (loading) return <div>Загрузка...</div>;
  if (!batch) return <div>Партия не найдена</div>;

  return (
    <div className="label-container">
      <div className="batch-label">
        {/* Название товара */}
        <div className="label-header">
          <h2>{batch.product_name}</h2>
        </div>

        {/* Номер партии */}
        <div className="label-info">
          <strong>Партия:</strong> {batch.batch_number}
        </div>

        {/* Штрихкод */}
        <div className="label-barcode">
          <Barcode
            value={batch.barcode}
            format="CODE128"
            width={2}
            height={50}
            displayValue={true}
            fontSize={12}
            margin={5}
          />
        </div>

        {/* Дополнительная информация */}
        <div className="label-details">
          {batch.expiry_date && (
            <div className="detail-row">
              <strong>Срок годности:</strong> {batch.expiry_date}
            </div>
          )}
          <div className="detail-row">
            <strong>Количество:</strong> {batch.quantity}
          </div>
          {batch.purchase_price && (
            <div className="detail-row">
              <strong>Цена закупки:</strong> {batch.purchase_price} сум
            </div>
          )}
        </div>

        {/* Дата печати */}
        <div className="label-footer">
          <small>Напечатано: {new Date().toLocaleString('ru-RU')}</small>
        </div>
      </div>

      {/* Кнопка печати (скрывается при печати) */}
      <div className="print-controls">
        <button onClick={handlePrint} className="btn-print">
          🖨️ Печать этикетки
        </button>
      </div>
    </div>
  );
}

export default BatchLabelPrint;
```

---

## CSS для этикетки

```css
/* BatchLabel.css */

.label-container {
  padding: 20px;
}

.batch-label {
  width: 80mm;
  height: auto;
  border: 2px solid #333;
  border-radius: 8px;
  padding: 10mm;
  background: white;
  font-family: Arial, sans-serif;
}

.label-header h2 {
  margin: 0 0 10px 0;
  font-size: 18px;
  font-weight: bold;
  text-align: center;
  border-bottom: 2px solid #333;
  padding-bottom: 5px;
}

.label-info {
  margin: 10px 0;
  font-size: 14px;
}

.label-barcode {
  display: flex;
  justify-content: center;
  margin: 15px 0;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
}

.label-details {
  margin: 10px 0;
  font-size: 13px;
  border-top: 1px solid #ddd;
  padding-top: 10px;
}

.detail-row {
  margin: 5px 0;
  display: flex;
  justify-content: space-between;
}

.detail-row strong {
  color: #333;
}

.label-footer {
  margin-top: 10px;
  padding-top: 5px;
  border-top: 1px solid #ddd;
  text-align: center;
  color: #666;
}

.print-controls {
  margin-top: 20px;
  text-align: center;
}

.btn-print {
  padding: 12px 24px;
  font-size: 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-print:hover {
  background: #0056b3;
}

/* Стили для печати */
@media print {
  body {
    margin: 0;
    padding: 0;
  }

  .print-controls {
    display: none; /* Скрыть кнопку при печати */
  }

  .label-container {
    padding: 0;
  }

  .batch-label {
    border: none;
    width: 80mm;
    margin: 0;
  }

  /* Разрыв страницы после каждой этикетки */
  .batch-label {
    page-break-after: always;
  }
}
```

---

## Массовая печать этикеток

Если нужно напечатать этикетки для нескольких партий:

```jsx
import React, { useState } from 'react';
import Barcode from 'react-barcode';

function BatchLabelsBulkPrint({ batches }) {
  const handlePrint = () => {
    window.print();
  };

  return (
    <div>
      <div className="print-controls">
        <button onClick={handlePrint}>
          🖨️ Печать всех этикеток ({batches.length} шт)
        </button>
      </div>

      <div className="labels-grid">
        {batches.map(batch => (
          <div key={batch.id} className="batch-label">
            <h2>{batch.product_name}</h2>
            <p>Партия: {batch.batch_number}</p>

            <Barcode
              value={batch.barcode}
              format="CODE128"
              width={2}
              height={50}
            />

            {batch.expiry_date && <p>Срок: {batch.expiry_date}</p>}
            <p>Кол-во: {batch.quantity}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default BatchLabelsBulkPrint;
```

---

## Сканирование штрихкода

Для сканирования штрихкодов партий можно использовать:

### 1. **react-qr-barcode-scanner**

```bash
npm install react-qr-barcode-scanner
```

```jsx
import React, { useState } from 'react';
import { Scanner } from 'react-qr-barcode-scanner';

function BatchScanner() {
  const [scannedBatch, setScannedBatch] = useState(null);

  const handleScan = (data) => {
    if (data && data.startsWith('BATCH-')) {
      // Найти партию по штрихкоду
      const token = localStorage.getItem('access_token');
      const tenantKey = localStorage.getItem('tenant_key');

      fetch(`http://localhost:8000/api/products/batches/?barcode=${data}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-Key': tenantKey
        }
      })
        .then(r => r.json())
        .then(result => {
          if (result.results && result.results.length > 0) {
            setScannedBatch(result.results[0]);
            alert(`Партия найдена: ${result.results[0].product_name}`);
          } else {
            alert('Партия не найдена');
          }
        });
    }
  };

  return (
    <div>
      <h2>Сканирование партии</h2>

      <Scanner
        onScan={handleScan}
        onError={(err) => console.error(err)}
      />

      {scannedBatch && (
        <div className="scanned-info">
          <h3>Отсканированная партия:</h3>
          <p><strong>Товар:</strong> {scannedBatch.product_name}</p>
          <p><strong>Партия:</strong> {scannedBatch.batch_number}</p>
          <p><strong>Штрихкод:</strong> {scannedBatch.barcode}</p>
          <p><strong>Остаток:</strong> {scannedBatch.quantity}</p>
        </div>
      )}
    </div>
  );
}

export default BatchScanner;
```

### 2. Поиск партии по штрихкоду через API

```javascript
async function findBatchByBarcode(barcode) {
  const token = localStorage.getItem('access_token');
  const tenantKey = localStorage.getItem('tenant_key');

  const response = await fetch(
    `http://localhost:8000/api/products/batches/?barcode=${barcode}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-Key': tenantKey
      }
    }
  );

  const data = await response.json();

  if (data.results && data.results.length > 0) {
    return data.results[0];
  }

  return null;
}

// Использование:
const batch = await findBatchByBarcode('BATCH-20241215103045-A3F4B2C1');
if (batch) {
  console.log('Партия найдена:', batch.product_name);
}
```

---

## Форматы штрихкодов

Для штрихкодов партий используйте формат **CODE128**:

```jsx
<Barcode
  value={batch.barcode}
  format="CODE128"  // ⭐ Рекомендуется
  width={2}
  height={60}
/>
```

**Почему CODE128?**
- ✅ Поддерживает буквы и цифры
- ✅ Компактный
- ✅ Поддерживается всеми сканерами
- ✅ Высокая плотность данных

---

## Примеры использования

### 1. Печать этикетки при создании товара

```jsx
function ProductCreatedSuccess({ product }) {
  const firstBatch = product.batches[0];

  return (
    <div>
      <h2>✅ Товар создан!</h2>
      <p>Товар: {product.name}</p>
      <p>Партия: {firstBatch.batch_number}</p>

      {/* Показываем штрихкод сразу */}
      <div className="label-preview">
        <h3>Этикетка партии:</h3>
        <Barcode value={firstBatch.barcode} />

        <button onClick={() => window.print()}>
          🖨️ Печать этикетки
        </button>
      </div>
    </div>
  );
}
```

### 2. Список партий с кнопками печати

```jsx
function BatchList({ batches }) {
  const printLabel = (batchId) => {
    window.open(`/batches/${batchId}/print`, '_blank');
  };

  return (
    <table>
      <thead>
        <tr>
          <th>Товар</th>
          <th>Партия</th>
          <th>Штрихкод</th>
          <th>Действия</th>
        </tr>
      </thead>
      <tbody>
        {batches.map(batch => (
          <tr key={batch.id}>
            <td>{batch.product_name}</td>
            <td>{batch.batch_number}</td>
            <td>
              <Barcode
                value={batch.barcode}
                width={1}
                height={30}
                displayValue={false}
              />
              <small>{batch.barcode}</small>
            </td>
            <td>
              <button onClick={() => printLabel(batch.id)}>
                🖨️ Печать
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

## Итого

✅ **Штрихкоды генерируются автоматически** на бэкенде
✅ **Формат CODE128** подходит для любых сканеров
✅ **react-barcode** - простая библиотека для генерации
✅ **Готовые компоненты** для печати этикеток
✅ **Поддержка массовой печати**

**Штрихкоды партий готовы к использованию!** 🚀
