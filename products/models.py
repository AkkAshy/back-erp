"""
Модели для управления товарами в tenant схеме.

ВАЖНО: Все эти модели находятся в tenant_{slug} схемах, а НЕ в public!
Это означает что каждый магазин имеет свои отдельные товары, категории и атрибуты.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _


class Unit(models.Model):
    """
    Единица измерения товара (шт, кг, л, м и т.д.)

    Примеры:
    - шт (штука)
    - кг (килограмм)
    - л (литр)
    - м (метр)
    - упак (упаковка)
    """

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Название'),
        help_text=_('Например: шт, кг, л, м')
    )

    short_name = models.CharField(
        max_length=10,
        verbose_name=_('Краткое название'),
        help_text=_('Например: шт, кг')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активна')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    class Meta:
        db_table = 'products_unit'
        verbose_name = _('Единица измерения')
        verbose_name_plural = _('Единицы измерения')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.short_name})"


class Category(models.Model):
    """
    Категория товаров с поддержкой вложенности (дерево категорий).

    Примеры:
    - Электроника
      - Телефоны
      - Ноутбуки
    - Одежда
      - Мужская
      - Женская
    """

    name = models.CharField(
        max_length=200,
        verbose_name=_('Название'),
        help_text=_('Название категории')
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly идентификатор')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )

    # Вложенность категорий
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name=_('Родительская категория')
    )

    # Изображение категории
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        verbose_name=_('Изображение')
    )

    # Порядок отображения
    order = models.IntegerField(
        default=0,
        verbose_name=_('Порядок'),
        help_text=_('Чем меньше число, тем выше в списке')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активна')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        db_table = 'products_category'
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    @property
    def full_path(self):
        """Возвращает полный путь категории"""
        if self.parent:
            return f"{self.parent.full_path} → {self.name}"
        return self.name


class Attribute(models.Model):
    """
    Атрибут товара (Цвет, Размер, Материал и т.д.)

    Атрибуты используются для характеристик товаров.
    Например:
    - Цвет: красный, синий, зеленый
    - Размер: S, M, L, XL
    - Материал: хлопок, полиэстер
    """

    TYPE_CHOICES = [
        ('text', _('Текст')),
        ('number', _('Число')),
        ('select', _('Выбор из списка')),
        ('multiselect', _('Множественный выбор')),
        ('boolean', _('Да/Нет')),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Название'),
        help_text=_('Например: Цвет, Размер, Материал')
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_('Slug')
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='text',
        verbose_name=_('Тип атрибута')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )

    # Обязательность атрибута
    is_required = models.BooleanField(
        default=False,
        verbose_name=_('Обязательный'),
        help_text=_('Обязателен ли этот атрибут для товаров')
    )

    # Использовать в фильтрах
    is_filterable = models.BooleanField(
        default=True,
        verbose_name=_('Для фильтрации'),
        help_text=_('Использовать в фильтрах товаров')
    )

    # Порядок отображения
    order = models.IntegerField(
        default=0,
        verbose_name=_('Порядок')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    class Meta:
        db_table = 'products_attribute'
        verbose_name = _('Атрибут')
        verbose_name_plural = _('Атрибуты')
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class AttributeValue(models.Model):
    """
    Значение атрибута (конкретные опции для select/multiselect атрибутов).

    Например для атрибута "Цвет":
    - Красный
    - Синий
    - Зеленый
    """

    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name=_('Атрибут')
    )

    value = models.CharField(
        max_length=200,
        verbose_name=_('Значение'),
        help_text=_('Например: Красный, L, Хлопок')
    )

    # Порядок отображения
    order = models.IntegerField(
        default=0,
        verbose_name=_('Порядок')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    class Meta:
        db_table = 'products_attribute_value'
        verbose_name = _('Значение атрибута')
        verbose_name_plural = _('Значения атрибутов')
        ordering = ['attribute', 'order', 'value']
        unique_together = [['attribute', 'value']]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class Product(models.Model):
    """
    Товар - основная модель продукта (нормализованная версия).

    ВАЖНО: Эта модель находится в tenant схеме, поэтому каждый магазин
    имеет свои отдельные товары.

    Связанные модели:
    - ProductPricing - цены товара (1:1)
    - ProductInventory - остатки товара (1:1)
    """

    # Основная информация
    name = models.CharField(
        max_length=200,
        verbose_name=_('Название'),
        help_text=_('Название товара')
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=_('Slug')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )

    # Категория
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_('Категория')
    )

    # Идентификаторы
    sku = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Артикул'),
        help_text=_('Уникальный артикул товара (SKU)')
    )

    barcode = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name=_('Штрихкод'),
        help_text=_('Штрихкод для сканера')
    )

    # Единица измерения
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_('Единица измерения')
    )

    # Изображения
    main_image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name=_('Главное изображение')
    )

    # Характеристики товара
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('Вес (кг)')
    )

    volume = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('Объём (л)')
    )

    # Статусы
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен'),
        help_text=_('Доступен для продажи')
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name=_('Рекомендуемый'),
        help_text=_('Показывать в рекомендованных')
    )

    # Теги (добавлено позже, поэтому определение модели ProductTag идет ниже)
    # tags = models.ManyToManyField('ProductTag', blank=True, related_name='products')
    # Будет добавлено через миграцию после создания ProductTag

    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        db_table = 'products_product'
        verbose_name = _('Товар')
        verbose_name_plural = _('Товары')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['-created_at']),
        ]

    def save(self, *args, **kwargs):
        """Автоматическая генерация штрихкода если не указан"""
        if not self.barcode:
            import random
            # Генерируем EAN-13 совместимый штрихкод (13 цифр)
            # Формат: 487 (prefix) + 9 случайных цифр + контрольная сумма
            prefix = "487"  # Можно изменить на свой префикс
            random_part = ''.join([str(random.randint(0, 9)) for _ in range(9)])

            # Генерируем штрихкод без контрольной суммы
            barcode_without_check = prefix + random_part

            # Вычисляем контрольную сумму EAN-13
            odd_sum = sum(int(barcode_without_check[i]) for i in range(0, 12, 2))
            even_sum = sum(int(barcode_without_check[i]) for i in range(1, 12, 2))
            total = odd_sum + (even_sum * 3)
            check_digit = (10 - (total % 10)) % 10

            self.barcode = barcode_without_check + str(check_digit)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def margin(self):
        """Рассчитывает наценку в процентах"""
        if hasattr(self, 'pricing') and self.pricing.cost_price > 0:
            return ((self.pricing.sale_price - self.pricing.cost_price) / self.pricing.cost_price) * 100
        return 0

    @property
    def profit(self):
        """Рассчитывает прибыль с единицы товара"""
        if hasattr(self, 'pricing'):
            return self.pricing.sale_price - self.pricing.cost_price
        return 0

    @property
    def is_low_stock(self):
        """Проверяет достиг ли товар минимального остатка"""
        if hasattr(self, 'inventory'):
            return self.inventory.quantity <= self.inventory.min_quantity
        return False

    @property
    def stock_status(self):
        """Возвращает статус остатка"""
        if not hasattr(self, 'inventory'):
            return 'unknown'

        if not self.inventory.track_inventory:
            return 'unlimited'
        if self.inventory.quantity <= 0:
            return 'out_of_stock'
        if self.is_low_stock:
            return 'low_stock'
        return 'in_stock'


class ProductPricing(models.Model):
    """
    Цены товара (отдельная таблица для нормализации).

    Связь 1:1 с Product.
    Позволяет легко работать с ценами без загрузки всей информации о товаре.
    """

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='pricing',
        verbose_name=_('Товар')
    )

    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Себестоимость'),
        help_text=_('Цена закупки')
    )

    sale_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Цена продажи'),
        help_text=_('Розничная цена')
    )

    wholesale_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        verbose_name=_('Оптовая цена'),
        help_text=_('Цена для оптовых покупателей')
    )

    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Ставка НДС (%)'),
        help_text=_('Например: 12, 15, 20')
    )

    # Метаданные
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        db_table = 'products_product_pricing'
        verbose_name = _('Цены товара')
        verbose_name_plural = _('Цены товаров')

    def __str__(self):
        return f"{self.product.name} - {self.sale_price}"

    @property
    def margin(self):
        """Рассчитывает наценку в процентах"""
        if self.cost_price > 0:
            return ((self.sale_price - self.cost_price) / self.cost_price) * 100
        return 0

    @property
    def profit(self):
        """Рассчитывает прибыль с единицы товара"""
        return self.sale_price - self.cost_price


class ProductInventory(models.Model):
    """
    Настройки учёта остатков товара.

    Связь 1:1 с Product.
    Хранит только настройки учёта, а фактические остатки находятся в партиях (ProductBatch).
    """

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory',
        verbose_name=_('Товар')
    )

    min_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Минимальный остаток'),
        help_text=_('Уведомление при достижении минимума')
    )

    max_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('Максимальный остаток'),
        help_text=_('Максимальное количество на складе')
    )

    track_inventory = models.BooleanField(
        default=True,
        verbose_name=_('Учёт остатков'),
        help_text=_('Вести учёт количества товара')
    )

    # Метаданные
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        db_table = 'products_product_inventory'
        verbose_name = _('Настройки учёта товара')
        verbose_name_plural = _('Настройки учёта товаров')
        indexes = [
            models.Index(fields=['track_inventory']),
        ]

    def __str__(self):
        return f"{self.product.name} - Учёт: {'Вкл' if self.track_inventory else 'Выкл'}"

    @property
    def quantity(self):
        """Общее количество товара из всех активных партий"""
        if not self.track_inventory:
            return None

        from django.db.models import Sum
        total = self.product.batches.filter(is_active=True).aggregate(
            total=Sum('quantity')
        )['total']
        return total or 0

    @property
    def is_low_stock(self):
        """Проверяет достиг ли товар минимального остатка"""
        qty = self.quantity
        if qty is not None:
            return qty <= self.min_quantity
        return False

    @property
    def stock_status(self):
        """Возвращает статус остатка"""
        if not self.track_inventory:
            return 'unlimited'

        qty = self.quantity
        if qty <= 0:
            return 'out_of_stock'
        if self.is_low_stock:
            return 'low_stock'
        return 'in_stock'


class ProductBatch(models.Model):
    """
    Партия товара - для учёта товаров с разными характеристиками.

    Каждая партия имеет:
    - Свою цену закупки
    - Своё количество
    - Срок годности (опционально)
    - Дату поступления
    - Номер партии/накладной

    Это позволяет вести учёт по FIFO/FEFO методам.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='batches',
        verbose_name=_('Товар')
    )

    batch_number = models.CharField(
        max_length=100,
        verbose_name=_('Номер партии'),
        help_text=_('Номер партии или накладной')
    )

    barcode = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Штрихкод партии'),
        help_text=_('Автоматически генерируется для каждой партии')
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Количество в партии')
    )

    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Цена закупки'),
        help_text=_('Цена закупки этой партии')
    )

    # Срок годности (опционально)
    manufacturing_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Дата производства')
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Срок годности'),
        help_text=_('Дата окончания срока годности')
    )

    # Поставщик
    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='batches',
        verbose_name=_('Поставщик')
    )

    supplier_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Поставщик (строка)'),
        help_text=_('Название поставщика (для обратной совместимости)')
    )

    # Примечание
    notes = models.TextField(
        blank=True,
        verbose_name=_('Примечания')
    )

    # Статус
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активна'),
        help_text=_('Партия доступна для продажи')
    )

    # Метаданные
    received_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата поступления')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        db_table = 'products_product_batch'
        verbose_name = _('Партия товара')
        verbose_name_plural = _('Партии товаров')
        ordering = ['expiry_date', 'received_at']  # FEFO: First Expired, First Out
        indexes = [
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['received_at']),
        ]

    def __str__(self):
        return f"{self.product.name} - Партия {self.batch_number} ({self.quantity} {self.product.unit.short_name})"

    def save(self, *args, **kwargs):
        """Автоматическая генерация штрихкода для партии"""
        if not self.barcode:
            import uuid
            from django.utils import timezone
            # Генерируем уникальный штрихкод на основе UUID
            # Формат: BATCH-{timestamp}-{random}
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            unique_part = uuid.uuid4().hex[:8].upper()
            self.barcode = f"BATCH-{timestamp}-{unique_part}"

        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Проверяет истёк ли срок годности"""
        if self.expiry_date:
            from django.utils import timezone
            return timezone.now().date() > self.expiry_date
        return False

    @property
    def days_until_expiry(self):
        """Количество дней до истечения срока годности"""
        if self.expiry_date:
            from django.utils import timezone
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None

    @property
    def is_near_expiry(self, days=30):
        """Проверяет близок ли срок годности (по умолчанию 30 дней)"""
        days_left = self.days_until_expiry
        if days_left is not None:
            return 0 < days_left <= days
        return False


class ProductAttribute(models.Model):
    """
    Связь товара с атрибутами и их значениями.

    Например:
    - Товар "Футболка Nike" имеет атрибут "Цвет" = "Красный"
    - Товар "Футболка Nike" имеет атрибут "Размер" = "L"
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='attributes',
        verbose_name=_('Товар')
    )

    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        verbose_name=_('Атрибут')
    )

    # Для text/number атрибутов
    value_text = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Текстовое значение')
    )

    value_number = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_('Числовое значение')
    )

    value_boolean = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_('Логическое значение')
    )

    # Для select/multiselect атрибутов
    value_option = models.ForeignKey(
        AttributeValue,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Выбранное значение')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    class Meta:
        db_table = 'products_product_attribute'
        verbose_name = _('Атрибут товара')
        verbose_name_plural = _('Атрибуты товаров')
        unique_together = [['product', 'attribute']]

    def __str__(self):
        return f"{self.product.name}: {self.attribute.name} = {self.get_value()}"

    def get_value(self):
        """Возвращает значение атрибута в зависимости от типа"""
        if self.attribute.type == 'text':
            return self.value_text
        elif self.attribute.type == 'number':
            return self.value_number
        elif self.attribute.type == 'boolean':
            return 'Да' if self.value_boolean else 'Нет'
        elif self.attribute.type in ['select', 'multiselect']:
            return self.value_option.value if self.value_option else None
        return None


class ProductImage(models.Model):
    """
    Дополнительные изображения товара.

    Товар может иметь несколько изображений помимо главного.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Товар')
    )

    image = models.ImageField(
        upload_to='products/gallery/',
        verbose_name=_('Изображение')
    )

    alt_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Альтернативный текст')
    )

    order = models.IntegerField(
        default=0,
        verbose_name=_('Порядок')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    class Meta:
        db_table = 'products_product_image'
        verbose_name = _('Изображение товара')
        verbose_name_plural = _('Изображения товаров')
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"


class Supplier(models.Model):
    """
    Поставщик товаров.

    Хранит информацию о поставщиках: контакты, условия оплаты, рейтинг.
    Связан с партиями товаров (ProductBatch).
    """

    name = models.CharField(
        max_length=200,
        verbose_name=_('Название'),
        help_text=_('Название поставщика')
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('Код поставщика'),
        help_text=_('Уникальный код для идентификации')
    )

    # Контактная информация
    contact_person = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Контактное лицо')
    )

    email = models.EmailField(
        blank=True,
        verbose_name=_('Email')
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Телефон')
    )

    address = models.TextField(
        blank=True,
        verbose_name=_('Адрес')
    )

    website = models.URLField(
        blank=True,
        verbose_name=_('Веб-сайт')
    )

    # Условия работы
    payment_terms = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Условия оплаты'),
        help_text=_('Например: предоплата, отсрочка 30 дней')
    )

    delivery_time = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('Срок поставки (дней)'),
        help_text=_('Среднее время доставки в днях')
    )

    min_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('Минимальная сумма заказа')
    )

    # Рейтинг и статус
    rating = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name=_('Рейтинг'),
        help_text=_('От 0 до 5 звезд')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен'),
        help_text=_('Работаем ли с этим поставщиком')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Примечания')
    )

    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        db_table = 'products_supplier'
        verbose_name = _('Поставщик')
        verbose_name_plural = _('Поставщики')
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return self.name


class ProductBarcode(models.Model):
    """
    Штрих-коды товара.

    Один товар может иметь несколько штрих-кодов разных типов.
    Например: EAN-13, UPC, QR-код, внутренний код магазина.
    """

    BARCODE_TYPES = [
        ('ean13', 'EAN-13'),
        ('ean8', 'EAN-8'),
        ('upc', 'UPC'),
        ('qr', 'QR Code'),
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('internal', _('Внутренний код')),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='barcodes',
        verbose_name=_('Товар')
    )

    barcode = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Штрих-код'),
        help_text=_('Уникальный штрих-код')
    )

    barcode_type = models.CharField(
        max_length=20,
        choices=BARCODE_TYPES,
        default='ean13',
        verbose_name=_('Тип штрих-кода')
    )

    is_primary = models.BooleanField(
        default=False,
        verbose_name=_('Основной'),
        help_text=_('Основной штрих-код для печати')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    class Meta:
        db_table = 'products_product_barcode'
        verbose_name = _('Штрих-код товара')
        verbose_name_plural = _('Штрих-коды товаров')
        ordering = ['-is_primary', 'barcode']
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['product', 'is_primary']),
        ]
        unique_together = [['product', 'barcode']]

    def __str__(self):
        primary = ' (осн.)' if self.is_primary else ''
        return f"{self.product.name} - {self.barcode}{primary}"


class ProductTag(models.Model):
    """
    Теги для товаров.

    Используются для маркетинга, фильтрации и группировки товаров.
    Примеры: Новинка, Хит продаж, Скидка, Эко, Premium.
    """

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Название'),
        help_text=_('Например: Новинка, Хит продаж')
    )

    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name=_('Slug')
    )

    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        verbose_name=_('Цвет'),
        help_text=_('Hex цвет для отображения: #RRGGBB')
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Иконка'),
        help_text=_('Название иконки (например, из Font Awesome)')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен')
    )

    order = models.IntegerField(
        default=0,
        verbose_name=_('Порядок сортировки')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    class Meta:
        db_table = 'products_product_tag'
        verbose_name = _('Тег товара')
        verbose_name_plural = _('Теги товаров')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class StockReservation(models.Model):
    """
    Резервирование товаров.

    Блокирует партии товаров под заказы в обработке.
    Предотвращает двойную продажу одного товара.
    """

    STATUS_CHOICES = [
        ('active', _('Активно')),
        ('completed', _('Выполнено')),
        ('cancelled', _('Отменено')),
        ('expired', _('Истекло')),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('Товар')
    )

    batch = models.ForeignKey(
        ProductBatch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reservations',
        verbose_name=_('Партия'),
        help_text=_('Конкретная партия для резервирования (FEFO)')
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        verbose_name=_('Количество')
    )

    # Ссылка на заказ (будет позже связана с моделью Order)
    order_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('ID заказа'),
        help_text=_('Временно используем ID, позже будет FK')
    )

    order_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Номер заказа'),
        help_text=_('Номер заказа для отображения')
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=_('Статус')
    )

    reserved_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Зарезервировано до'),
        help_text=_('Автоматически освободится после этой даты')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Примечания')
    )

    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата резервирования')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    created_by = models.ForeignKey(
        'users.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_reservations',
        verbose_name=_('Создал')
    )

    class Meta:
        db_table = 'products_stock_reservation'
        verbose_name = _('Резервирование товара')
        verbose_name_plural = _('Резервирование товаров')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'status']),
            models.Index(fields=['batch', 'status']),
            models.Index(fields=['order_id']),
            models.Index(fields=['reserved_until']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        batch_info = f" (Партия {self.batch.batch_number})" if self.batch else ""
        return f"Резерв: {self.product.name}{batch_info} - {self.quantity} {self.product.unit.short_name}"

    @property
    def is_expired(self):
        """Проверяет истекло ли резервирование"""
        if self.reserved_until and self.status == 'active':
            from django.utils import timezone
            return timezone.now() > self.reserved_until
        return False

    def release(self):
        """Освобождает резервирование"""
        if self.status == 'active':
            self.status = 'cancelled'
            self.save()

    def complete(self):
        """
        Завершает резервирование (товар продан).
        ВАЖНО: Уменьшает количество товара в партии или общий запас!
        """
        if self.status == 'active':
            # Уменьшаем количество товара
            if self.batch:
                # Списываем из конкретной партии
                self.batch.quantity -= self.quantity
                if self.batch.quantity < 0:
                    self.batch.quantity = 0
                self.batch.save(update_fields=['quantity', 'updated_at'])
            # Если партия не указана, товар уже должен быть списан из партий
            # Ничего дополнительно делать не нужно, так как количество хранится в партиях

            # Меняем статус резервирования
            self.status = 'completed'
            self.save()
