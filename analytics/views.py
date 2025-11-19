# coding: utf-8
"""
Views для аналитики и отчётов.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta, datetime

from analytics.models import (
    DailySalesReport,
    ProductPerformance,
    CustomerAnalytics,
    InventorySnapshot
)
from analytics.serializers import (
    DailySalesReportSerializer,
    ProductPerformanceSerializer,
    CustomerAnalyticsSerializer,
    InventorySnapshotSerializer,
    SalesTrendSerializer,
    TopProductSerializer,
    CustomerSegmentSerializer,
)


class DailySalesReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для дневных отчётов по продажам.
    
    Только чтение (read-only), данные обновляются автоматически через signals.
    """
    
    queryset = DailySalesReport.objects.all()
    serializer_class = DailySalesReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['date']
    ordering_fields = ['date', 'total_sales', 'total_sales_count']
    ordering = ['-date']
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Отчёт за сегодня"""
        today = timezone.now().date()
        report = self.queryset.filter(date=today).first()
        
        if not report:
            return Response({
                'message': 'Отчёт за сегодня ещё не сформирован'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def period(self, request):
        """
        Отчёты за период.
        
        Query params:
        - start_date: дата начала (YYYY-MM-DD)
        - end_date: дата окончания (YYYY-MM-DD)
        """
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response({
                'error': 'Укажите start_date и end_date'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'error': 'Неверный формат даты. Используйте YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reports = self.queryset.filter(date__gte=start, date__lte=end)
        
        # Агрегированные данные за период
        totals = reports.aggregate(
            total_sales=Sum('total_sales'),
            total_count=Sum('total_sales_count'),
            total_discount=Sum('total_discount'),
            total_tax=Sum('total_tax'),
            total_items=Sum('total_items_sold'),
            avg_sale=Avg('avg_sale_amount'),
        )
        
        serializer = self.get_serializer(reports, many=True)
        
        return Response({
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': (end - start).days + 1
            },
            'totals': totals,
            'daily_reports': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """
        График продаж за последние N дней.
        
        Query params:
        - days: количество дней (по умолчанию 30)
        """
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        reports = self.queryset.filter(date__gte=start_date).order_by('date')
        
        trend_data = reports.values('date').annotate(
            total_sales=F('total_sales'),
            total_count=F('total_sales_count'),
            avg_sale=F('avg_sale_amount')
        )
        
        serializer = SalesTrendSerializer(trend_data, many=True)
        
        return Response({
            'period': f'Последние {days} дней',
            'trends': serializer.data
        })


class ProductPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для производительности товаров.
    
    Только чтение, обновляется автоматически.
    """
    
    queryset = ProductPerformance.objects.select_related('product').all()
    serializer_class = ProductPerformanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['product', 'date']
    ordering_fields = ['date', 'total_revenue', 'quantity_sold', 'profit_margin']
    ordering = ['-date', '-total_revenue']
    
    @action(detail=False, methods=['get'])
    def top_products(self, request):
        """
        Топ товаров за период.
        
        Query params:
        - start_date: дата начала
        - end_date: дата окончания
        - limit: количество товаров (по умолчанию 10)
        - order_by: сортировка (revenue, quantity, profit) - по умолчанию revenue
        """
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        limit = int(request.query_params.get('limit', 10))
        order_by = request.query_params.get('order_by', 'revenue')
        
        if not start_date or not end_date:
            # По умолчанию - последние 30 дней
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Агрегируем данные по товарам
        performance = self.queryset.filter(
            date__gte=start_date,
            date__lte=end_date
        ).values(
            'product__id', 'product__name', 'product__sku'
        ).annotate(
            total_revenue=Sum('total_revenue'),
            total_quantity=Sum('quantity_sold'),
            total_profit=Sum('total_profit'),
            sales_count=Sum('sales_count')
        )

        # Сортировка
        if order_by == 'quantity':
            performance = performance.order_by('-total_quantity')
        elif order_by == 'profit':
            performance = performance.order_by('-total_profit')
        else:
            performance = performance.order_by('-total_revenue')

        # Ограничиваем количество
        performance = performance[:limit]

        # Преобразуем данные
        top_data = [{
            'product_id': p['product__id'],
            'product_name': p['product__name'],
            'product_sku': p['product__sku'],
            'total_revenue': p['total_revenue'],
            'total_quantity': p['total_quantity'],
            'total_profit': p['total_profit'],
            'sales_count': p['sales_count'],
        } for p in performance]
        
        serializer = TopProductSerializer(top_data, many=True)
        
        return Response({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'top_products': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def slow_movers(self, request):
        """Медленно продающиеся товары за последние 30 дней"""
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        # Товары с продажами < 5 единиц
        slow_products = self.queryset.filter(
            date__gte=start_date
        ).values(
            'product__id', 'product__name', 'product__sku'
        ).annotate(
            total_quantity=Sum('quantity_sold')
        ).filter(
            total_quantity__lt=5
        ).order_by('total_quantity')[:20]
        
        return Response({
            'period': f'Последние {days} дней',
            'slow_movers': list(slow_products)
        })


class CustomerAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для аналитики покупателей (RFM).
    
    Только чтение, обновляется автоматически.
    """
    
    queryset = CustomerAnalytics.objects.select_related('customer').all()
    serializer_class = CustomerAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['customer', 'segment', 'rfm_score']
    ordering_fields = ['monetary', 'frequency', 'recency_days', 'rfm_score']
    ordering = ['-monetary']
    
    @action(detail=False, methods=['get'])
    def segments(self, request):
        """Статистика по сегментам клиентов"""
        
        # Берём последний период
        latest_period = self.queryset.values('period_start', 'period_end').order_by('-period_end').first()
        
        if not latest_period:
            return Response({
                'message': 'Нет данных по клиентам'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Агрегируем по сегментам
        segments = self.queryset.filter(
            period_start=latest_period['period_start'],
            period_end=latest_period['period_end']
        ).values('segment').annotate(
            count=Count('id'),
            total_spent=Sum('monetary'),
            avg_purchase=Avg('avg_purchase_amount')
        ).order_by('-total_spent')
        
        serializer = CustomerSegmentSerializer(segments, many=True)
        
        return Response({
            'period': latest_period,
            'segments': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def at_risk(self, request):
        """Клиенты в группе риска (At Risk, Can't Lose Them, Hibernating)"""
        
        at_risk_segments = ['At Risk', 'Can\'t Lose Them', 'Hibernating', 'Lost']
        
        customers = self.queryset.filter(
            segment__in=at_risk_segments
        ).order_by('-monetary')
        
        serializer = self.get_serializer(customers, many=True)
        
        return Response({
            'count': customers.count(),
            'customers': serializer.data
        })


class InventorySnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для снимков остатков.
    
    Только чтение, обновляется автоматически.
    """
    
    queryset = InventorySnapshot.objects.select_related('product').all()
    serializer_class = InventorySnapshotSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['product', 'date', 'is_low_stock', 'is_out_of_stock', 'is_overstock']
    ordering_fields = ['date', 'quantity_on_hand', 'turnover_rate', 'days_of_stock']
    ordering = ['-date', 'product']
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Последние снимки остатков (по одному на товар)"""
        
        # Получаем последнюю дату
        latest_date = self.queryset.values('date').order_by('-date').first()
        
        if not latest_date:
            return Response({
                'message': 'Нет данных по остаткам'
            }, status=status.HTTP_404_NOT_FOUND)
        
        snapshots = self.queryset.filter(date=latest_date['date'])
        serializer = self.get_serializer(snapshots, many=True)
        
        return Response({
            'date': latest_date['date'],
            'snapshots': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def low_stock_alerts(self, request):
        """Товары с низким остатком"""
        
        latest_date = self.queryset.values('date').order_by('-date').first()
        
        if not latest_date:
            return Response({'message': 'Нет данных'}, status=status.HTTP_404_NOT_FOUND)
        
        low_stock = self.queryset.filter(
            date=latest_date['date'],
            is_low_stock=True
        ).order_by('days_of_stock')
        
        serializer = self.get_serializer(low_stock, many=True)
        
        return Response({
            'date': latest_date['date'],
            'count': low_stock.count(),
            'products': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Товары с нулевым остатком"""
        
        latest_date = self.queryset.values('date').order_by('-date').first()
        
        if not latest_date:
            return Response({'message': 'Нет данных'}, status=status.HTTP_404_NOT_FOUND)
        
        out_of_stock = self.queryset.filter(
            date=latest_date['date'],
            is_out_of_stock=True
        )
        
        serializer = self.get_serializer(out_of_stock, many=True)
        
        return Response({
            'date': latest_date['date'],
            'count': out_of_stock.count(),
            'products': serializer.data
        })
