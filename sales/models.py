"""
Модели для управления продажами в tenant схеме.

ВАЖНО: Все эти модели находятся в tenant_{slug} схемах, а НЕ в public!
Это означает что каждый магазин имеет свои отдельные продажи и кассовые смены.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class CashRegister(models.Model):
    """
    Касса - физическое устройство для приёма платежей.

    Может быть несколько касс в одном магазине.
    """

    name = models.CharField(
        max_length=100,
        verbose_name=_('Название'),
        help_text=_('Например: Касса 1, Главная касса')
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Код кассы'),
        help_text=_('Уникальный код для идентификации')
    )

    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Расположение'),
        help_text=_('Например: Зал 1, Склад')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активна'),
        help_text=_('Касса доступна для работы')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Примечания')
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
        db_table = 'sales_cash_register'
        verbose_name = _('Касса')
        verbose_name_plural = _('Кассы')
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),  # Уникальный поиск по коду
            models.Index(fields=['is_active']),  # Фильтрация активных касс
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class CashierSession(models.Model):
    """
    Кассовая смена - период работы кассира на конкретной кассе.

    Кассир открывает смену в начале рабочего дня и закрывает в конце.
    При открытии указывается начальная сумма наличных в кассе.
    """

    STATUS_CHOICES = [
        ('open', _('Открыта')),
        ('closed', _('Закрыта')),
        ('suspended', _('Приостановлена')),
    ]

    cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT,
        related_name='sessions',
        verbose_name=_('Касса')
    )

    # Кассир (Employee) - может быть как с user аккаунтом, так и без
    cashier = models.ForeignKey(
        'users.Employee',
        on_delete=models.PROTECT,
        related_name='cashier_sessions',
        null=True,
        blank=True,
        verbose_name=_('Кассир'),
        help_text=_('Сотрудник, работающий на этой смене')
    )

    # Оставляем для обратной совместимости (deprecated)
    cashier_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Имя кассира (устарело)'),
        help_text=_('Используется только для старых записей. Новые смены используют cashier (FK)')
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name=_('Статус')
    )

    # Начальная сумма при открытии
    opening_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Начальная сумма наличных'),
        help_text=_('Сколько денег было в кассе при открытии смены')
    )

    # Ожидаемая сумма при закрытии (рассчитывается автоматически)
    expected_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Ожидаемая сумма наличных'),
        help_text=_('Сколько должно быть денег по расчётам')
    )

    # Фактическая сумма при закрытии (вводит кассир)
    actual_cash = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('Фактическая сумма наличных'),
        help_text=_('Сколько денег фактически в кассе при закрытии')
    )

    # Разница (недостача/излишек)
    cash_difference = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Разница'),
        help_text=_('Фактическая - Ожидаемая (+ излишек, - недостача)')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Примечания')
    )

    opened_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата открытия')
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата закрытия')
    )

    class Meta:
        db_table = 'sales_cashier_session'
        verbose_name = _('Кассовая смена')
        verbose_name_plural = _('Кассовые смены')
        ordering = ['-opened_at']
        indexes = [
            models.Index(fields=['cash_register', 'status']),
            models.Index(fields=['status', 'opened_at']),
        ]

    def __str__(self):
        return f"{self.cash_register.name} - {self.cashier_name} ({self.get_status_display()})"

    @property
    def duration(self):
        """Длительность смены"""
        if self.closed_at:
            return self.closed_at - self.opened_at
        from django.utils import timezone
        return timezone.now() - self.opened_at

    @property
    def total_sales(self):
        """Общая сумма продаж за смену"""
        from django.db.models import Sum
        total = self.sales.filter(status='completed').aggregate(
            total=Sum('total_amount')
        )['total']
        return total or Decimal('0.00')

    @property
    def cash_sales(self):
        """Сумма продаж наличными"""
        from django.db.models import Sum
        total = self.payments.filter(
            payment_method='cash',
            sale__status='completed'
        ).aggregate(total=Sum('amount'))['total']
        return total or Decimal('0.00')

    @property
    def card_sales(self):
        """Сумма продаж по карте"""
        from django.db.models import Sum
        total = self.payments.filter(
            payment_method='card',
            sale__status='completed'
        ).aggregate(total=Sum('amount'))['total']
        return total or Decimal('0.00')

    def calculate_expected_cash(self):
        """Рассчитать ожидаемую сумму наличных"""
        # Начальная сумма + продажи наличными + внесения - изъятия
        cash_in = self.cash_movements.filter(movement_type='cash_in').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        cash_out = self.cash_movements.filter(movement_type='cash_out').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        expected = self.opening_cash + self.cash_sales + cash_in - cash_out
        self.expected_cash = expected
        return expected

    def close_session(self, actual_cash_amount):
        """Закрыть смену"""
        from django.utils import timezone

        self.calculate_expected_cash()
        self.actual_cash = Decimal(str(actual_cash_amount))
        self.cash_difference = self.actual_cash - self.expected_cash
        self.status = 'closed'
        self.closed_at = timezone.now()
        self.save()


class Sale(models.Model):
    """
    Продажа (чек) - одна транзакция продажи товаров.

    Может содержать несколько позиций (SaleItem).
    """

    STATUS_CHOICES = [
        ('pending', _('В обработке')),
        ('completed', _('Завершена')),
        ('cancelled', _('Отменена')),
        ('refunded', _('Возврат')),
    ]

    session = models.ForeignKey(
        CashierSession,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name=_('Кассовая смена')
    )

    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Номер чека'),
        help_text=_('Уникальный номер чека')
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Статус')
    )

    # Клиент (опционально)
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales',
        verbose_name=_('Клиент'),
        help_text=_('Покупатель (опционально)')
    )

    # Для обратной совместимости, если клиент не из базы
    customer_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Имя клиента'),
        help_text=_('Используется если customer не указан')
    )

    customer_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Телефон клиента'),
        help_text=_('Используется если customer не указан')
    )

    # Суммы
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Сумма без скидки')
    )

    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Сумма скидки')
    )

    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Процент скидки')
    )

    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Сумма налога')
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Итоговая сумма')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Примечания')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата завершения')
    )

    class Meta:
        db_table = 'sales_sale'
        verbose_name = _('Продажа')
        verbose_name_plural = _('Продажи')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', 'status']),
            models.Index(fields=['receipt_number']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Чек #{self.receipt_number} - {self.total_amount}"

    @property
    def items_count(self):
        """Количество позиций в чеке"""
        return self.items.count()

    @property
    def total_quantity(self):
        """Общее количество товаров"""
        from django.db.models import Sum
        total = self.items.aggregate(total=Sum('quantity'))['total']
        return total or 0

    def calculate_totals(self):
        """Рассчитать итоговые суммы"""
        # Сумма всех позиций
        self.subtotal = sum(item.line_total for item in self.items.all())

        # Применяем скидку
        if self.discount_percent > 0:
            self.discount_amount = self.subtotal * (self.discount_percent / 100)

        # Итого с учётом скидки
        amount_after_discount = self.subtotal - self.discount_amount

        # Рассчитываем налог (если есть)
        # self.tax_amount рассчитывается от позиций

        # Финальная сумма
        self.total_amount = amount_after_discount + self.tax_amount
        self.save()

    def complete_sale(self):
        """Завершить продажу"""
        from django.utils import timezone

        if self.status == 'pending':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()

            # Создаём резервирования для товаров
            for item in self.items.all():
                item.create_stock_reservation()


class SaleItem(models.Model):
    """
    Позиция в чеке - один товар в продаже.
    """

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Продажа')
    )

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='sale_items',
        verbose_name=_('Товар')
    )

    batch = models.ForeignKey(
        'products.ProductBatch',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='sale_items',
        verbose_name=_('Партия'),
        help_text=_('Партия товара для списания (FEFO)')
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        verbose_name=_('Количество')
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Цена за единицу'),
        help_text=_('Цена на момент продажи')
    )

    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Скидка на позицию')
    )

    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Ставка НДС (%)')
    )

    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Сумма позиции'),
        help_text=_('quantity * unit_price - discount')
    )

    # Резервирование товара
    reservation = models.ForeignKey(
        'products.StockReservation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sale_items',
        verbose_name=_('Резервирование')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата добавления')
    )

    class Meta:
        db_table = 'sales_sale_item'
        verbose_name = _('Позиция продажи')
        verbose_name_plural = _('Позиции продаж')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['sale', 'product']),  # Поиск товара в продаже
            models.Index(fields=['batch']),  # Поиск по партии для FEFO
            models.Index(fields=['product']),  # Аналитика по товарам
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity} = {self.line_total}"

    def save(self, *args, **kwargs):
        """Пересчитываем line_total при сохранении"""
        self.line_total = (self.quantity * self.unit_price) - self.discount_amount
        super().save(*args, **kwargs)

    def create_stock_reservation(self):
        """Создать резервирование товара"""
        from products.models import StockReservation

        if not self.reservation:
            # Пытаемся найти Employee через User кассира
            # Поскольку в CashierSession нет прямой связи с Employee,
            # а только cashier_name (строка), оставляем created_by = None
            reservation = StockReservation.objects.create(
                product=self.product,
                batch=self.batch,
                quantity=self.quantity,
                order_reference=self.sale.receipt_number,
                status='active',
                created_by=None  # TODO: Добавить связь когда CashierSession будет иметь FK к Employee
            )
            self.reservation = reservation
            self.save()


class Payment(models.Model):
    """
    Платёж - оплата за продажу.

    Одна продажа может иметь несколько платежей (разные способы оплаты).
    """

    PAYMENT_METHOD_CHOICES = [
        ('cash', _('Наличные')),
        ('card', _('Банковская карта')),
        ('transfer', _('Перевод')),
        ('online', _('Онлайн оплата')),
        ('credit', _('В кредит')),
        ('other', _('Другое')),
    ]

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Продажа')
    )

    session = models.ForeignKey(
        CashierSession,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name=_('Кассовая смена')
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name=_('Способ оплаты')
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Сумма')
    )

    # Для наличных - сдача
    received_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_('Получено'),
        help_text=_('Для наличных - сколько дал клиент')
    )

    change_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Сдача')
    )

    # Для карты - последние 4 цифры
    card_last4 = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        verbose_name=_('Последние 4 цифры карты')
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('ID транзакции'),
        help_text=_('Номер транзакции для безналичных')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Примечания')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата платежа')
    )

    class Meta:
        db_table = 'sales_payment'
        verbose_name = _('Платёж')
        verbose_name_plural = _('Платежи')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sale']),
            models.Index(fields=['session', 'payment_method']),
        ]

    def __str__(self):
        return f"{self.get_payment_method_display()} - {self.amount}"

    def save(self, *args, **kwargs):
        """Рассчитываем сдачу для наличных"""
        if self.payment_method == 'cash' and self.received_amount:
            self.change_amount = self.received_amount - self.amount
        super().save(*args, **kwargs)


class CashMovement(models.Model):
    """
    Движение наличности - внесение или изъятие денег из кассы.

    Например: инкассация, размен, внесение сдачи.
    """

    MOVEMENT_TYPE_CHOICES = [
        ('cash_in', _('Внесение')),
        ('cash_out', _('Изъятие')),
    ]

    REASON_CHOICES = [
        ('collection', _('Инкассация')),
        ('change', _('Размен')),
        ('float', _('Пополнение сдачи')),
        ('expense', _('Расход')),
        ('correction', _('Корректировка')),
        ('other', _('Другое')),
    ]

    session = models.ForeignKey(
        CashierSession,
        on_delete=models.PROTECT,
        related_name='cash_movements',
        verbose_name=_('Кассовая смена')
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPE_CHOICES,
        verbose_name=_('Тип операции')
    )

    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        verbose_name=_('Причина')
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Сумма')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )

    # Кто выполнил операцию
    performed_by = models.ForeignKey(
        'users.Employee',
        on_delete=models.SET_NULL,
        null=True,
        related_name='cash_movements',
        verbose_name=_('Выполнил')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата операции')
    )

    class Meta:
        db_table = 'sales_cash_movement'
        verbose_name = _('Движение наличности')
        verbose_name_plural = _('Движения наличности')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', 'movement_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        sign = '+' if self.movement_type == 'cash_in' else '-'
        return f"{sign}{self.amount} - {self.get_reason_display()}"
