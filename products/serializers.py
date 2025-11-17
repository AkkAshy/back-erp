"""
Serializers для products app.
"""

from rest_framework import serializers
from products.models import (
    Unit, Category, Attribute, AttributeValue,
    Product, ProductPricing, ProductInventory, ProductBatch,
    ProductAttribute, ProductImage, Supplier, ProductBarcode,
    ProductTag, StockReservation
)


class UnitSerializer(serializers.ModelSerializer):
    """Сериализатор для единиц измерения"""

    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = ['id', 'name', 'short_name', 'description', 'is_active', 'created_at', 'display_name']
        read_only_fields = ['id', 'created_at', 'display_name']

    def get_display_name(self, obj):
        """Возвращает отображаемое имя: 'штука (шт)'"""
        return f"{obj.name} ({obj.short_name})"


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий"""

    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'parent_name',
            'image', 'order', 'is_active', 'created_at', 'updated_at',
            'children_count', 'products_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'slug': {'required': False}  # Делаем slug опциональным, будем генерировать автоматически
        }

    def create(self, validated_data):
        """Автоматически генерируем slug из name если не передан"""
        if 'slug' not in validated_data or not validated_data['slug']:
            from products.utils import slugify
            import uuid

            base_slug = slugify(validated_data['name'])
            slug = base_slug

            # Проверяем уникальность slug
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
                counter += 1

            validated_data['slug'] = slug
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Автоматически обновляем slug если изменилось name"""
        if 'name' in validated_data and ('slug' not in validated_data or not validated_data['slug']):
            from products.utils import slugify
            import uuid

            base_slug = slugify(validated_data['name'])
            slug = base_slug

            # Проверяем уникальность slug (исключая текущий объект)
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
                slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
                counter += 1

            validated_data['slug'] = slug
        return super().update(instance, validated_data)

    def get_children_count(self, obj):
        return obj.children.count()

    def get_products_count(self, obj):
        return obj.products.count()


