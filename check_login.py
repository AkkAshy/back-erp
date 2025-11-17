#!/usr/bin/env python
"""
Скрипт для диагностики проблем с логином.

Usage:
    python check_login.py <username>
    python check_login.py testuser
"""

import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import Employee, Store


def check_user_login(username):
    """Проверка возможности логина для пользователя"""

    print(f"\n{'='*60}")
    print(f"Проверка логина для: {username}")
    print(f"{'='*60}\n")

    # 1. Проверка существования пользователя
    try:
        user = User.objects.get(username=username)
        print(f"✓ Пользователь найден")
        print(f"  - ID: {user.id}")
        print(f"  - Email: {user.email}")
        print(f"  - Имя: {user.get_full_name() or 'Не указано'}")
        print(f"  - Активен: {'✓' if user.is_active else '✗'}")
    except User.DoesNotExist:
        print(f"✗ ОШИБКА: Пользователь '{username}' не найден!\n")
        print("Создайте пользователя через регистрацию:")
        print(f"  POST /api/users/auth/register/")
        return False

    if not user.is_active:
        print(f"\n✗ ОШИБКА: Пользователь неактивен!")
        print("Активируйте пользователя:")
        print(f"  User.objects.filter(username='{username}').update(is_active=True)")
        return False

    # 2. Проверка Employee записей
    print(f"\n{'─'*60}")
    print("Employee записи:")
    print(f"{'─'*60}")

    employees = Employee.objects.filter(user=user).select_related('store')

    if employees.count() == 0:
        print(f"✗ ОШИБКА: У пользователя нет Employee записей!")
        print("\nЭто критическая проблема. Employee должен создаваться автоматически.")
        print("\nРешение 1: Создать Employee вручную через Django shell")
        print(f"  python manage.py shell")
        print(f"  >>> from users.models import Employee, Store")
        print(f"  >>> from django.contrib.auth.models import User")
        print(f"  >>> user = User.objects.get(username='{username}')")
        print(f"  >>> store = Store.objects.first()")
        print(f"  >>> Employee.objects.create(user=user, store=store, role='owner', is_active=True)")
        print("\nРешение 2: Запустите скрипт создания тестового пользователя")
        print(f"  python create_test_user.py")
        return False

    print(f"Найдено Employee записей: {employees.count()}\n")

    for i, emp in enumerate(employees, 1):
        print(f"Employee #{i}:")
        print(f"  - Магазин: {emp.store.name}")
        print(f"  - Роль: {emp.role} ({emp.get_role_display()})")
        print(f"  - Активен: {'✓' if emp.is_active else '✗'}")
        print(f"  - Магазин активен: {'✓' if emp.store.is_active else '✗'}")
        print(f"  - Tenant Key: {emp.store.tenant_key}")
        print()

    # 3. Проверка активных Employee (условие для логина)
    print(f"{'─'*60}")
    print("Проверка условий логина:")
    print(f"{'─'*60}")

    active_employees = Employee.objects.filter(
        user=user,
        is_active=True,
        store__is_active=True
    ).select_related('store')

    active_count = active_employees.count()
    print(f"Активных Employee (для логина): {active_count}\n")

    if active_count == 0:
        print("✗ ЛОГИН НЕ ПРОЙДЕТ!")
        print("\nПричины:")

        for emp in employees:
            issues = []
            if not emp.is_active:
                issues.append(f"Employee #{emp.id} неактивен")
            if not emp.store.is_active:
                issues.append(f"Магазин '{emp.store.name}' неактивен")

            if issues:
                for issue in issues:
                    print(f"  - {issue}")

        print("\nРешение:")
        print("Активируйте Employee и магазины:")
        print(f"  Employee.objects.filter(user__username='{username}').update(is_active=True)")
        print(f"  Store.objects.all().update(is_active=True)")
        return False

    # 4. Успех!
    print("✓ ЛОГИН ДОЛЖЕН РАБОТАТЬ!\n")

    emp = active_employees.first()
    print("Данные для входа:")
    print(f"  Username: {username}")
    print(f"  Password: <ваш пароль>")
    print(f"\n  Магазин: {emp.store.name}")
    print(f"  Tenant Key: {emp.store.tenant_key}")
    print(f"  Роль: {emp.get_role_display()}")

    print(f"\nПосле логина используйте этот tenant_key в заголовке:")
    print(f"  X-Tenant-Key: {emp.store.tenant_key}")

    return True


def create_test_user_if_needed(username):
    """Создать тестового пользователя если его нет"""

    print(f"\nСоздать тестового пользователя '{username}'? (y/n): ", end='')
    choice = input().strip().lower()

    if choice != 'y':
        return

    print(f"\nСоздание пользователя '{username}'...")

    # Удаляем если существует
    User.objects.filter(username=username).delete()

    # Создаём пользователя
    user = User.objects.create_user(
        username=username,
        password='TestPass123!',
        first_name='Test',
        last_name='User',
        email=f'{username}@example.com',
        is_active=True
    )

    # Создаём или получаем магазин
    store, created = Store.objects.get_or_create(
        slug=f'{username}-store',
        defaults={
            'name': f'{username.capitalize()} Store',
            'owner': user,
            'address': 'Test Address',
            'phone': '+998901234567',
            'is_active': True
        }
    )

    if created:
        print(f"✓ Создан магазин: {store.name}")
    else:
        print(f"✓ Использован существующий магазин: {store.name}")
        store.is_active = True
        store.save()

    # Создаём Employee
    employee = Employee.objects.create(
        user=user,
        store=store,
        role='owner',
        position='Владелец',
        phone='+998901234567',
        is_active=True
    )

    print(f"\n{'='*60}")
    print("✓ Тестовый пользователь успешно создан!")
    print(f"{'='*60}\n")
    print(f"Username: {username}")
    print(f"Password: TestPass123!")
    print(f"Store: {store.name}")
    print(f"Tenant Key: {store.tenant_key}")
    print(f"\nТеперь можно войти через:")
    print(f"  POST /api/users/auth/login/")
    print(f"  {{")
    print(f'    "username": "{username}",')
    print(f'    "password": "TestPass123!"')
    print(f"  }}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_login.py <username>")
        print("Example: python check_login.py testuser")
        sys.exit(1)

    username = sys.argv[1]

    can_login = check_user_login(username)

    if not can_login:
        print(f"\n{'='*60}")
        create_test_user_if_needed(username)
