"""
URL Configuration 4;O products app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.views import (
    UnitViewSet, CategoryViewSet, AttributeViewSet,
    AttributeValueViewSet, ProductViewSet, ProductBatchViewSet,
    ProductImageViewSet, SupplierViewSet, ProductBarcodeViewSet,
    ProductTagViewSet, StockReservationViewSet
)

app_name = 'products'

router = DefaultRouter()
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'attributes', AttributeViewSet, basename='attribute')
router.register(r'attribute-values', AttributeValueViewSet, basename='attribute-value')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'batches', ProductBatchViewSet, basename='batch')
router.register(r'product-images', ProductImageViewSet, basename='product-image')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'barcodes', ProductBarcodeViewSet, basename='barcode')
router.register(r'tags', ProductTagViewSet, basename='tag')
router.register(r'reservations', StockReservationViewSet, basename='reservation')

urlpatterns = [
    path('', include(router.urls)),
]
