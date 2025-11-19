"""
Serializers для sales app.
"""

from rest_framework import serializers
from decimal import Decimal
from django.db import transaction
from sales.models import (
    CashRegister, CashierSession, Sale, SaleItem,
    Payment, CashMovement
)


class CashRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для касс"""

    active_sessions_count = serializers.SerializerMethodField()

    class Meta:
        model = CashRegister
        fields = [
            'id', 'name', 'code', 'location', 'is_active', 'notes',
            'active_sessions_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_active_sessions_count(self, obj):
        """Количество активных смен"""
        return obj.sessions.filter(status='open').count()


class CashMovementSerializer(serializers.ModelSerializer):
    """Сериализатор для движения наличности"""

    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)

    class Meta:
        model = CashMovement
        fields = [
            'id', 'session', 'movement_type', 'movement_type_display',
            'reason', 'reason_display', 'amount', 'description',
            'performed_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CashierSessionSerializer(serializers.ModelSerializer):
    """Сериализатор для кассовых смен"""

    cash_register_name = serializers.CharField(source='cash_register.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Кассир - опциональное поле (для закрытия смены с привязкой к кассиру)
    cashier_id = serializers.IntegerField(
        source='cashier.id',
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID кассира (Employee) - опционально"
    )
    cashier_full_name = serializers.CharField(source='cashier.full_name', read_only=True, allow_null=True)

    # Вычисляемые поля
    duration = serializers.SerializerMethodField()
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    cash_sales = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    card_sales = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CashierSession
        fields = [
            'id', 'cash_register', 'cash_register_name',
            'cashier_id', 'cashier_full_name', 'cashier_name',  # Новые поля
            'status', 'status_display',
            'opening_cash', 'expected_cash', 'actual_cash', 'cash_difference',
            'duration', 'total_sales', 'cash_sales', 'card_sales',
            'notes', 'opened_at', 'closed_at'
        ]
        read_only_fields = ['id', 'expected_cash', 'cash_difference', 'opened_at', 'closed_at', 'cashier_name', 'cash_register']

    def validate_cashier_id(self, value):
        """Проверяем что кассир существует и активен (если указан)"""
        if value is None:
            return value

        from users.models import Employee
        request = self.context.get('request')

        if not request or not hasattr(request, 'tenant'):
            raise serializers.ValidationError("Не удалось определить магазин")

        try:
            cashier = Employee.objects.get(
                id=value,
                store=request.tenant,
                role='cashier',
                is_active=True
            )
            # Сохраняем объект для использования в create/update
            self._cashier = cashier
            return value
        except Employee.DoesNotExist:
            raise serializers.ValidationError(
                f"Кассир с ID {value} не найден или неактивен в вашем магазине"
            )

    def get_duration(self, obj):
        """Длительность смены в секундах"""
        duration = obj.duration
        if duration:
            return duration.total_seconds()
        return None

    def validate(self, data):
        """Валидация кассовой смены"""
        from sales.models import CashRegister

        cash_register = data.get('cash_register')

        # Если касса не указана, используем общую (первую активную)
        if not cash_register:
            default_register = CashRegister.objects.filter(is_active=True).first()
            if not default_register:
                raise serializers.ValidationError({
                    'cash_register': 'В магазине нет активных касс'
                })
            data['cash_register'] = default_register

        # Проверяем что нет уже открытой смены на этой кассе
        cash_register = data.get('cash_register')
        if cash_register:
            existing_session = CashierSession.objects.filter(
                cash_register=cash_register,
                status='open'
            ).exclude(pk=self.instance.pk if self.instance else None).exists()

            if existing_session:
                raise serializers.ValidationError({
                    'cash_register': 'На этой кассе уже есть открытая смена'
                })

        return data


class CashierSessionDetailSerializer(CashierSessionSerializer):
    """Детальный сериализатор для кассовой смены с движениями и продажами"""

    cash_movements = CashMovementSerializer(many=True, read_only=True)
    sales_count = serializers.SerializerMethodField()

    class Meta(CashierSessionSerializer.Meta):
        fields = CashierSessionSerializer.Meta.fields + [
            'cash_movements', 'sales_count'
        ]

    def get_sales_count(self, obj):
        """Количество продаж за смену"""
        return obj.sales.filter(status='completed').count()


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для платежей"""

    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'sale', 'session', 'payment_method', 'payment_method_display',
            'amount', 'received_amount', 'change_amount',
            'card_last4', 'transaction_id', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'change_amount', 'created_at']

    def validate(self, data):
        """Валидация платежа"""
        payment_method = data.get('payment_method')
        amount = data.get('amount', 0)
        received_amount = data.get('received_amount')

        # Для наличных проверяем что получено >= суммы
        if payment_method == 'cash' and received_amount:
            if received_amount < amount:
                raise serializers.ValidationError({
                    'received_amount': 'Полученная сумма не может быть меньше суммы платежа'
                })

        return data


