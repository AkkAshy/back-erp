# coding: utf-8
"""
URL конфигурация для аналитики.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from analytics import views

app_name = 'analytics'

router = DefaultRouter()
router.register(r'daily-sales', views.DailySalesReportViewSet, basename='daily-sales')
router.register(r'product-performance', views.ProductPerformanceViewSet, basename='product-performance')
router.register(r'customer-analytics', views.CustomerAnalyticsViewSet, basename='customer-analytics')
router.register(r'inventory-snapshots', views.InventorySnapshotViewSet, basename='inventory-snapshots')

urlpatterns = [
    path('', include(router.urls)),
]
