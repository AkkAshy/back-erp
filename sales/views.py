"""
ViewSets для sales app.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.db.models import Sum, Count
from django.utils import timezone

from sales.models import (
    CashRegister, CashierSession, Sale, SaleItem,
    Payment, CashMovement
)
from sales.serializers import (
    CashRegisterSerializer, CashierSessionSerializer,
    CashierSessionDetailSerializer, SaleSerializer,
    SaleDetailSerializer, SaleCreateUpdateSerializer,
    SaleItemSerializer, PaymentSerializer, CashMovementSerializer
)
from core.permissions import IsTenantUser


class CashRegisterViewSet(viewsets.ModelViewSet):
    """ViewSet для касс"""

    queryset = CashRegister.objects.prefetch_related('sessions').all()
    serializer_class = CashRegisterSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'location']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def sessions(self, request, pk=None):
        """Получить все смены кассы"""
        cash_register = self.get_object()
        sessions = cash_register.sessions.select_related('cash_register').all()

        # Фильтр по статусу
        status_filter = request.query_params.get('status')
        if status_filter:
            sessions = sessions.filter(status=status_filter)

        page = self.paginate_queryset(sessions)
        if page is not None:
            serializer = CashierSessionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CashierSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def current_session(self, request, pk=None):
        """Получить текущую открытую смену"""
        cash_register = self.get_object()
        session = cash_register.sessions.filter(status='open').first()

        if not session:
            return Response(
                {'error': 'Нет открытой смены на этой кассе'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CashierSessionDetailSerializer(session)
        return Response(serializer.data)


class CashierSessionViewSet(viewsets.ModelViewSet):
    """ViewSet для кассовых смен"""

    queryset = CashierSession.objects.select_related('cash_register').all()
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['cash_register', 'status', 'cashier_name']
    search_fields = ['cashier_name', 'cash_register__name']
    ordering_fields = ['opened_at', 'closed_at']
    ordering = ['-opened_at']

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'retrieve':
            return CashierSessionDetailSerializer
        return CashierSessionSerializer

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Получить текущую открытую смену текущего пользователя"""
        # Ищем открытую смену для текущего пользователя
        session = CashierSession.objects.filter(
            status='open',
            cashier_name=request.user.get_full_name() or request.user.username
        ).first()

        if not session:
            return Response(
                {
                    'status': 'error',
                    'message': 'Нет открытой смены',
                    'data': None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CashierSessionDetailSerializer(session)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def open(self, request):
        """Открыть новую кассовую смену"""
        # Проверяем, есть ли уже открытая смена у пользователя
        existing_session = CashierSession.objects.filter(
            status='open',
            cashier_name=request.user.get_full_name() or request.user.username
        ).first()

        if existing_session:
            return Response(
                {
                    'status': 'error',
                    'message': 'У вас уже есть открытая смена',
                    'non_field_errors': ['У вас уже есть открытая смена']
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        opening_balance = request.data.get('opening_balance')
        if opening_balance is None:
            return Response(
                {
                    'status': 'error',
                    'message': 'Укажите начальный баланс',
                    'non_field_errors': ['Укажите начальный баланс']
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем или создаём кассу по умолчанию
        from sales.models import CashRegister
        cash_register, _ = CashRegister.objects.get_or_create(
            name='Главная касса',
            defaults={'code': 'MAIN', 'location': 'Основной зал'}
        )

        # Создаём новую смену
        session = CashierSession.objects.create(
            cash_register=cash_register,
            cashier_name=request.user.get_full_name() or request.user.username,
            opening_cash=opening_balance,
            status='open'
        )

        serializer = CashierSessionDetailSerializer(session)
        return Response({
            'status': 'success',
            'message': 'Смена успешно открыта',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Закрыть кассовую смену"""
        session = self.get_object()

        if session.status != 'open':
            return Response(
                {'error': 'Смена уже закрыта'},
                status=status.HTTP_400_BAD_REQUEST
            )

        actual_cash = request.data.get('actual_cash')
        if actual_cash is None:
            return Response(
                {'error': 'Укажите фактическую сумму наличных'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session.close_session(actual_cash)
            serializer = self.get_serializer(session)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Приостановить смену"""
        session = self.get_object()

        if session.status != 'open':
            return Response(
                {'error': 'Можно приостановить только открытую смену'},
                status=status.HTTP_400_BAD_REQUEST
            )

        session.status = 'suspended'
        session.save()

        serializer = self.get_serializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Возобновить приостановленную смену"""
        session = self.get_object()

        if session.status != 'suspended':
            return Response(
                {'error': 'Можно возобновить только приостановленную смену'},
                status=status.HTTP_400_BAD_REQUEST
            )

        session.status = 'open'
        session.save()

        serializer = self.get_serializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """Получить отчёт по смене"""
        session = self.get_object()

        # Статистика по продажам
        sales_stats = session.sales.filter(status='completed').aggregate(
            total_sales=Sum('total_amount'),
            total_items=Sum('items__quantity'),
            count=Count('id')
        )

        # Статистика по платежам
        payment_stats = session.payments.filter(
            sale__status='completed'
        ).values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        )

        # Движения наличности
        cash_movements = session.cash_movements.aggregate(
            cash_in=Sum('amount', filter=models.Q(movement_type='cash_in')),
            cash_out=Sum('amount', filter=models.Q(movement_type='cash_out'))
        )

        report = {
            'session': CashierSessionSerializer(session).data,
            'sales': {
                'total_amount': sales_stats['total_sales'] or 0,
                'total_items': sales_stats['total_items'] or 0,
                'count': sales_stats['count'] or 0,
            },
            'payments': list(payment_stats),
            'cash_movements': {
                'cash_in': cash_movements['cash_in'] or 0,
                'cash_out': cash_movements['cash_out'] or 0,
            }
        }

        return Response(report)

    @action(detail=False, methods=['get'], url_path='cashier-stats')
    def cashier_stats(self, request):
        """
        Получить топ статистику по кассирам за период.

        GET /api/sales/cashier-sessions/cashier-stats/?date_from=2025-01-01&date_to=2025-01-31&limit=10

        Параметры:
        - date_from: начальная дата (опционально, по умолчанию начало месяца)
        - date_to: конечная дата (опционально, по умолчанию сегодня)
        - limit: количество топ кассиров (опционально, по умолчанию все)
        """
        from datetime import datetime
        from django.db.models import Sum, Count, Q, DecimalField
        from django.db.models.functions import Coalesce
        from django.utils import timezone
        from users.models import Employee

        # Параметры фильтрации по дате
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        limit = request.query_params.get('limit')

        # Дефолтные даты: начало месяца - сегодня
        if not date_from:
            date_from = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # Поддержка формата YYYY-MM-DD и YYYY-MM-DDTHH:MM:SS
            if 'T' not in date_from:
                # Только дата - добавляем начало дня
                date_from = timezone.make_aware(datetime.fromisoformat(f"{date_from}T00:00:00"))
            else:
                date_from = timezone.make_aware(datetime.fromisoformat(date_from))

        if not date_to:
            date_to = timezone.now()
        else:
            # Поддержка формата YYYY-MM-DD и YYYY-MM-DDTHH:MM:SS
            if 'T' not in date_to:
                # Только дата - добавляем конец дня
                date_to = timezone.make_aware(datetime.fromisoformat(f"{date_to}T23:59:59"))
            else:
                date_to = timezone.make_aware(datetime.fromisoformat(date_to))

        # Получаем статистику по продажам напрямую из Sale.cashier
        from sales.models import Sale, Payment

        cashier_stats = Sale.objects.filter(
            created_at__gte=date_from,
            created_at__lte=date_to,
            status='completed',
            cashier__isnull=False
        ).values(
            'cashier__id',
            'cashier__first_name',
            'cashier__last_name',
            'cashier__phone',
            'cashier__role'
        ).annotate(
            total_sales=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()),
            sales_count=Count('id')
        ).order_by('-total_sales')

        # Получаем статистику по способам оплаты для каждого кассира
        cashiers_list = []
        for stat in cashier_stats:
            cashier_id = stat['cashier__id']

            # Статистика по оплатам
            payment_stats = Payment.objects.filter(
                sale__cashier_id=cashier_id,
                sale__created_at__gte=date_from,
                sale__created_at__lte=date_to,
                sale__status='completed'
            ).aggregate(
                cash_total=Coalesce(Sum('amount', filter=Q(payment_method='cash')), 0, output_field=DecimalField()),
                card_total=Coalesce(Sum('amount', filter=Q(payment_method='card')), 0, output_field=DecimalField())
            )

            # Подсчет смен (уникальных сессий, в которых кассир работал)
            sessions_count = Sale.objects.filter(
                cashier_id=cashier_id,
                created_at__gte=date_from,
                created_at__lte=date_to,
                status='completed'
            ).values('session').distinct().count()

            cashiers_list.append({
                'id': cashier_id,
                'full_name': f"{stat['cashier__last_name']} {stat['cashier__first_name']}".strip(),
                'phone': stat['cashier__phone'],
                'role': stat['cashier__role'],
                'total_sales': str(stat['total_sales']),
                'cash_sales': str(payment_stats['cash_total']),
                'card_sales': str(payment_stats['card_total']),
                'sales_count': stat['sales_count'],
                'sessions_count': sessions_count
            })

        # Ограничиваем количество если указан limit
        if limit:
            cashiers_list = cashiers_list[:int(limit)]

        return Response({
            'status': 'success',
            'data': {
                'period': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat()
                },
                'cashiers': cashiers_list,
                'total_cashiers': len(cashiers_list)
            }
        })

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Получить все активные смены"""
        sessions = self.get_queryset().filter(status='open')

        page = self.paginate_queryset(sessions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)


class SaleViewSet(viewsets.ModelViewSet):
    """ViewSet для продаж"""

    queryset = Sale.objects.select_related('session', 'session__cash_register').prefetch_related('items', 'payments')
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['session', 'status']
    search_fields = ['receipt_number', 'customer_name', 'customer_phone']
    ordering_fields = ['created_at', 'completed_at', 'total_amount']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update']:
            return SaleCreateUpdateSerializer
        elif self.action == 'retrieve':
            return SaleDetailSerializer
        return SaleSerializer

    @action(detail=False, methods=['post'])
    def scan_item(self, request):
        """
        Сканирование товара на кассе.
        Создаёт новую продажу (черновик) или добавляет товар в текущую незавершённую продажу.

        Body:
        - session: ID кассовой смены
        - product: ID товара
        - quantity: количество (по умолчанию 1)
        - batch: ID партии (опционально)
        """
        from products.models import Product, ProductBatch
        from decimal import Decimal

        session_id = request.data.get('session')
        product_id = request.data.get('product')
        quantity = Decimal(str(request.data.get('quantity', 1)))
        batch_id = request.data.get('batch')

        if not session_id or not product_id:
            return Response(
                {'error': 'Укажите session и product'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = CashierSession.objects.get(id=session_id, status='open')
        except CashierSession.DoesNotExist:
            return Response(
                {'error': 'Смена не найдена или закрыта'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            product = Product.objects.select_related('pricing').get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Товар не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        batch = None
        if batch_id:
            try:
                batch = ProductBatch.objects.get(id=batch_id, product=product)
            except ProductBatch.DoesNotExist:
                return Response(
                    {'error': 'Партия не найдена'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Автоматический выбор партии (FEFO - First Expired, First Out)
            # Выбираем партию с самым ранним сроком годности и достаточным количеством
            batch = ProductBatch.objects.filter(
                product=product,
                quantity__gte=quantity,
                is_active=True
            ).order_by('expiry_date', 'received_at').first()

        # Получаем кассира из request.employee (заполняется middleware)
        cashier = getattr(request, 'employee', None)
        cashier_id = cashier.id if cashier else None

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
                status='pending',
                cashier_id=cashier_id  # Заполняем ID кассира для статистики
            )
        else:
            # Если продажа существует, но cashier не заполнен - заполняем
            if not sale.cashier_id and cashier_id:
                sale.cashier_id = cashier_id
                sale.save(update_fields=['cashier_id'])

        # ПРОВЕРКА НАЛИЧИЯ ТОВАРА
        # Получаем доступное количество из inventory
        available_qty = Decimal('0')
        if hasattr(product, 'inventory') and product.inventory:
            if product.inventory.track_inventory:
                available_qty = Decimal(str(product.inventory.quantity or 0))
            else:
                # Если учет не ведется - считаем что товар всегда доступен
                available_qty = Decimal('999999')  # Очень большое число
        else:
            # Если нет inventory - считаем что товара нет
            available_qty = Decimal('0')

        # Проверяем, сколько уже добавлено в текущую продажу
        existing_item = SaleItem.objects.filter(
            sale=sale,
            product=product,
            batch=batch
        ).first()

        current_qty_in_sale = existing_item.quantity if existing_item else Decimal('0')
        total_requested = current_qty_in_sale + quantity

        if total_requested > available_qty:
            return Response({
                'status': 'error',
                'code': 'insufficient_stock',
                'message': f'Недостаточно товара на складе. Доступно: {available_qty}, запрошено: {total_requested}',
                'data': {
                    'available': str(available_qty),
                    'requested': str(total_requested),
                    'current_in_sale': str(current_qty_in_sale)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Получаем цену товара из pricing
        unit_price = Decimal('0.00')
        if hasattr(product, 'pricing') and product.pricing:
            unit_price = product.pricing.sale_price or product.pricing.cost_price or Decimal('0.00')

        if existing_item:
            # Увеличиваем количество существующей позиции
            existing_item.quantity += quantity
            existing_item.save()
            sale_item = existing_item
        else:
            # Создаём новую позицию
            sale_item = SaleItem.objects.create(
                sale=sale,
                product=product,
                batch=batch,
                quantity=quantity,
                unit_price=unit_price
            )

        # Пересчитываем суммы
        sale.calculate_totals()

        serializer = SaleDetailSerializer(sale)
        return Response({
            'status': 'success',
            'message': 'Товар добавлен',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """
        Добавить товар в существующую продажу.

        Body:
        - product: ID товара
        - quantity: количество
        - batch: ID партии (опционально)
        """
        from products.models import Product, ProductBatch
        from decimal import Decimal

        sale = self.get_object()

        if sale.status != 'pending':
            return Response(
                {'error': 'Можно добавлять товары только в незавершённую продажу'},
                status=status.HTTP_400_BAD_REQUEST
            )

        product_id = request.data.get('product')
        quantity = Decimal(str(request.data.get('quantity', 1)))
        batch_id = request.data.get('batch')

        if not product_id:
            return Response(
                {'error': 'Укажите product'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.select_related('pricing').get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Товар не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        batch = None
        if batch_id:
            try:
                batch = ProductBatch.objects.get(id=batch_id, product=product)
            except ProductBatch.DoesNotExist:
                return Response(
                    {'error': 'Партия не найдена'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # ПРОВЕРКА НАЛИЧИЯ ТОВАРА
        # Получаем доступное количество из inventory
        available_qty = Decimal('0')
        if hasattr(product, 'inventory') and product.inventory:
            if product.inventory.track_inventory:
                available_qty = Decimal(str(product.inventory.quantity or 0))
            else:
                # Если учет не ведется - считаем что товар всегда доступен
                available_qty = Decimal('999999')  # Очень большое число
        else:
            # Если нет inventory - считаем что товара нет
            available_qty = Decimal('0')

        # Проверяем, сколько уже добавлено в эту продажу
        current_qty_in_sale = SaleItem.objects.filter(
            sale=sale,
            product=product
        ).aggregate(total=models.Sum('quantity'))['total'] or Decimal('0')

        total_requested = current_qty_in_sale + quantity

        if total_requested > available_qty:
            return Response({
                'status': 'error',
                'code': 'insufficient_stock',
                'message': f'Недостаточно товара на складе. Доступно: {available_qty}, запрошено: {total_requested}',
                'data': {
                    'available': str(available_qty),
                    'requested': str(total_requested),
                    'current_in_sale': str(current_qty_in_sale)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Получаем цену товара из pricing
        unit_price = Decimal('0.00')
        if hasattr(product, 'pricing') and product.pricing:
            unit_price = product.pricing.sale_price or product.pricing.cost_price or Decimal('0.00')

        # Добавляем позицию
        SaleItem.objects.create(
            sale=sale,
            product=product,
            batch=batch,
            quantity=quantity,
            unit_price=unit_price
        )

        # Пересчитываем суммы
        sale.calculate_totals()

        serializer = SaleDetailSerializer(sale)
        return Response({
            'status': 'success',
            'message': 'Товар добавлен',
            'data': serializer.data
        })

    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        """
        Удалить товар из продажи.

        Body:
        - item_id: ID позиции (SaleItem)
        """
        sale = self.get_object()

        if sale.status != 'pending':
            return Response(
                {'error': 'Можно удалять товары только из незавершённой продажи'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item_id = request.data.get('item_id')

        if not item_id:
            return Response(
                {'error': 'Укажите item_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = sale.items.get(id=item_id)
            item.delete()

            # Пересчитываем суммы
            sale.calculate_totals()

            serializer = SaleDetailSerializer(sale)
            return Response({
                'status': 'success',
                'message': 'Товар удалён',
                'data': serializer.data
            })
        except SaleItem.DoesNotExist:
            return Response(
                {'error': 'Товар не найден в этой продаже'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        """
        Завершить продажу (оформить оплату).

        Body:
        - payments: массив платежей [{"payment_method": "cash", "amount": 150000, "received_amount": 200000}]
        """
        from decimal import Decimal

        sale = self.get_object()

        if sale.status != 'pending':
            return Response(
                {'error': 'Можно завершить только незавершённую продажу'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем что есть товары
        if not sale.items.exists():
            return Response(
                {'error': 'Нельзя завершить продажу без товаров'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payments_data = request.data.get('payments', [])

        if not payments_data:
            return Response(
                {'error': 'Укажите способ оплаты'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаём платежи
        total_paid = Decimal('0.00')
        for payment_data in payments_data:
            payment_method = payment_data.get('payment_method')
            amount = Decimal(str(payment_data.get('amount', 0)))
            received_amount = payment_data.get('received_amount')

            if received_amount:
                received_amount = Decimal(str(received_amount))

            # Валидация для наличных
            if payment_method == 'cash' and received_amount:
                if received_amount < amount:
                    return Response(
                        {'error': 'Полученная сумма не может быть меньше суммы платежа'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            Payment.objects.create(
                sale=sale,
                session=sale.session,
                payment_method=payment_method,
                amount=amount,
                received_amount=received_amount,
                card_last4=payment_data.get('card_last4'),
                transaction_id=payment_data.get('transaction_id'),
                notes=payment_data.get('notes', '')
            )

            total_paid += amount

        # Проверяем что оплачено достаточно
        if total_paid < sale.total_amount:
            return Response(
                {'error': f'Недостаточно оплачено. Нужно: {sale.total_amount}, Оплачено: {total_paid}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Завершаем продажу
        try:
            sale.complete_sale()
            serializer = SaleDetailSerializer(sale)
            return Response({
                'status': 'success',
                'message': 'Продажа завершена',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Завершить продажу (legacy метод, используйте checkout)"""
        sale = self.get_object()

        if sale.status != 'pending':
            return Response(
                {'error': 'Можно завершить только продажу в статусе "В обработке"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем что сумма платежей >= суммы продажи (агрегация вместо loop)
        from decimal import Decimal
        total_paid = sale.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        if total_paid < sale.total_amount:
            return Response(
                {'error': f'Недостаточно оплачено. Нужно: {sale.total_amount}, Оплачено: {total_paid}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            sale.complete_sale()
            serializer = SaleDetailSerializer(sale)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отменить продажу"""
        sale = self.get_object()

        if sale.status == 'completed':
            return Response(
                {'error': 'Нельзя отменить завершённую продажу. Используйте возврат.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sale.status = 'cancelled'
        sale.save()

        # Освобождаем резервирования (prefetch для оптимизации)
        items = sale.items.select_related('reservation').all()
        for item in items:
            if item.reservation:
                item.reservation.release()

        serializer = SaleDetailSerializer(sale)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Оформить возврат"""
        sale = self.get_object()

        if sale.status != 'completed':
            return Response(
                {'error': 'Можно вернуть только завершённую продажу'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sale.status = 'refunded'
        sale.save()

        # Освобождаем резервирования и возвращаем товар на склад (prefetch для оптимизации)
        items = sale.items.select_related('reservation', 'batch').all()
        for item in items:
            if item.reservation:
                item.reservation.status = 'cancelled'
                item.reservation.save()

                # Возвращаем количество в партию
                if item.batch:
                    item.batch.quantity += item.quantity
                    item.batch.save()

        serializer = SaleDetailSerializer(sale)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Получить текущую незавершённую продажу (черновик) для указанной смены.

        Query params:
        - session: ID кассовой смены
        """
        session_id = request.query_params.get('session')

        if not session_id:
            return Response(
                {'error': 'Укажите параметр session'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = CashierSession.objects.get(id=session_id, status='open')
        except CashierSession.DoesNotExist:
            return Response(
                {'error': 'Смена не найдена или закрыта'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Ищем текущую незавершённую продажу
        sale = Sale.objects.filter(
            session=session,
            status='pending'
        ).order_by('-created_at').first()

        if not sale:
            return Response(
                {
                    'status': 'success',
                    'message': 'Нет активной продажи',
                    'data': None
                }
            )

        serializer = SaleDetailSerializer(sale)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Получить продажи за сегодня"""
        today = timezone.now().date()
        sales = self.get_queryset().filter(
            created_at__date=today,
            status='completed'
        )

        page = self.paginate_queryset(sales)
        if page is not None:
            serializer = SaleSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = SaleSerializer(sales, many=True)
        return Response(serializer.data)


class SaleItemViewSet(viewsets.ModelViewSet):
    """ViewSet для позиций продажи"""

    queryset = SaleItem.objects.select_related('sale', 'product', 'batch').all()
    serializer_class = SaleItemSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['sale', 'product']
    ordering_fields = ['created_at']
    ordering = ['created_at']


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet для платежей"""

    queryset = Payment.objects.select_related('sale', 'session').all()
    serializer_class = PaymentSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['sale', 'session', 'payment_method']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']


class CashMovementViewSet(viewsets.ModelViewSet):
    """ViewSet для движения наличности"""

    queryset = CashMovement.objects.select_related('session').all()
    serializer_class = CashMovementSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session', 'movement_type', 'reason']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