class SaleItemSerializer(serializers.ModelSerializer):
    """Сериализатор для позиций продажи"""

    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True, allow_null=True)

    class Meta:
        model = SaleItem
        fields = [
            'id', 'sale', 'product', 'product_name', 'product_sku',
            'batch', 'batch_number', 'quantity', 'unit_price',
            'discount_amount', 'tax_rate', 'line_total',
            'reservation', 'created_at'
        ]
        read_only_fields = ['id', 'line_total', 'reservation', 'created_at']

    def validate(self, data):
        """Валидация позиции продажи"""
        product = data.get('product')
        batch = data.get('batch')
        quantity = data.get('quantity', 0)

        # Проверяем что партия принадлежит товару
        if batch and batch.product != product:
            raise serializers.ValidationError({
                'batch': 'Партия не принадлежит указанному товару'
            })

        # Проверяем доступное количество
        if batch:
            # Проверка доступности в партии с блокировкой
            from django.db.models import Sum
            from products.models import StockReservation, ProductBatch

            # Блокируем партию для проверки (защита от race condition)
            batch_locked = ProductBatch.objects.select_for_update().filter(pk=batch.pk).first()
            if not batch_locked:
                raise serializers.ValidationError({
                    'batch': 'Партия не найдена'
                })

            reserved = StockReservation.objects.filter(
                batch=batch,
                status='active'
            ).aggregate(total=Sum('quantity'))['total'] or 0

            available = batch_locked.quantity - reserved
            if quantity > available:
                raise serializers.ValidationError({
                    'quantity': f'Недостаточно товара в партии. Доступно: {available}'
                })

        return data


