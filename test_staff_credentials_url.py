#!/usr/bin/env python
"""
Тест для проверки URL staff-credentials endpoint
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.urls import reverse
from rest_framework.test import APIRequestFactory
from users.views import StoreViewSet

# Проверка что action существует
print("=" * 60)
print("Проверка StoreViewSet.staff_credentials action")
print("=" * 60)

viewset = StoreViewSet()
print(f"✅ StoreViewSet имеет метод staff_credentials: {hasattr(viewset, 'staff_credentials')}")

# Проверка URL
try:
    # Для действия detail=False URL должен быть: /api/users/stores/staff-credentials/
    factory = APIRequestFactory()
    request = factory.get('/api/users/stores/staff-credentials/')

    # Проверяем что action зарегистрирован
    from rest_framework.routers import DefaultRouter
    router = DefaultRouter()
    router.register(r'stores', StoreViewSet, basename='store')

    urls = router.urls
    print(f"\n📋 Зарегистрированные URL для StoreViewSet:")
    for url in urls:
        if 'staff' in str(url.pattern):
            print(f"   ✅ {url.pattern} - {url.name}")

    # Проверяем формат action декоратора
    action_attr = getattr(StoreViewSet.staff_credentials, 'mapping', None)
    detail = getattr(StoreViewSet.staff_credentials, 'detail', None)
    url_path = getattr(StoreViewSet.staff_credentials, 'url_path', None)

    print(f"\n🔍 Action attributes:")
    print(f"   detail: {detail}")
    print(f"   url_path: {url_path}")
    print(f"   mapping: {action_attr}")

    if detail == False and url_path == 'staff-credentials':
        print("\n✅ Action правильно настроен!")
        print(f"   URL должен быть: /api/users/stores/staff-credentials/")
    else:
        print("\n❌ Проблема с настройкой action!")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
