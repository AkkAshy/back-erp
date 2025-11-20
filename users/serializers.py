"""
Serializers для пользователей, магазинов и аутентификации.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.text import slugify
from users.models import Store, Employee
from core.schema_utils import SchemaManager
import logging

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для списка пользователей с информацией об Employee"""

    full_name = serializers.CharField(source='get_full_name', read_only=True)
    employee_info = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'is_active', 'date_joined', 'employee_info'
        ]
        read_only_fields = ['id', 'date_joined']

    def get_employee_info(self, obj):
        """
        Получить информацию об Employee для текущего магазина.
        Возвращает данные о роли, телефоне и т.д.
        """
        request = self.context.get('request')

        # Проверяем что есть tenant (магазин)
        if not request or not hasattr(request, 'tenant') or not request.tenant:
            return None

        try:
            # Получаем Employee для текущего магазина
            employee = Employee.objects.select_related('store').get(
                user=obj,
                store=request.tenant
            )

            return {
                'id': employee.id,
                'role': employee.role,
                'role_display': employee.get_role_display(),
                'phone': employee.phone,
                'position': employee.position,
                'sex': employee.sex,
                'sex_display': employee.get_sex_display() if employee.sex else None,
                'is_active': employee.is_active,
                'hired_at': employee.hired_at,
                'photo': employee.photo.url if employee.photo else None
            }
        except Employee.DoesNotExist:
            return None



class EmployeeSerializer(serializers.ModelSerializer):
    """Сериализатор для Employee"""

    full_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    sex_display = serializers.CharField(source='get_sex_display', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'user', 'full_name', 'username', 'email',
            'store', 'role', 'role_display', 'phone', 'photo',
            'position', 'sex', 'sex_display', 'is_active', 'hired_at', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'hired_at', 'created_at']

    def get_full_name(self, obj):
        """Получить полное имя - из User или из Employee"""
        if obj.user:
            return obj.user.get_full_name()
        return obj.full_name  # Employee.full_name property

    def get_username(self, obj):
        """Получить username - только если есть User"""
        return obj.user.username if obj.user else None

    def get_email(self, obj):
        """Получить email - только если есть User"""
        return obj.user.email if obj.user else None


