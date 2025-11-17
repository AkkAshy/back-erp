"""
URL Configuration 4;O sales app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from sales.views import (
    CashRegisterViewSet, CashierSessionViewSet, SaleViewSet,
    SaleItemViewSet, PaymentViewSet, CashMovementViewSet
)

app_name = 'sales'

router = DefaultRouter()
router.register(r'cash-registers', CashRegisterViewSet, basename='cash-register')
router.register(r'sessions', CashierSessionViewSet, basename='session')
router.register(r'shifts', CashierSessionViewSet, basename='shift')  # ⭐ Alias for sessions
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'sale-items', SaleItemViewSet, basename='sale-item')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'cash-movements', CashMovementViewSet, basename='cash-movement')

urlpatterns = [
    path('', include(router.urls)),
]