class AttributeValueSerializer(serializers.ModelSerializer):
    """Сериализатор для значений атрибутов"""

    class Meta:
        model = AttributeValue
        fields = ['id', 'attribute', 'value', 'order', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class AttributeSerializer(serializers.ModelSerializer):
    """Сериализатор для атрибутов"""

    values = AttributeValueSerializer(many=True, read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Attribute
        fields = [
            'id', 'name', 'slug', 'type', 'type_display', 'description',
            'is_required', 'is_filterable', 'order', 'is_active',
            'created_at', 'values'
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'slug': {'required': False}  # Делаем slug опциональным
        }

    def create(self, validated_data):
        """Автоматически генерируем slug из name если не передан"""
        if 'slug' not in validated_data or not validated_data['slug']:
            from products.utils import slugify
            import uuid

            base_slug = slugify(validated_data['name'])
            slug = base_slug

            # Проверяем уникальность slug
            counter = 1
            while Attribute.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
                counter += 1

            validated_data['slug'] = slug
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Автоматически обновляем slug если изменилось name"""
        if 'name' in validated_data and ('slug' not in validated_data or not validated_data['slug']):
            from products.utils import slugify
            import uuid

            base_slug = slugify(validated_data['name'])
            slug = base_slug

            # Проверяем уникальность slug (исключая текущий объект)
            counter = 1
            while Attribute.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
                slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
                counter += 1

            validated_data['slug'] = slug
        return super().update(instance, validated_data)


class ProductImageSerializer(serializers.ModelSerializer):
    """Сериализатор для изображений товара"""

    class Meta:
        model = ProductImage
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class ProductPricingSerializer(serializers.ModelSerializer):
    """Сериализатор для цен товара"""

    margin = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    profit = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ProductPricing
        fields = [
            'id', 'product', 'cost_price', 'sale_price',
            'wholesale_price', 'tax_rate', 'margin', 'profit', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']

    def validate(self, data):
        """Валидация цен"""
        cost_price = data.get('cost_price', 0)
        sale_price = data.get('sale_price', 0)

        if cost_price and sale_price and sale_price < cost_price:
            raise serializers.ValidationError({
                'sale_price': 'Цена продажи не может быть меньше себестоимости'
            })

        return data


class ProductInventorySerializer(serializers.ModelSerializer):
    """Сериализатор для настроек учёта товара"""

    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    stock_status = serializers.CharField(read_only=True)

    class Meta:
        model = ProductInventory
        fields = [
            'id', 'product', 'quantity', 'min_quantity', 'max_quantity',
            'track_inventory', 'is_low_stock', 'stock_status', 'updated_at'
        ]
        read_only_fields = ['id', 'quantity', 'updated_at']


class ProductBatchSerializer(serializers.ModelSerializer):
    """Сериализатор для партий товара"""

    product_name = serializers.CharField(source='product.name', read_only=True)
    supplier_info = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)
    is_expired = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    is_near_expiry = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProductBatch
        fields = [
            'id', 'product', 'product_name', 'batch_number', 'barcode', 'quantity',
            'purchase_price', 'manufacturing_date', 'expiry_date',
            'supplier', 'supplier_info', 'supplier_name', 'notes', 'is_active',
            'is_expired', 'days_until_expiry', 'is_near_expiry',
            'received_at', 'updated_at'
        ]
        read_only_fields = ['id', 'barcode', 'received_at', 'updated_at']

    def validate(self, data):
        """Валидация партии"""
        manufacturing_date = data.get('manufacturing_date')
        expiry_date = data.get('expiry_date')

        if manufacturing_date and expiry_date and manufacturing_date >= expiry_date:
            raise serializers.ValidationError({
                'expiry_date': 'Срок годности должен быть позже даты производства'
            })

        return data


class ProductAttributeSerializer(serializers.ModelSerializer):
    """Сериализатор для атрибутов товара"""

    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    attribute_type = serializers.CharField(source='attribute.type', read_only=True)
    value = serializers.SerializerMethodField()

    class Meta:
        model = ProductAttribute
        fields = [
            'id', 'attribute', 'attribute_name', 'attribute_type',
            'value_text', 'value_number', 'value_boolean', 'value_option',
            'value', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_value(self, obj):
        """Возвращает отображаемое значение атрибута"""
        return obj.get_value()


class ProductListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка товаров (краткая информация)"""

    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_name = serializers.CharField(source='unit.short_name', read_only=True)

    # Поля из pricing
    sale_price = serializers.DecimalField(source='pricing.sale_price', max_digits=12, decimal_places=2, read_only=True)
    cost_price = serializers.DecimalField(source='pricing.cost_price', max_digits=12, decimal_places=2, read_only=True)
    margin = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    # Поля из inventory
    quantity = serializers.DecimalField(source='inventory.quantity', max_digits=12, decimal_places=3, read_only=True)
    stock_status = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'barcode',
            'category', 'category_name',
            'unit', 'unit_name',
            'sale_price', 'cost_price', 'margin',
            'quantity', 'stock_status',
            'main_image', 'is_active', 'is_featured',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о товаре"""

    category_name = serializers.CharField(source='category.name', read_only=True)
    category_path = serializers.CharField(source='category.full_path', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    unit_short = serializers.CharField(source='unit.short_name', read_only=True)

    # Связанные данные
    pricing = ProductPricingSerializer(read_only=True)
    inventory = ProductInventorySerializer(read_only=True)
    batches = ProductBatchSerializer(many=True, read_only=True)
    attributes = ProductAttributeSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    # Вычисляемые поля
    stock_status = serializers.CharField(read_only=True)
    margin = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    profit = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'category', 'category_name', 'category_path',
            'sku', 'barcode', 'unit', 'unit_name', 'unit_short',
            'main_image', 'weight', 'volume',
            'is_active', 'is_featured',
            'pricing', 'inventory', 'batches', 'attributes', 'images',
            'stock_status', 'margin', 'profit', 'is_low_stock',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductCreateSerializer(serializers.ModelSerializer):
    """
    Полное создание товара в одном запросе!

    Создаёт сразу:
    - Product (основная информация)
    - ProductPricing (цены)
    - ProductInventory (настройки учёта)
    - ProductBatch (первая партия с количеством)
    - ProductBarcode (штрихкод если указан)

    Владелец заполняет одну форму и товар готов к продаже!
    """

    # ===== ОСНОВНАЯ ИНФОРМАЦИЯ =====
    name = serializers.CharField(
        max_length=255,
        help_text="Название товара"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Описание товара"
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        help_text="Категория товара"
    )
    unit = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(),
        help_text="Единица измерения"
    )

    # ===== ЦЕНЫ =====
    cost_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Себестоимость (закупочная цена)"
    )
    sale_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Цена продажи"
    )
    wholesale_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Оптовая цена"
    )
    tax_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        required=False,
        help_text="Налоговая ставка (%)"
    )

    # ===== КОЛИЧЕСТВО (первая партия) =====
    initial_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        help_text="Начальное количество (первая партия)"
    )

    # ===== НАСТРОЙКИ УЧЁТА =====
    min_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        required=False,
        help_text="Минимальный остаток (для уведомлений)"
    )
    max_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        required=False,
        allow_null=True,
        help_text="Максимальный остаток"
    )
    track_inventory = serializers.BooleanField(
        default=True,
        required=False,
        help_text="Вести учёт остатков"
    )

    # ===== ПЕРВАЯ ПАРТИЯ (опционально) =====
    batch_number = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Номер партии (если пусто - генерируется)"
    )
    expiry_date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Срок годности партии"
    )
    supplier = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        required=False,
        allow_null=True,
        help_text="Поставщик"
    )

    # ===== ДОПОЛНИТЕЛЬНО =====
    weight = serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        required=False,
        allow_null=True,
        help_text="Вес (кг)"
    )
    volume = serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        required=False,
        allow_null=True,
        help_text="Объём (л)"
    )
    is_featured = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Популярный товар"
    )

    class Meta:
        model = Product
        fields = [
            # Основная информация
            'name', 'description', 'category', 'unit',
            # Цены
            'cost_price', 'sale_price', 'wholesale_price', 'tax_rate',
            # Количество
            'initial_quantity',
            # Настройки учёта
            'min_quantity', 'max_quantity', 'track_inventory',
            # Партия
            'batch_number', 'expiry_date', 'supplier',
            # Дополнительно
            'weight', 'volume', 'is_featured'
        ]

    def validate(self, data):
        """
        Валидация всех данных.

        Автоматически генерирует:
        - SKU (артикул)
        - Barcode (штрихкод)
        - Slug (для URL)
        """
        from products.utils import slugify
        import uuid
        from django.utils import timezone

        # Валидация цен
        cost_price = data.get('cost_price', 0)
        sale_price = data.get('sale_price', 0)

        if cost_price and sale_price and sale_price < cost_price:
            raise serializers.ValidationError({
                'sale_price': 'Цена продажи не может быть меньше себестоимости'
            })

        # ===== АВТОМАТИЧЕСКАЯ ГЕНЕРАЦИЯ SKU =====
        # Формат: {НАЗВАНИЕ}_{TIMESTAMP}_{UUID}
        # Пример: FUTBOLKA_20231117_A1B2C3D4
        base_sku = slugify(data['name'])[:15].replace('-', '_')
        timestamp = timezone.now().strftime('%Y%m%d')
        unique_id = uuid.uuid4().hex[:8]
        sku = f"{base_sku}_{timestamp}_{unique_id}".upper()

        # Гарантируем уникальность SKU (на всякий случай)
        counter = 1
        original_sku = sku
        while Product.objects.filter(sku=sku).exists():
            sku = f"{original_sku}_{counter}"
            counter += 1

        data['sku'] = sku

        # ===== АВТОМАТИЧЕСКАЯ ГЕНЕРАЦИЯ BARCODE =====
        # Формат: EAN-13 совместимый (13 цифр)
        # Используем текущее время + случайные цифры
        timestamp_part = timezone.now().strftime('%y%m%d%H%M')  # 10 цифр
        random_part = str(uuid.uuid4().int)[:3]  # 3 случайные цифры
        barcode = f"{timestamp_part}{random_part}"  # Итого 13 цифр

        # Гарантируем уникальность barcode
        counter = 1
        while Product.objects.filter(barcode=barcode).exists():
            random_part = str(uuid.uuid4().int)[:3]
            barcode = f"{timestamp_part}{random_part}"
            counter += 1
            if counter > 100:  # Защита от бесконечного цикла
                barcode = str(uuid.uuid4().int)[:13]
                break

        data['barcode'] = barcode

        # ===== ГЕНЕРАЦИЯ SLUG =====
        base_slug = slugify(data['name'])
        slug = base_slug

        # Проверяем уникальность slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
            counter += 1

        data['slug'] = slug

        return data

    def create(self, validated_data):
        """
        Создание товара со ВСЕМИ данными в одной транзакции.

        Создаёт:
        - Product
        - ProductPricing
        - ProductInventory
        - ProductBatch (первая партия)
        - ProductBarcode (если указан)
        """
        from django.db import transaction
        from django.utils import timezone
        import uuid

        # Извлекаем данные для разных моделей
        pricing_data = {
            'cost_price': validated_data.pop('cost_price'),
            'sale_price': validated_data.pop('sale_price'),
            'wholesale_price': validated_data.pop('wholesale_price', None),
            'tax_rate': validated_data.pop('tax_rate', 0),
        }

        inventory_data = {
            'min_quantity': validated_data.pop('min_quantity', 0),
            'max_quantity': validated_data.pop('max_quantity', None),
            'track_inventory': validated_data.pop('track_inventory', True),
        }

        batch_data = {
            'quantity': validated_data.pop('initial_quantity'),
            'batch_number': validated_data.pop('batch_number', ''),
            'expiry_date': validated_data.pop('expiry_date', None),
            'supplier': validated_data.pop('supplier', None),
            'purchase_price': pricing_data['cost_price'],  # Закупочная цена = себестоимость
        }

        # Генерация номера партии если не указан
        if not batch_data['batch_number']:
            batch_data['batch_number'] = f"BATCH-{uuid.uuid4().hex[:8].upper()}"

        barcode = validated_data.pop('barcode', '')

        with transaction.atomic():
            # 1. Создаём Product
            product = Product.objects.create(**validated_data)

            # 2. Создаём ProductPricing
            ProductPricing.objects.create(product=product, **pricing_data)

            # 3. Создаём ProductInventory (изначально quantity=0)
            ProductInventory.objects.create(product=product, **inventory_data)

            # 4. Создаём первую партию (она автоматически обновит quantity через сигнал)
            ProductBatch.objects.create(
                product=product,
                **batch_data,
                is_active=True,
                received_at=timezone.now()
            )

            # 5. Создаём ProductBarcode если указан
            if barcode:
                ProductBarcode.objects.create(
                    product=product,
                    barcode=barcode,
                    is_primary=True
                )

        return product


class ProductUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления товара (без изменения количества)"""

    # Поля для pricing
    cost_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    sale_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    wholesale_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)

    # Поля для inventory
    min_quantity = serializers.DecimalField(max_digits=12, decimal_places=3, required=False)
    max_quantity = serializers.DecimalField(max_digits=12, decimal_places=3, required=False, allow_null=True)
    track_inventory = serializers.BooleanField(required=False)

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'sku', 'barcode', 'unit',
            'weight', 'volume', 'is_active', 'is_featured',
            # Pricing
            'cost_price', 'sale_price', 'wholesale_price', 'tax_rate',
            # Inventory settings
            'min_quantity', 'max_quantity', 'track_inventory'
        ]

    def update(self, instance, validated_data):
        """Обновление товара с ценами и настройками учёта"""
        # Извлекаем данные для pricing и inventory
        pricing_data = {}
        inventory_data = {}

        pricing_fields = ['cost_price', 'sale_price', 'wholesale_price', 'tax_rate']
        inventory_fields = ['min_quantity', 'max_quantity', 'track_inventory']

        for field in pricing_fields:
            if field in validated_data:
                pricing_data[field] = validated_data.pop(field)

        for field in inventory_fields:
            if field in validated_data:
                inventory_data[field] = validated_data.pop(field)

        # Обновляем Product
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем ProductPricing
        if pricing_data:
            pricing, created = ProductPricing.objects.get_or_create(product=instance)
            for attr, value in pricing_data.items():
                setattr(pricing, attr, value)
            pricing.save()

        # Обновляем ProductInventory
        if inventory_data:
            inventory, created = ProductInventory.objects.get_or_create(product=instance)
            for attr, value in inventory_data.items():
                setattr(inventory, attr, value)
            inventory.save()

        return instance


