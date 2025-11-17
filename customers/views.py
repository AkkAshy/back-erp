"""
ViewSets для customers app.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal

from customers.models import CustomerGroup, Customer, CustomerTransaction
from customers.serializers import (
    CustomerGroupSerializer, CustomerSerializer,
    CustomerDetailSerializer, CustomerCreateUpdateSerializer,
    CustomerTransactionSerializer
)
from core.permissions import IsTenantUser


class CustomerGroupViewSet(viewsets.ModelViewSet):
    """ViewSet для групп покупателей"""

    queryset = CustomerGroup.objects.prefetch_related('customers').all()
    serializer_class = CustomerGroupSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'discount_percent', 'created_at']
    ordering = ['-discount_percent']

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Получить всех членов группы"""
        group = self.get_object()
        customers = group.customers.filter(is_active=True)

        page = self.paginate_queryset(customers)
        if page is not None:
            serializer = CustomerSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet для покупателей"""

    queryset = Customer.objects.select_related('group').all()
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['group', 'customer_type', 'is_active', 'is_blocked']
    search_fields = ['first_name', 'last_name', 'middle_name', 'phone', 'email', 'company_name']
    ordering_fields = ['created_at', 'last_purchase_at', 'total_purchases', 'loyalty_points']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update']:
            return CustomerCreateUpdateSerializer
        elif self.action == 'retrieve':
            return CustomerDetailSerializer
        return CustomerSerializer

    @action(detail=True, methods=['get'], url_path='purchase-history')
    def purchase_history(self, request, pk=None):
        """
        Получить историю покупок клиента.

        GET /api/customers/customers/{id}/purchase-history/

        Query параметры:
        - date_from: Дата начала (YYYY-MM-DD)
        - date_to: Дата окончания (YYYY-MM-DD)
        """
        customer = self.get_object()

        # Получаем продажи для этого клиента
        try:
            from sales.models import Sale
            from sales.serializers import SaleSerializer

            purchases = Sale.objects.filter(
                customer=customer
            ).select_related(
                'customer', 'store'
            ).prefetch_related(
                'items__product'
            ).order_by('-created_at')

            # Фильтр по датам
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')

            if date_from:
                purchases = purchases.filter(created_at__gte=date_from)
            if date_to:
                purchases = purchases.filter(created_at__lte=date_to)

            page = self.paginate_queryset(purchases)
            if page is not None:
                serializer = SaleSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = SaleSerializer(purchases, many=True)
            return Response(serializer.data)

        except ImportError:
            # Если модуль sales еще не готов
            return Response({
                'status': 'success',
                'message': 'История покупок пока недоступна',
                'data': []
            })

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Получить статистику по покупателю"""
        customer = self.get_object()

        # Статистика по покупкам
        stats = {
            'customer': CustomerSerializer(customer).data,
            'purchases': {
                'total_amount': customer.total_purchases,
                'total_count': customer.total_purchases_count,
                'last_purchase': customer.last_purchase_at,
                'loyalty_points': customer.loyalty_points,
            }
        }

        return Response(stats)

    @action(detail=False, methods=['get'])
    def search_by_phone(self, request):
        """Быстрый поиск покупателя по телефону"""
        phone = request.query_params.get('phone')

        if not phone:
            return Response(
                {
                    'status': 'error',
                    'message': 'Укажите номер телефона'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        customer = Customer.objects.filter(phone=phone, is_active=True).first()

        if not customer:
            return Response(
                {
                    'status': 'error',
                    'message': 'Покупатель не найден'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CustomerDetailSerializer(customer)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def vip_customers(self, request):
        """Получить VIP покупателей"""
        customers = self.get_queryset().filter(
            is_active=True,
            group__discount_percent__gte=10
        )

        page = self.paginate_queryset(customers)
        if page is not None:
            serializer = CustomerSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)


class CustomerTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для транзакций покупателей (только чтение)"""

    queryset = CustomerTransaction.objects.select_related('customer', 'sale').all()
    serializer_class = CustomerTransactionSerializer
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['customer', 'transaction_type', 'sale']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