class CreateEmployeeSerializer(serializers.Serializer):
    """
    Сериализатор для создания нового сотрудника владельцем/менеджером.
    Создает: User + Employee в одной транзакции.

    Особенности:
    - Владелец/менеджер создает сотрудника с паролем
    - Пароль хранится хешированным
    - Владелец может сбросить пароль в любой момент
    - Сотрудник может сменить пароль (опционально)
    """

    # Данные пользователя (опциональны для кассиров)
    username = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        help_text="Логин для входа в систему (опционально для кассиров)"
    )
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={'input_type': 'password'},
        help_text="Пароль сотрудника (минимум 8 символов, опционально для кассиров)"
    )
    first_name = serializers.CharField(
        max_length=150,
        help_text="Имя сотрудника"
    )
    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        help_text="Фамилия сотрудника"
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="Email сотрудника"
    )

    # Данные Employee
    role = serializers.ChoiceField(
        choices=Employee.Role.choices,
        help_text="Роль сотрудника: manager, cashier, stockkeeper"
    )
    phone = serializers.RegexField(
        regex=r'^\+998\d{9}$',
        required=False,
        allow_blank=True,
        help_text="Телефон: +998XXXXXXXXX"
    )
    position = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Должность (например: Кассир, Менеджер зала)"
    )

    def validate_username(self, value):
        """Проверка уникальности username"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким логином уже существует")
        return value

    def validate_role(self, value):
        """Владелец не может быть создан через этот endpoint"""
        if value == 'owner':
            raise serializers.ValidationError(
                "Роль 'owner' может быть только у владельца магазина. "
                "Используйте регистрацию для создания владельца."
            )
        return value

    def validate_password(self, value):
        """Валидация пароля"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """Валидация: для не-кассиров требуется username/password"""
        role = attrs.get('role')
        username = attrs.get('username')
        password = attrs.get('password')

        # Для всех ролей кроме кассира требуется аккаунт
        if role != 'cashier' and (not username or not password):
            raise serializers.ValidationError({
                'username': 'Для этой роли требуется создание аккаунта (username и password)'
            })

        # Для кассиров аккаунт опционален
        if role == 'cashier':
            # Если указан username, то нужен и password
            if username and not password:
                raise serializers.ValidationError({
                    'password': 'Если указан username, необходимо указать password'
                })
            if password and not username:
                raise serializers.ValidationError({
                    'username': 'Если указан password, необходимо указать username'
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """
        Создание Employee с опциональным User аккаунтом.
        Store берется из request.tenant (установлен middleware).
        """

        # Получаем store из контекста
        request = self.context.get('request')
        if not hasattr(request, 'tenant') or not request.tenant:
            raise serializers.ValidationError("Не удалось определить магазин. Проверьте X-Tenant-Key header.")

        store = request.tenant
        username = validated_data.get('username')
        password = validated_data.get('password')

        try:
            user = None

            # 1. Создаем User только если указаны username/password
            if username and password:
                user = User.objects.create_user(
                    username=username,
                    password=password,  # Хешируется автоматически
                    first_name=validated_data['first_name'],
                    last_name=validated_data.get('last_name', ''),
                    email=validated_data.get('email', ''),
                    is_active=True
                )
                logger.info(f"Created user for employee: {user.username}")

            # 2. Создаем Employee запись (с user или без)
            employee = Employee.objects.create(
                user=user,  # Может быть None для кассиров
                store=store,
                first_name=validated_data['first_name'],
                last_name=validated_data.get('last_name', ''),
                role=validated_data['role'],
                phone=validated_data.get('phone', ''),
                position=validated_data.get('position', ''),
                is_active=True
            )

            logger.info(
                f"Created employee: {employee.full_name} ({employee.role}) "
                f"for store: {store.name} by {request.user.username}"
            )

            # 3. Возвращаем данные
            return {
                'employee': employee,
                'username': username or None,
                'password': password or None  # Plaintext для владельца (если был создан)
            }

        except Exception as e:
            logger.error(f"Error creating employee: {e}", exc_info=True)
            raise serializers.ValidationError(f"Ошибка при создании сотрудника: {str(e)}")


class CreateStoreSerializer(serializers.Serializer):
    """
    Сериализатор для создания нового магазина существующим владельцем.
    Автоматически создает Store + Employee(owner) + Staff User + Schema.
    """

    name = serializers.CharField(
        max_length=255,
        help_text="Название магазина"
    )
    slug = serializers.SlugField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Уникальный идентификатор магазина (если пусто - создастся автоматически)"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Описание магазина"
    )
    address = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Адрес магазина"
    )
    city = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Город"
    )
    region = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Область/регион"
    )
    phone = serializers.RegexField(
        regex=r'^\+998\d{9}$',
        required=False,
        allow_blank=True,
        help_text="Телефон магазина: +998XXXXXXXXX"
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="Email магазина"
    )
    legal_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Юридическое название"
    )
    tax_id = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text="ИНН"
    )

    def validate_slug(self, value):
        """Валидация slug"""
        if value:
            # Проверка формата
            if not value.replace('_', '').isalnum():
                raise serializers.ValidationError(
                    "Слаг может содержать только буквы, цифры и подчеркивание"
                )

            # Не может начинаться с цифры
            if value[0].isdigit():
                raise serializers.ValidationError("Слаг не может начинаться с цифры")

            # Проверка уникальности
            if Store.objects.filter(slug=value.lower()).exists():
                raise serializers.ValidationError("Магазин с таким slug уже существует")

            return value.lower()

        return value

    def validate(self, data):
        """Генерация slug если не указан"""
        if not data.get('slug'):
            base_slug = slugify(data['name'])
            slug = base_slug
            counter = 1

            # Проверяем уникальность
            while Store.objects.filter(slug=slug).exists():
                slug = f"{base_slug}_{counter}"
                counter += 1

            data['slug'] = slug

        return data

    @transaction.atomic
    def create(self, validated_data):
        """
        Создание Store + Employee(owner) + Staff User в одной транзакции.
        Owner берется из request.user.
        """
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Не удалось определить пользователя")

        owner = request.user

        try:
            # 1. Создаем магазин
            store = Store.objects.create(
                name=validated_data['name'],
                slug=validated_data['slug'],
                description=validated_data.get('description', ''),
                address=validated_data.get('address', ''),
                city=validated_data.get('city', ''),
                region=validated_data.get('region', ''),
                phone=validated_data.get('phone', ''),
                email=validated_data.get('email', ''),
                legal_name=validated_data.get('legal_name', ''),
                tax_id=validated_data.get('tax_id', ''),
                owner=owner,
                is_active=True
            )

            logger.info(f"Created store: {store.name} ({store.slug}) by {owner.username}")

            # 2. Создаем PostgreSQL схему
            if SchemaManager.create_schema(store.schema_name):
                logger.info(f"Created schema: {store.schema_name}")
            else:
                logger.warning(f"Failed to create schema for store: {store.slug}")

            # 3. Employee(owner) и Staff User создаются автоматически через signal

            logger.info(f"Store creation completed: {store.name}")

            return store

        except Exception as e:
            logger.error(f"Error creating store: {e}", exc_info=True)
            raise serializers.ValidationError(f"Ошибка при создании магазина: {str(e)}")


class StoreSerializer(serializers.ModelSerializer):
    """Сериализатор для Store (для GET/UPDATE)"""

    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    employee_count = serializers.IntegerField(read_only=True)
    active_employee_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Store
        fields = [
            'id', 'name', 'slug', 'description',
            'address', 'city', 'region',
            'phone', 'email',
            'legal_name', 'tax_id',
            'tenant_key', 'schema_name', 'is_active',
            'created_at', 'updated_at',
            'owner', 'owner_name',
            'employee_count', 'active_employee_count'
        ]
        read_only_fields = ['id', 'tenant_key', 'schema_name', 'created_at', 'updated_at', 'owner']

    def validate_slug(self, value):
        """Валидация slug"""
        # Проверка формата
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Слаг может содержать только буквы, цифры и подчеркивание"
            )

        # Не может начинаться с цифры
        if value[0].isdigit():
            raise serializers.ValidationError("Слаг не может начинаться с цифры")

        return value.lower()


class UserRegistrationSerializer(serializers.Serializer):
    """
    Сериализатор для регистрации нового владельца магазина.
    Создает: User + Store + Employee(owner) - всё в одном запросе!

    Владелец заполняет одну форму с полными данными и сразу получает:
    - Аккаунт пользователя
    - Магазин с настройками
    - Доступ как владелец
    - JWT токены для входа
    """

    # ===== ЛИЧНЫЕ ДАННЫЕ ВЛАДЕЛЬЦА =====
    first_name = serializers.CharField(
        max_length=150,
        help_text="Имя владельца"
    )
    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        help_text="Фамилия владельца"
    )
    middle_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        help_text="Отчество владельца"
    )
    owner_phone = serializers.RegexField(
        regex=r'^\+998\d{9}$',
        help_text="Личный телефон владельца: +998XXXXXXXXX"
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="Email владельца"
    )

    # ===== ДАННЫЕ ДЛЯ ВХОДА =====
    username = serializers.CharField(
        max_length=150,
        help_text="Логин для входа в систему"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Пароль (минимум 8 символов)"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Повторите пароль"
    )

    # ===== ДАННЫЕ МАГАЗИНА =====
    store_name = serializers.CharField(
        max_length=255,
        help_text="Название магазина (например: 'Магазин №1', 'Супермаркет Азия')"
    )
    store_slug = serializers.SlugField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Уникальный идентификатор магазина (если пусто - создастся автоматически)"
    )
    store_description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Краткое описание магазина"
    )
    store_address = serializers.CharField(
        max_length=500,
        help_text="Адрес магазина (город, улица, дом)"
    )
    store_phone = serializers.RegexField(
        regex=r'^\+998\d{9}$',
        help_text="Телефон магазина: +998XXXXXXXXX"
    )
    store_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="Email магазина (для чеков и уведомлений)"
    )

    # Дополнительные поля магазина
    store_city = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Город"
    )
    store_region = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Область/регион"
    )
    store_tax_id = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text="ИНН магазина"
    )
    store_legal_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Юридическое название организации"
    )

    def validate_username(self, value):
        """Проверка уникальности username"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким логином уже существует")
        return value

    def validate_store_slug(self, value):
        """Проверка уникальности slug магазина"""
        if value and Store.objects.filter(slug=value).exists():
            raise serializers.ValidationError("Магазин с таким идентификатором уже существует")
        return value

    def validate(self, data):
        """Валидация всех данных"""

        # Проверка совпадения паролей
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Пароли не совпадают"
            })

        # Валидация пароля Django валидаторами
        try:
            validate_password(data['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })

        # Генерация slug если не указан
        if not data.get('store_slug'):
            base_slug = slugify(data['store_name'])
            slug = base_slug
            counter = 1

            # Проверяем уникальность
            while Store.objects.filter(slug=slug).exists():
                slug = f"{base_slug}_{counter}"
                counter += 1

            data['store_slug'] = slug

        return data

    @transaction.atomic
    def create(self, validated_data):
        """
        Создание User + Store + Employee в одной транзакции.
        Все данные из одной формы регистрации.
        """

        try:
            # 1. Создаем пользователя
            user = User.objects.create_user(
                username=validated_data['username'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data.get('last_name', ''),
                email=validated_data.get('email', ''),
                is_staff=True,  # Владелец получает доступ к админке
                is_active=True
            )

            logger.info(f"Created user: {user.username}")

            # 2. Создаем магазин со всеми данными
            store = Store.objects.create(
                name=validated_data['store_name'],
                slug=validated_data['store_slug'],
                description=validated_data.get('store_description', ''),
                address=validated_data.get('store_address', ''),
                city=validated_data.get('store_city', ''),
                region=validated_data.get('store_region', ''),
                phone=validated_data.get('store_phone', ''),
                email=validated_data.get('store_email', ''),
                legal_name=validated_data.get('store_legal_name', ''),
                tax_id=validated_data.get('store_tax_id', ''),
                owner=user,
                is_active=True
            )

            logger.info(f"Created store: {store.name} ({store.slug})")

            # 3. Создаем PostgreSQL схему (если используется PostgreSQL)
            if SchemaManager.create_schema(store.schema_name):
                logger.info(f"Created schema: {store.schema_name}")
            else:
                logger.warning(f"Failed to create schema for store: {store.slug}")

            # 4. Employee запись создается автоматически через сигнал post_save
            # Обновим телефон и отчество владельца
            employee = Employee.objects.get(user=user, store=store)
            if validated_data.get('owner_phone'):
                employee.phone = validated_data['owner_phone']
                employee.save(update_fields=['phone'])

            logger.info(f"Registration completed for: {user.username}")

            return {
                'user': user,
                'store': store,
                'employee': employee
            }

        except Exception as e:
            logger.error(f"Error during registration: {e}", exc_info=True)
            raise serializers.ValidationError(f"Ошибка при регистрации: {str(e)}")


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Кастомный сериализатор для JWT токенов.

    ВАЖНО: В новой схемной архитектуре JWT НЕ содержит store_id.
    Вместо этого клиент получает список доступных магазинов с их tenant_key.
    При каждом запросе клиент передает X-Tenant-Key в header.
    """

    def validate(self, attrs):
        """Валидация и получение информации о пользователе"""

        # Получаем стандартные токены
        data = super().validate(attrs)

        # Получаем пользователя
        user = self.user

        # Добавляем информацию о пользователе в ответ
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name() or user.username
        }

        # Получаем список всех магазинов пользователя с tenant_key
        stores = Employee.objects.filter(
            user=user,
            is_active=True,
            store__is_active=True
        ).select_related('store')

        if not stores.exists():
            raise serializers.ValidationError({
                'non_field_errors': 'У вас нет доступа ни к одному активному магазину'
            })

        # Формируем список магазинов с tenant_key
        available_stores = []
        for emp in stores:
            store_data = {
                'id': emp.store.id,
                'name': emp.store.name,
                'slug': emp.store.slug,
                'tenant_key': emp.store.tenant_key,  # ВАЖНО: клиент будет использовать это
                'role': emp.role,
                'role_display': emp.get_role_display(),
                'permissions': emp.permissions
            }

            # Если роль STAFF, добавляем список кассиров для выбора
            if emp.role == Employee.Role.STAFF:
                cashiers = Employee.objects.filter(
                    store=emp.store,
                    role__in=[Employee.Role.CASHIER, Employee.Role.STOCKKEEPER],
                    is_active=True,
                    user__isnull=True  # Только кассиры без user аккаунта
                ).values('id', 'first_name', 'last_name', 'phone', 'role')

                store_data['cashiers'] = [
                    {
                        'id': c['id'],
                        'full_name': f"{c['last_name']} {c['first_name']}".strip(),
                        'phone': c['phone'],
                        'role': c['role']
                    }
                    for c in cashiers
                ]

            available_stores.append(store_data)

        data['available_stores'] = available_stores

        # Указываем первый магазин как дефолтный (для удобства)
        default_store = available_stores[0]
        data['default_store'] = {
            'tenant_key': default_store['tenant_key'],
            'name': default_store['name'],
            'role': default_store['role']
        }

        logger.info(f"User {user.username} logged in. Available stores: {len(available_stores)}")

        return data

    @classmethod
    def get_token(cls, user):
        """
        Переопределяем для добавления базовых claims.
        ВАЖНО: НЕ добавляем store_id в токен!
        """
        token = super().get_token(user)

        # Базовые claims
        token['username'] = user.username
        token['email'] = user.email
        token['full_name'] = user.get_full_name() or user.username

        return token