class SupplierSerializer(serializers.ModelSerializer):
    """Сериализатор для поставщиков"""

    batches_count = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'code', 'contact_person', 'email', 'phone',
            'address', 'website', 'payment_terms', 'delivery_time',
            'min_order_amount', 'rating', 'is_active', 'notes',
            'batches_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_batches_count(self, obj):
        """Количество партий от этого поставщика"""
        return obj.batches.count()


class ProductBarcodeSerializer(serializers.ModelSerializer):
    """Сериализатор для штрих-кодов товаров"""

    product_name = serializers.CharField(source='product.name', read_only=True)
    barcode_type_display = serializers.CharField(source='get_barcode_type_display', read_only=True)

    class Meta:
        model = ProductBarcode
        fields = [
            'id', 'product', 'product_name', 'barcode', 'barcode_type',
            'barcode_type_display', 'is_primary', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_barcode(self, value):
        """Проверка уникальности штрих-кода"""
        instance = self.instance
        if instance and instance.barcode == value:
            return value

        if ProductBarcode.objects.filter(barcode=value).exists():
            raise serializers.ValidationError("Штрих-код уже используется другим товаром")
        return value


class ProductTagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов товаров"""

    products_count = serializers.SerializerMethodField()

    class Meta:
        model = ProductTag
        fields = [
            'id', 'name', 'slug', 'color', 'icon', 'description',
            'is_active', 'order', 'products_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_products_count(self, obj):
        """Количество товаров с этим тегом"""
        # Будет работать после добавления M2M поля
        return 0  # obj.products.count()


class StockReservationSerializer(serializers.ModelSerializer):
    """Сериализатор для резервирования товаров"""

    product_name = serializers.CharField(source='product.name', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = StockReservation
        fields = [
            'id', 'product', 'product_name', 'batch', 'batch_number',
            'quantity', 'order_id', 'order_reference', 'status',
            'status_display', 'reserved_until', 'notes', 'created_by',
            'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """Валидация резервирования"""
        product = data.get('product')
        batch = data.get('batch')
        quantity = data.get('quantity', 0)

        # Проверка что партия принадлежит товару
        if batch and batch.product != product:
            raise serializers.ValidationError({
                'batch': 'Партия не принадлежит указанному товару'
            })

        # Проверка доступного количества в партии
        if batch:
            # Получаем сумму активных резервов для этой партии
            from django.db.models import Sum
            reserved = StockReservation.objects.filter(
                batch=batch,
                status='active'
            ).aggregate(total=Sum('quantity'))['total'] or 0

            available = batch.quantity - reserved
            if quantity > available:
                raise serializers.ValidationError({
                    'quantity': f'Недостаточно товара в партии. Доступно: {available}'
                })

        return data
