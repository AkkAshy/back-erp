"""
Management command для создания staff users для всех магазинов.
Используется если staff user был случайно удален или не создан при регистрации.

Usage:
    python manage.py create_staff_users
    python manage.py create_staff_users --store test_shop
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Store, Employee


class Command(BaseCommand):
    help = 'Создает staff users для всех магазинов (или для конкретного магазина)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--store',
            type=str,
            help='Slug конкретного магазина (опционально)',
        )

    def handle(self, *args, **options):
        store_slug = options.get('store')

        if store_slug:
            # Создаем для конкретного магазина
            try:
                store = Store.objects.get(slug=store_slug)
                self.create_staff_user_for_store(store)
            except Store.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Магазин с slug "{store_slug}" не найден'))
                return
        else:
            # Создаем для всех магазинов
            stores = Store.objects.filter(is_active=True)
            self.stdout.write(f'Найдено магазинов: {stores.count()}')

            for store in stores:
                self.create_staff_user_for_store(store)

        self.stdout.write(self.style.SUCCESS('\n✅ Готово!'))

    def create_staff_user_for_store(self, store):
        """Создает staff user и Employee для магазина"""
        staff_username = f"{store.slug}_staff"
        staff_password = "12345678"

        self.stdout.write(f'\n📝 Обработка магазина: {store.name} ({store.slug})')

        # Проверяем существование User
        try:
            staff_user = User.objects.get(username=staff_username)
            self.stdout.write(self.style.WARNING(f'   ⚠️  User уже существует: {staff_username}'))
        except User.DoesNotExist:
            # Создаем staff user
            staff_user = User.objects.create_user(
                username=staff_username,
                password=staff_password,
                first_name="Сотрудники",
                last_name=store.name,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'   ✅ User создан: {staff_username}'))

        # Проверяем существование Employee
        employee, created = Employee.objects.get_or_create(
            user=staff_user,
            store=store,
            defaults={
                'role': Employee.Role.STAFF,
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'   ✅ Employee создан для {staff_username}'))
        else:
            self.stdout.write(self.style.WARNING(f'   ⚠️  Employee уже существует'))

        # Выводим credentials
        self.stdout.write(f'   📋 Username: {staff_username}')
        self.stdout.write(f'   🔑 Password: {staff_password}')
