"""
URL configuration для customers app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from customers.views import (
    CustomerGroupViewSet,
    CustomerViewSet,
    CustomerTransactionViewSet
)

router = DefaultRouter()
router.register(r'groups', CustomerGroupViewSet, basename='customergroup')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'transactions', CustomerTransactionViewSet, basename='customertransaction')

urlpatterns = [
    path('', include(router.urls)),
]
