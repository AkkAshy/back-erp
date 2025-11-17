#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY4NTQ1NTg4LCJpYXQiOjE3NjMzNjE1ODgsImp0aSI6IjNjZDE2NjRhYzUzZjQ3ZGVhNGMyYjdmNGI3MzMzZGRkIiwidXNlcl9pZCI6MX0.2YwYnrgy5tLKaFZ0UGNPo4b07VboUwSRkZlEL0Ntwp4"

# Единицы измерения
curl -X POST http://localhost:8000/api/products/units/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Штука", "short_name": "шт", "description": "Поштучный учет"}'

curl -X POST http://localhost:8000/api/products/units/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Килограмм", "short_name": "кг", "description": "Единица массы"}'

curl -X POST http://localhost:8000/api/products/units/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Грамм", "short_name": "г", "description": "Единица массы"}'

curl -X POST http://localhost:8000/api/products/units/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Литр", "short_name": "л", "description": "Единица объема"}'

curl -X POST http://localhost:8000/api/products/units/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Миллилитр", "short_name": "мл", "description": "Единица объема"}'

curl -X POST http://localhost:8000/api/products/units/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Метр", "short_name": "м", "description": "Единица длины"}'

curl -X POST http://localhost:8000/api/products/units/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Упаковка", "short_name": "уп", "description": "Упаковка товара"}'

echo ""
echo "✓ Единицы измерения созданы!"

# Категории
curl -X POST http://localhost:8000/api/products/categories/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Одежда", "description": "Одежда и текстиль"}'

curl -X POST http://localhost:8000/api/products/categories/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Обувь", "description": "Обувь всех видов"}'

curl -X POST http://localhost:8000/api/products/categories/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Аксессуары", "description": "Аксессуары и украшения"}'

curl -X POST http://localhost:8000/api/products/categories/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Электроника", "description": "Электронные товары"}'

curl -X POST http://localhost:8000/api/products/categories/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Продукты питания", "description": "Продукты и напитки"}'

curl -X POST http://localhost:8000/api/products/categories/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Косметика", "description": "Косметика и парфюмерия"}'

curl -X POST http://localhost:8000/api/products/categories/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Спорт", "description": "Спортивные товары"}'

curl -X POST http://localhost:8000/api/products/categories/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Дом и сад", "description": "Товары для дома и сада"}'

echo ""
echo "✓ Категории созданы!"
