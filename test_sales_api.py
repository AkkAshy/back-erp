#!/usr/bin/env python
"""
Quick test script to verify sales API endpoints are registered correctly
"""

import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import get_resolver

def print_sales_urls():
    """Print all sales-related URLs"""
    resolver = get_resolver()

    print("=== Sales API Endpoints ===\n")

    def show_urls(urlpatterns, prefix=''):
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                # It's an include, recurse
                show_urls(pattern.url_patterns, prefix + str(pattern.pattern))
            else:
                full_pattern = prefix + str(pattern.pattern)
                if '/sales/' in full_pattern:
                    # Get view name
                    view_name = pattern.name if hasattr(pattern, 'name') else 'N/A'
                    print(f"  {full_pattern:<60} [{view_name}]")

    show_urls(resolver.url_patterns)

    print("\n=== Available Sales ViewSet Actions ===\n")

    # Import viewsets to check available actions
    from sales.views import (
        CashRegisterViewSet, CashierSessionViewSet, SaleViewSet,
        SaleItemViewSet, PaymentViewSet, CashMovementViewSet
    )

    viewsets = {
        'CashRegister': CashRegisterViewSet,
        'CashierSession': CashierSessionViewSet,
        'Sale': SaleViewSet,
        'SaleItem': SaleItemViewSet,
        'Payment': PaymentViewSet,
        'CashMovement': CashMovementViewSet,
    }

    for name, viewset_class in viewsets.items():
        print(f"{name}ViewSet:")

        # Get custom actions
        actions = []
        for attr_name in dir(viewset_class):
            attr = getattr(viewset_class, attr_name)
            if hasattr(attr, 'mapping'):
                # It's a custom action
                detail = getattr(attr, 'detail', False)
                actions.append((attr_name, 'detail' if detail else 'list'))

        if actions:
            for action_name, action_type in actions:
                print(f"  - {action_name} ({action_type})")
        else:
            print("  - Standard CRUD operations only")
        print()

if __name__ == '__main__':
    print_sales_urls()
