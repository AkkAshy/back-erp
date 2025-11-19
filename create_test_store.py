#!/usr/bin/env python
"""
Скрипт для создания тестового магазина с админом и общим аккаунтом.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Store

User = get_user_model()

def create_test_store():
    """Создание тестового магазина"""

    # Данные магазина
    store_name = "Тестовый Магазин"
    store_slug = "test_shop"

    # Данные администратора
    admin_username = "admin_testshop"
    admin_password = "admin12345"
    admin_email = "admin@testshop.com"
    admin_first_name = "Админ"
    admin_last_name = "Тестовый"
    admin_phone = "+998901111111"

    print("🏪 Создание тестового магазина...")
    print(f"📋 Название: {store_name}")
    print(f"🔑 Slug: {store_slug}")
    print()

    # Проверяем существует ли уже магазин
    if Store.objects.filter(slug=store_slug).exists():
        print("⚠️  Магазин с таким slug уже существует!")
        store = Store.objects.get(slug=store_slug)
        print(f"   Store ID: {store.id}")
        print(f"   Tenant Key: {store.tenant_key}")
        print()

        # Показываем данные владельца
        owner = store.owner
        print("👤 Владелец (Админ):")
        print(f"   Username: {owner.username}")
        print(f"   Password: admin12345 (если не менялся)")
        print(f"   Email: {owner.email}")
        print()

        # Показываем общий аккаунт
        staff_username = f"{store.slug}_staff"
        try:
            staff_user = User.objects.get(username=staff_username)
            print("👥 Общий аккаунт сотрудников:")
            print(f"   Username: {staff_username}")
            print(f"   Password: 12345678")
            print()
        except User.DoesNotExist:
            print("⚠️  Общий аккаунт не найден!")
            print()

        return

    # Создаем владельца (админа)
    print("👤 Создание администратора...")
    admin_user = User.objects.create_user(
        username=admin_username,
        password=admin_password,
        email=admin_email,
        first_name=admin_first_name,
        last_name=admin_last_name,
        phone=admin_phone,
        is_active=True
    )
    print(f"   ✅ Создан: {admin_username}")

    # Создаем магазин
    print()
    print("🏪 Создание магазина...")
    store = Store.objects.create(
        name=store_name,
        slug=store_slug,
        owner=admin_user,
        address="ул. Тестовая, 1",
        phone="+998901111111",
        is_active=True
    )
    print(f"   ✅ Создан: {store.name}")
    print(f"   Schema: {store.schema_name}")
    print(f"   Tenant Key: {store.tenant_key}")

    # При создании магазина автоматически создаются:
    # - Employee для владельца (через сигнал)
    # - Общий staff аккаунт (через сигнал)
    # - Общая касса (через сигнал)

    print()
    print("=" * 60)
    print("✅ МАГАЗИН УСПЕШНО СОЗДАН!")
    print("=" * 60)
    print()

    print("📝 ДАННЫЕ ДЛЯ ВХОДА:")
    print()

    print("1️⃣  АДМИНИСТРАТОР (Владелец):")
    print(f"   Username: {admin_username}")
    print(f"   Password: {admin_password}")
    print(f"   Права: Полный доступ")
    print()

    print("2️⃣  ОБЩИЙ АККАУНТ СОТРУДНИКОВ:")
    print(f"   Username: {store.slug}_staff")
    print(f"   Password: 12345678")
    print(f"   Права: Продажи, просмотр товаров")
    print()

    print("🔑 ВАЖНО:")
    print(f"   Tenant Key: {store.tenant_key}")
    print(f"   Используйте этот ключ в заголовке X-Tenant-Key")
    print()

    print("📡 ПРИМЕРЫ ЗАПРОСОВ:")
    print()
    print("Логин администратора:")
    print(f"""
curl -X POST https://back-erp-gules.vercel.app/api/users/auth/login/ \\
  -H "Content-Type: application/json" \\
  -H "X-Tenant-Key: {store.tenant_key}" \\
  -d '{{
    "username": "{admin_username}",
    "password": "{admin_password}"
  }}'
""")

    print()
    print("Логин общего аккаунта:")
    print(f"""
curl -X POST https://back-erp-gules.vercel.app/api/users/auth/login/ \\
  -H "Content-Type: application/json" \\
  -H "X-Tenant-Key: {store.tenant_key}" \\
  -d '{{
    "username": "{store.slug}_staff",
    "password": "12345678"
  }}'
""")

if __name__ == '__main__':
    create_test_store()
