"""
ViewSets для products app.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.db.models import Q, F

from products.models import (
    Unit, Category, Attribute, AttributeValue, CategoryAttribute,
    Product, ProductBatch, ProductAttribute, ProductImage,
    Supplier, ProductBarcode, ProductTag, StockReservation
)
from products.serializers import (
    UnitSerializer, CategorySerializer, AttributeSerializer,
    AttributeValueSerializer, CategoryAttributeSerializer, CategoryAttributeDetailSerializer,
    ProductListSerializer, ProductDetailSerializer,
    ProductCreateSerializer, ProductUpdateSerializer, ProductBatchSerializer,
    ProductAttributeSerializer, ProductImageSerializer,
    SupplierSerializer, ProductBarcodeSerializer, ProductTagSerializer,
    StockReservationSerializer
)
from core.permissions import IsTenantUser


class UnitViewSet(viewsets.ModelViewSet):
    """ViewSet для единиц измерения"""

    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'short_name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Фильтр по активности
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet для категорий товаров"""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'order', 'created_at']
    ordering = ['order', 'name']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтр только корневых категорий
        root_only = self.request.query_params.get('root_only')
        if root_only and root_only.lower() == 'true':
            queryset = queryset.filter(parent__isnull=True)

        return queryset

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Получить дочерние категории"""
        category = self.get_object()
        children = category.children.filter(is_active=True)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Получить товары категории"""
        from products.serializers import ProductListSerializer

        category = self.get_object()
        products = category.products.filter(is_active=True)

        # Пагинация
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class AttributeViewSet(viewsets.ModelViewSet):
    """ViewSet для атрибутов товаров"""

    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'is_required', 'is_filterable', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'order', 'created_at']
    ordering = ['order', 'name']


class AttributeValueViewSet(viewsets.ModelViewSet):
    """ViewSet для значений атрибутов"""

    queryset = AttributeValue.objects.all()
    serializer_class = AttributeValueSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['attribute', 'is_active']
    search_fields = ['value']
    ordering_fields = ['value', 'order', 'created_at']
    ordering = ['order', 'value']


class CategoryAttributeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для привязки атрибутов к категориям.

    Позволяет:
    - Просматривать какие атрибуты привязаны к категории
    - Добавлять новые атрибуты к категории
    - Удалять привязки атрибутов
    - Обновлять настройки (is_required, is_variant, order)
    """

    queryset = CategoryAttribute.objects.all()
    serializer_class = CategoryAttributeSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category', 'attribute', 'is_required', 'is_variant']
    ordering_fields = ['order', 'created_at']
    ordering = ['order', 'attribute__name']

    def get_queryset(self):
        """Оптимизация запросов"""
        return super().get_queryset().select_related('category', 'attribute')

    def get_serializer_class(self):
        """Использовать детальный сериализатор для retrieve"""
        if self.action == 'retrieve':
            return CategoryAttributeDetailSerializer
        return CategoryAttributeSerializer

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Получить все атрибуты категории с полными данными.

        Query params:
        - category_id: ID категории (обязательный)

        Пример: GET /api/products/category-attributes/by_category/?category_id=5
        """
        category_id = request.query_params.get('category_id')

        if not category_id:
            return Response(
                {'error': 'Параметр category_id обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем все привязанные атрибуты с полными данными
        category_attrs = self.get_queryset().filter(
            category_id=category_id
        ).select_related('attribute').prefetch_related('attribute__values')

        serializer = CategoryAttributeDetailSerializer(category_attrs, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Массовое добавление атрибутов к категории.

        Body:
        {
            "category": 5,
            "attributes": [
                {"attribute": 1, "is_required": true, "is_variant": false, "order": 0},
                {"attribute": 2, "is_required": false, "is_variant": true, "order": 1}
            ]
        }
        """
        category_id = request.data.get('category')
        attributes_data = request.data.get('attributes', [])

        if not category_id:
            return Response(
                {'error': 'Поле category обязательно'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not attributes_data:
            return Response(
                {'error': 'Поле attributes обязательно и не должно быть пустым'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаём привязки
        created_items = []
        errors = []

        for attr_data in attributes_data:
            attr_data['category'] = category_id
            serializer = self.get_serializer(data=attr_data)

            if serializer.is_valid():
                serializer.save()
                created_items.append(serializer.data)
            else:
                errors.append({
                    'attribute': attr_data.get('attribute'),
                    'errors': serializer.errors
                })

        if errors:
            return Response(
                {
                    'status': 'partial_success',
                    'message': 'Некоторые атрибуты не были добавлены',
                    'created': created_items,
                    'errors': errors
                },
                status=status.HTTP_207_MULTI_STATUS
            )

        return Response(
            {
                'status': 'success',
                'message': f'Добавлено атрибутов: {len(created_items)}',
                'data': created_items
            },
            status=status.HTTP_201_CREATED
        )


class ProductImageViewSet(viewsets.ModelViewSet):
    """ViewSet для изображений товаров"""

    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']


class ProductBatchViewSet(viewsets.ModelViewSet):
    """ViewSet для партий товаров"""

    queryset = ProductBatch.objects.select_related('product').all()
    serializer_class = ProductBatchSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product', 'is_active']
    search_fields = ['batch_number', 'supplier_name']
    ordering_fields = ['received_at', 'expiry_date', 'quantity']
    ordering = ['expiry_date', 'received_at']  # FEFO по умолчанию

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтр по истёкшим партиям
        expired = self.request.query_params.get('expired')
        if expired is not None:
            from django.utils import timezone
            if expired.lower() == 'true':
                queryset = queryset.filter(expiry_date__lt=timezone.now().date())
            else:
                queryset = queryset.filter(
                    models.Q(expiry_date__isnull=True) | models.Q(expiry_date__gte=timezone.now().date())
                )

        # Фильтр по скоро истекающим партиям (по умолчанию 30 дней)
        near_expiry = self.request.query_params.get('near_expiry')
        if near_expiry is not None:
            from django.utils import timezone
            from datetime import timedelta

            days = int(self.request.query_params.get('days', 30))
            future_date = timezone.now().date() + timedelta(days=days)

            queryset = queryset.filter(
                expiry_date__gte=timezone.now().date(),
                expiry_date__lte=future_date
            )

        return queryset

    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Получить истёкшие партии"""
        from django.utils import timezone

        batches = self.get_queryset().filter(
            expiry_date__lt=timezone.now().date(),
            is_active=True
        )

        page = self.paginate_queryset(batches)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(batches, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def near_expiry(self, request):
        """Получить партии с истекающим сроком годности"""
        from django.utils import timezone
        from datetime import timedelta

        days = int(request.query_params.get('days', 30))
        future_date = timezone.now().date() + timedelta(days=days)

        batches = self.get_queryset().filter(
            expiry_date__gte=timezone.now().date(),
            expiry_date__lte=future_date,
            is_active=True
        )

        page = self.paginate_queryset(batches)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(batches, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet для товаров"""

    queryset = Product.objects.select_related(
        'category', 'unit', 'pricing', 'inventory'
    ).prefetch_related('attributes', 'images')

    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'unit', 'is_active', 'is_featured']
    search_fields = ['name', 'description', 'sku', 'barcode']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'create':
            return ProductCreateSerializer  # Полное создание в одном запросе
        elif self.action in ['update', 'partial_update']:
            return ProductUpdateSerializer  # Обновление без изменения количества
        return ProductDetailSerializer

    def create(self, request, *args, **kwargs):
        """Создание товара с использованием ProductCreateSerializer для входа и ProductDetailSerializer для ответа"""
        # Используем ProductCreateSerializer для валидации и создания
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        # Используем ProductDetailSerializer для ответа
        response_serializer = ProductDetailSerializer(product)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтр по статусу остатков (используем inventory)
        stock_status = self.request.query_params.get('stock_status')
        if stock_status == 'in_stock':
            queryset = queryset.filter(inventory__quantity__gt=0, inventory__track_inventory=True)
        elif stock_status == 'out_of_stock':
            queryset = queryset.filter(inventory__quantity=0, inventory__track_inventory=True)
        elif stock_status == 'low_stock':
            queryset = queryset.filter(
                inventory__track_inventory=True,
                inventory__quantity__gt=0,
                inventory__quantity__lte=F('inventory__min_quantity')
            )
        elif stock_status == 'unlimited':
            queryset = queryset.filter(inventory__track_inventory=False)

        # Фильтр по диапазону цен (используем pricing)
        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(pricing__sale_price__gte=min_price)

        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(pricing__sale_price__lte=max_price)

        # Фильтр по наличию изображений
        has_images = self.request.query_params.get('has_images')
        if has_images is not None:
            if has_images.lower() == 'true':
                queryset = queryset.filter(main_image__isnull=False)
            else:
                queryset = queryset.filter(main_image__isnull=True)

        return queryset

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Получить товары с низким остатком"""
        import logging
        logger = logging.getLogger(__name__)

        # Логируем параметры запроса
        min_quantity_param = request.query_params.get('min_quantity')
        logger.info(f"low_stock called with min_quantity_param: {min_quantity_param}")

        # Базовый queryset
        base_queryset = self.get_queryset()
        logger.info(f"Base queryset count: {base_queryset.count()}")

        # Фильтр товаров с inventory
        products_with_inventory = base_queryset.filter(inventory__isnull=False)
        logger.info(f"Products with inventory count: {products_with_inventory.count()}")

        try:
            # Получаем товары с учетом остатков
            products_tracked = products_with_inventory.filter(
                inventory__track_inventory=True
            ).select_related('inventory').prefetch_related('batches')

            # Фильтруем в Python, так как quantity - это property
            low_stock_products = []

            if min_quantity_param:
                # Используем переданный параметр min_quantity
                min_quantity = float(min_quantity_param)
                for product in products_tracked:
                    qty = product.inventory.quantity
                    if qty is not None and 0 < qty <= min_quantity:
                        low_stock_products.append(product)
                logger.info(f"Filtered by min_quantity={min_quantity}, count: {len(low_stock_products)}")
            else:
                # Используем inventory__min_quantity
                for product in products_tracked:
                    qty = product.inventory.quantity
                    if qty is not None and 0 < qty <= product.inventory.min_quantity:
                        low_stock_products.append(product)
                logger.info(f"Filtered by inventory__min_quantity, count: {len(low_stock_products)}")

            products = low_stock_products

            page = self.paginate_queryset(products)
            if page is not None:
                serializer = ProductListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = ProductListSerializer(products, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error in low_stock: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Получить товары, которых нет в наличии"""
        products = self.get_queryset().filter(
            inventory__track_inventory=True,
            inventory__quantity=0
        )

        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Получить избранные товары"""
        products = self.get_queryset().filter(is_featured=True, is_active=True)

        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='print-label')
    def print_label(self, request, pk=None):
        """
        Получить данные для печати этикетки товара.

        GET /api/products/products/{id}/print-label/

        Возвращает:
        - Название товара
        - Цену продажи
        - Штрих-код (base64 изображение)
        - Артикул (SKU)
        - Единицу измерения

        Query параметры:
        - quantity (int): Количество этикеток для печати (по умолчанию 1)
        """
        import barcode
        from barcode.writer import ImageWriter
        from io import BytesIO
        import base64

        product = self.get_object()
        quantity = int(request.query_params.get('quantity', 1))

        # Проверяем что есть pricing
        if not hasattr(product, 'pricing'):
            return Response({
                'status': 'error',
                'message': 'У товара не указана цена'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Генерируем штрих-код если он есть
        barcode_base64 = None
        if product.barcode:
            try:
                # Определяем тип штрих-кода (EAN13, EAN8, Code128 и т.д.)
                barcode_class = barcode.get_barcode_class('code128')

                # Создаем штрих-код
                barcode_instance = barcode_class(product.barcode, writer=ImageWriter())

                # Сохраняем в BytesIO
                buffer = BytesIO()
                barcode_instance.write(buffer, options={
                    'module_height': 8.0,
                    'module_width': 0.2,
                    'quiet_zone': 6.5,
                    'font_size': 10,
                    'text_distance': 5.0,
                    'write_text': True,
                })

                # Кодируем в base64
                buffer.seek(0)
                barcode_base64 = base64.b64encode(buffer.read()).decode('utf-8')

            except Exception as e:
                # Если не удалось сгенерировать штрих-код, продолжаем без него
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to generate barcode for product {product.id}: {str(e)}")

        # Формируем данные для этикетки
        label_data = {
            'status': 'success',
            'data': {
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'barcode': product.barcode if product.barcode else None,
                    'unit': product.unit.short_name if product.unit else 'шт',
                },
                'price': {
                    'sale_price': float(product.pricing.sale_price),
                    'formatted_price': f"{product.pricing.sale_price:,.2f}",
                    'currency': 'сум'  # Можно сделать настраиваемым
                },
                'barcode_image': f"data:image/png;base64,{barcode_base64}" if barcode_base64 else None,
                'quantity': quantity,
                'generated_at': product.updated_at.isoformat()
            }
        }

        return Response(label_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='scan_barcode')
    def scan_barcode(self, request):
        """
        Найти товар по штрих-коду и опционально добавить в продажу.

        GET /api/products/products/scan_barcode/?barcode=4870123456789&session=1&quantity=1

        Query параметры:
        - barcode (str): Штрих-код товара (обязательный)
        - session (int): ID кассовой смены (опционально)
        - quantity (number): Количество товара (опционально, по умолчанию 1)
        - batch (int): ID партии товара (опционально)

        Если указан session, товар автоматически добавляется в текущую продажу.
        Возвращает информацию о товаре и обновлённую продажу (если добавлено).
        """
        from sales.models import CashierSession, Sale, SaleItem
        from decimal import Decimal

        barcode_value = request.query_params.get('barcode')
        session_id = request.query_params.get('session')
        quantity = request.query_params.get('quantity', '1')
        batch_id = request.query_params.get('batch')

        if not barcode_value:
            return Response({
                'status': 'error',
                'message': 'Не указан штрих-код',
                'code': 'barcode_required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Ищем товар по штрих-коду
        try:
            product = Product.objects.select_related(
                'category', 'unit', 'pricing', 'inventory'
            ).prefetch_related('attributes', 'images').get(
                barcode=barcode_value,
                is_active=True
            )
        except Product.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'Товар с штрих-кодом "{barcode_value}" не найден',
                'code': 'product_not_found',
                'barcode': barcode_value
            }, status=status.HTTP_404_NOT_FOUND)

        response_data = {
            'status': 'success',
            'data': ProductDetailSerializer(product).data
        }

        # Если указана смена, добавляем товар в продажу
        if session_id:
            try:
                quantity = Decimal(str(quantity))
                if quantity <= 0:
                    return Response({
                        'status': 'error',
                        'message': 'Количество должно быть больше 0',
                        'code': 'invalid_quantity'
                    }, status=status.HTTP_400_BAD_REQUEST)

                session = CashierSession.objects.get(id=session_id, status='open')
            except CashierSession.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Смена не найдена или закрыта',
                    'code': 'session_not_found'
                }, status=status.HTTP_404_NOT_FOUND)
            except (ValueError, TypeError):
                return Response({
                    'status': 'error',
                    'message': 'Некорректное значение количества',
                    'code': 'invalid_quantity'
                }, status=status.HTTP_400_BAD_REQUEST)

            batch = None
            if batch_id:
                from products.models import ProductBatch
                try:
                    batch = ProductBatch.objects.get(id=batch_id, product=product)
                except ProductBatch.DoesNotExist:
                    return Response({
                        'status': 'error',
                        'message': 'Партия не найдена',
                        'code': 'batch_not_found'
                    }, status=status.HTTP_404_NOT_FOUND)

            # Ищем текущую незавершённую продажу этой смены
            sale = Sale.objects.filter(
                session=session,
                status='pending'
            ).order_by('-created_at').first()

            # Если нет незавершённой продажи - создаём новую
            if not sale:
                # Генерируем номер чека
                from django.utils import timezone
                receipt_number = f"CHECK-{timezone.now().strftime('%Y%m%d%H%M%S')}"

                sale = Sale.objects.create(
                    session=session,
                    receipt_number=receipt_number,
                    status='pending'
                )

            # Получаем цену товара из pricing
            unit_price = Decimal('0.00')
            if hasattr(product, 'pricing') and product.pricing:
                unit_price = product.pricing.sale_price or product.pricing.cost_price or Decimal('0.00')

            # Добавляем позицию
            sale_item = SaleItem.objects.create(
                sale=sale,
                product=product,
                batch=batch,
                quantity=quantity,
                unit_price=unit_price
            )

            # Пересчитываем суммы
            sale.calculate_totals()

            # Импортируем сериализатор продажи
            from sales.serializers import SaleDetailSerializer
            response_data['sale'] = SaleDetailSerializer(sale).data
            response_data['message'] = 'Товар добавлен в продажу'

        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def add_attribute(self, request, pk=None):
        """Добавить атрибут к товару"""
        product = self.get_object()
        serializer = ProductAttributeSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_image(self, request, pk=None):
        """Добавить изображение к товару"""
        product = self.get_object()
        data = request.data.copy()
        data['product'] = product.id

        serializer = ProductImageSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def update_quantity(self, request, pk=None):
        """Обновить количество товара"""
        product = self.get_object()
        quantity = request.data.get('quantity')

        if quantity is None:
            return Response(
                {'error': 'Количество не указано'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = float(quantity)
            if quantity < 0:
                return Response(
                    {'error': 'Количество не может быть отрицательным'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Обновляем inventory
            if hasattr(product, 'inventory'):
                product.inventory.quantity = quantity
                product.inventory.save()
            else:
                from products.models import ProductInventory
                ProductInventory.objects.create(product=product, quantity=quantity)

            serializer = self.get_serializer(product)
            return Response(serializer.data)

        except (ValueError, TypeError):
            return Response(
                {'error': 'Некорректное значение количества'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['patch'])
    def adjust_quantity(self, request, pk=None):
        """Корректировка количества товара (добавить/убавить)"""
        product = self.get_object()
        adjustment = request.data.get('adjustment')

        if adjustment is None:
            return Response(
                {'error': 'Значение корректировки не указано'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            adjustment = float(adjustment)

            # Получаем текущее количество из inventory
            if not hasattr(product, 'inventory'):
                from products.models import ProductInventory
                ProductInventory.objects.create(product=product, quantity=0)

            new_quantity = product.inventory.quantity + adjustment

            if new_quantity < 0:
                return Response(
                    {'error': 'Результирующее количество не может быть отрицательным'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            product.inventory.quantity = new_quantity
            product.inventory.save()

            serializer = self.get_serializer(product)
            return Response(serializer.data)

        except (ValueError, TypeError):
            return Response(
                {'error': 'Некорректное значение корректировки'},
                status=status.HTTP_400_BAD_REQUEST
            )


class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet для поставщиков"""

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'rating']
    search_fields = ['name', 'code', 'contact_person', 'email', 'phone']
    ordering_fields = ['name', 'rating', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def batches(self, request, pk=None):
        """Получить партии от поставщика"""
        supplier = self.get_object()
        batches = supplier.batches.all()

        # Пагинация
        page = self.paginate_queryset(batches)
        if page is not None:
            serializer = ProductBatchSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProductBatchSerializer(batches, many=True)
        return Response(serializer.data)


class ProductBarcodeViewSet(viewsets.ModelViewSet):
    """ViewSet для штрих-кодов товаров"""

    queryset = ProductBarcode.objects.select_related('product').all()
    serializer_class = ProductBarcodeSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product', 'barcode_type', 'is_primary']
    search_fields = ['barcode', 'product__name', 'product__sku']
    ordering_fields = ['barcode', 'created_at']
    ordering = ['-is_primary', 'barcode']

    @action(detail=False, methods=['get'])
    def search_barcode(self, request):
        """Поиск товара по штрих-коду"""
        barcode = request.query_params.get('barcode')
        if not barcode:
            return Response(
                {'error': 'Не указан штрих-код'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            barcode_obj = ProductBarcode.objects.select_related('product').get(barcode=barcode)
            product_serializer = ProductDetailSerializer(barcode_obj.product)
            return Response({
                'barcode': ProductBarcodeSerializer(barcode_obj).data,
                'product': product_serializer.data
            })
        except ProductBarcode.DoesNotExist:
            return Response(
                {'error': 'Штрих-код не найден'},
                status=status.HTTP_404_NOT_FOUND
            )


class ProductTagViewSet(viewsets.ModelViewSet):
    """ViewSet для тегов товаров"""

    queryset = ProductTag.objects.all()
    serializer_class = ProductTagSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'slug']
    ordering_fields = ['name', 'order', 'created_at']
    ordering = ['order', 'name']


class StockReservationViewSet(viewsets.ModelViewSet):
    """ViewSet для резервирования товаров"""

    queryset = StockReservation.objects.select_related(
        'product', 'batch'
    ).all()
    serializer_class = StockReservationSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product', 'batch', 'status', 'order_id']
    search_fields = ['order_reference', 'product__name', 'notes']
    ordering_fields = ['created_at', 'reserved_until']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        """Освободить резервирование"""
        reservation = self.get_object()
        reservation.release()
        serializer = self.get_serializer(reservation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Завершить резервирование (товар продан)"""
        reservation = self.get_object()
        reservation.complete()
        serializer = self.get_serializer(reservation)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Получить активные резервирования"""
        reservations = self.get_queryset().filter(status='active')

        page = self.paginate_queryset(reservations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(reservations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def cleanup_expired(self, request):
        """Очистить истекшие резервирования"""
        from django.utils import timezone

        expired = self.get_queryset().filter(
            status='active',
            reserved_until__lt=timezone.now()
        )

        count = expired.count()
        expired.update(status='expired')

        return Response({
            'message': f'Освобождено {count} истекших резервирований',
            'count': count
        })