class SaleSerializer(serializers.ModelSerializer):
    """Сериализатор для продаж"""

    session_info = serializers.CharField(source='session.cash_register.name', read_only=True)
    cashier_name = serializers.CharField(source='session.cashier_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Информация о покупателе
    customer_info = serializers.SerializerMethodField()

    # Вычисляемые поля
    items_count = serializers.IntegerField(read_only=True)
    total_quantity = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)

    class Meta:
        model = Sale
        fields = [
            'id', 'session', 'session_info', 'cashier_name',
            'receipt_number', 'status', 'status_display',
            'customer', 'customer_info', 'customer_name', 'customer_phone',
            'subtotal', 'discount_amount', 'discount_percent',
            'tax_amount', 'total_amount',
            'items_count', 'total_quantity',
            'notes', 'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'subtotal', 'total_amount', 'created_at', 'completed_at']

    def get_customer_info(self, obj):
        """Получить информацию о покупателе"""
        if obj.customer:
            return {
                'id': obj.customer.id,
                'full_name': obj.customer.full_name,
                'phone': obj.customer.phone,
                'email': obj.customer.email,
                'is_vip': obj.customer.is_vip,
                'default_discount': float(obj.customer.default_discount) if obj.customer.default_discount else 0
            }
        return None

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

        # Проверяем уникальность номера чека
        receipt_number = data.get('receipt_number')
        if receipt_number:
            instance = self.instance
            if instance and instance.receipt_number == receipt_number:
                return data

            if Sale.objects.filter(receipt_number=receipt_number).exists():
                raise serializers.ValidationError({
                    'receipt_number': 'Чек с таким номером уже существует'
                })

        return data


class SaleDetailSerializer(SaleSerializer):
    """Детальный сериализатор для продажи с позициями и платежами"""

    items = SaleItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta(SaleSerializer.Meta):
        fields = SaleSerializer.Meta.fields + ['items', 'payments']


class SaleItemNestedSerializer(serializers.ModelSerializer):
    """Вложенный сериализатор для позиций продажи (без поля sale)"""

    class Meta:
        model = SaleItem
        fields = [
            'product', 'batch', 'quantity', 'unit_price',
            'discount_amount', 'tax_rate'
        ]

    def validate(self, data):
        """Валидация позиции продажи"""
        product = data.get('product')
        batch = data.get('batch')
        quantity = data.get('quantity', 0)

        # Проверяем что партия принадлежит товару
        if batch and batch.product != product:
            raise serializers.ValidationError({
                'batch': 'Партия не принадлежит указанному товару'
            })

        # Проверяем доступное количество
        if batch:
            from django.db.models import Sum
            from products.models import StockReservation, ProductBatch

            batch_locked = ProductBatch.objects.select_for_update().filter(pk=batch.pk).first()
            if not batch_locked:
                raise serializers.ValidationError({
                    'batch': 'Партия не найдена'
                })

            reserved = StockReservation.objects.filter(
                batch=batch,
                status='active'
            ).aggregate(total=Sum('quantity'))['total'] or 0

            available = batch_locked.quantity - reserved
            if quantity > available:
                raise serializers.ValidationError({
                    'quantity': f'Недостаточно товара в партии. Доступно: {available}'
                })

        return data


class PaymentNestedSerializer(serializers.ModelSerializer):
    """Вложенный сериализатор для платежей (без полей sale и session)"""

    class Meta:
        model = Payment
        fields = [
            'payment_method', 'amount', 'received_amount',
            'card_last4', 'transaction_id', 'notes'
        ]

    def validate(self, data):
        """Валидация платежа"""
        payment_method = data.get('payment_method')
        amount = data.get('amount', 0)
        received_amount = data.get('received_amount')

        # Для наличных проверяем что получено >= суммы
        if payment_method == 'cash' and received_amount:
            if received_amount < amount:
                raise serializers.ValidationError({
                    'received_amount': 'Полученная сумма не может быть меньше суммы платежа'
                })

        return data


class CustomerNestedSerializer(serializers.Serializer):
    """Вложенный сериализатор для создания покупателя при продаже"""

    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone = serializers.RegexField(regex=r'^\+998\d{9}$', required=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    customer_type = serializers.ChoiceField(choices=['individual', 'company'], default='individual')
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True)


class SaleCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления продажи с позициями"""

    items = SaleItemNestedSerializer(many=True)
    payments = PaymentNestedSerializer(many=True, required=False)

    # Возможность создать нового покупателя или выбрать существующего
    customer_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    new_customer = CustomerNestedSerializer(required=False, allow_null=True, write_only=True)

    # Кассир, который делает продажу
    cashier_id = serializers.IntegerField(
        required=True,
        write_only=True,
        help_text="ID кассира, который совершает продажу"
    )

    class Meta:
        model = Sale
        fields = [
            'session', 'cashier_id', 'receipt_number', 'status',
            'customer', 'customer_id', 'new_customer',
            'customer_name', 'customer_phone',
            'discount_percent', 'notes',
            'items', 'payments'
        ]
        read_only_fields = ['customer']

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

        return data

    def validate_cashier_id(self, value):
        """Проверяем что кассир существует и активен"""
        from users.models import Employee

        try:
            cashier = Employee.objects.get(id=value, is_active=True)

            # Проверяем что это кассир или складчик
            if cashier.role not in [Employee.Role.CASHIER, Employee.Role.STOCKKEEPER]:
                raise serializers.ValidationError(
                    'Выбранный сотрудник не является кассиром'
                )

            return value
        except Employee.DoesNotExist:
            raise serializers.ValidationError('Кассир с таким ID не найден')

    @transaction.atomic
    def create(self, validated_data):
        """Создание продажи с позициями и платежами"""
        items_data = validated_data.pop('items')
        payments_data = validated_data.pop('payments', [])
        customer_id = validated_data.pop('customer_id', None)
        new_customer_data = validated_data.pop('new_customer', None)
        cashier_id = validated_data.pop('cashier_id')

        # Получаем кассира
        from users.models import Employee
        cashier = Employee.objects.get(id=cashier_id)
        validated_data['cashier'] = cashier

        # Обработка покупателя
        customer_instance = None

        if customer_id:
            # Выбран существующий покупатель
            from customers.models import Customer
            try:
                customer_instance = Customer.objects.get(id=customer_id, is_active=True)
                validated_data['customer'] = customer_instance
                # Копируем данные из Customer
                if not validated_data.get('customer_name'):
                    validated_data['customer_name'] = customer_instance.full_name
                if not validated_data.get('customer_phone'):
                    validated_data['customer_phone'] = customer_instance.phone
            except Customer.DoesNotExist:
                raise serializers.ValidationError({
                    'customer_id': 'Покупатель с таким ID не найден'
                })

        elif new_customer_data:
            # Создаём нового покупателя
            from customers.models import Customer

            # Проверяем уникальность телефона
            phone = new_customer_data.get('phone')
            existing_customer = Customer.objects.filter(phone=phone).first()

            if existing_customer:
                # Если покупатель с таким телефоном существует, используем его
                customer_instance = existing_customer
                validated_data['customer'] = customer_instance
                validated_data['customer_name'] = customer_instance.full_name
                validated_data['customer_phone'] = customer_instance.phone
            else:
                # Создаём нового покупателя
                customer_instance = Customer.objects.create(**new_customer_data)
                validated_data['customer'] = customer_instance
                validated_data['customer_name'] = customer_instance.full_name
                validated_data['customer_phone'] = customer_instance.phone

        # Создаём продажу
        sale = Sale.objects.create(**validated_data)

        # Создаём позиции
        for item_data in items_data:
            SaleItem.objects.create(sale=sale, **item_data)

        # Пересчитываем суммы
        sale.calculate_totals()

        # Создаём платежи
        for payment_data in payments_data:
            Payment.objects.create(
                sale=sale,
                session=sale.session,
                **payment_data
            )

        # Обновляем статистику покупателя
        if customer_instance:
            customer_instance.add_purchase(sale.total_amount)

        return sale

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление продажи"""
        items_data = validated_data.pop('items', None)
        payments_data = validated_data.pop('payments', None)

        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем позиции если переданы
        if items_data is not None:
            # Удаляем старые позиции
            instance.items.all().delete()

            # Создаём новые
            for item_data in items_data:
                SaleItem.objects.create(sale=instance, **item_data)

            # Пересчитываем суммы
            instance.calculate_totals()

        # Обновляем платежи если переданы
        if payments_data is not None:
            instance.payments.all().delete()

            for payment_data in payments_data:
                Payment.objects.create(
                    sale=instance,
                    session=instance.session,
                    **payment_data
                )

        return instance
