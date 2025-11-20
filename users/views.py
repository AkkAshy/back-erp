"""
Views для аутентификации и управления пользователями.
"""

from rest_framework import status, generics, viewsets, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from users.models import Store, Employee
from users.serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    StoreSerializer,
    CreateStoreSerializer,
    EmployeeSerializer,
    CreateEmployeeSerializer,
    UserSerializer
)
from core.permissions import IsTenantUser, IsOwner, CanManageEmployees
import logging

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """
    Регистрация нового владельца магазина.

    POST /api/auth/register/

    Создает:
    - User (пользователь Django)
    - Store (магазин)
    - Employee (запись владельца)
    - PostgreSQL схему для магазина

    Возвращает JWT токены для входа.
    """

    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    @swagger_auto_schema(
        operation_description="""
        ## Регистрация владельца магазина в одном запросе

        Создаёт сразу:
        - Аккаунт пользователя
        - Магазин со всеми данными
        - Роль владельца
        - JWT токены для входа

        ### Минимальные обязательные поля:
        - first_name, owner_phone
        - username, password, password_confirm
        - store_name, store_address, store_phone

        Все остальные поля опциональны.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['first_name', 'owner_phone', 'username', 'password', 'password_confirm',
                     'store_name', 'store_address', 'store_phone'],
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя владельца'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Фамилия'),
                'middle_name': openapi.Schema(type=openapi.TYPE_STRING, description='Отчество'),
                'owner_phone': openapi.Schema(type=openapi.TYPE_STRING, description='Телефон: +998XXXXXXXXX'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email владельца'),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Логин (уникальный)'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль (мин. 8 символов)'),
                'password_confirm': openapi.Schema(type=openapi.TYPE_STRING, description='Повтор пароля'),
                'store_name': openapi.Schema(type=openapi.TYPE_STRING, description='Название магазина'),
                'store_slug': openapi.Schema(type=openapi.TYPE_STRING, description='ID магазина (авто)'),
                'store_address': openapi.Schema(type=openapi.TYPE_STRING, description='Адрес'),
                'store_city': openapi.Schema(type=openapi.TYPE_STRING, description='Город'),
                'store_region': openapi.Schema(type=openapi.TYPE_STRING, description='Область'),
                'store_phone': openapi.Schema(type=openapi.TYPE_STRING, description='Телефон: +998XXXXXXXXX'),
                'store_email': openapi.Schema(type=openapi.TYPE_STRING, description='Email магазина'),
                'store_legal_name': openapi.Schema(type=openapi.TYPE_STRING, description='Юр. название'),
                'store_tax_id': openapi.Schema(type=openapi.TYPE_STRING, description='ИНН'),
            },
            example={
                "first_name": "Иван",
                "last_name": "Петров",
                "middle_name": "Сергеевич",
                "owner_phone": "+998901234567",
                "email": "ivan@example.com",
                "username": "ivan_owner",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "store_name": "Супермаркет Азия",
                "store_address": "ул. Навои, д. 45",
                "store_city": "Ташкент",
                "store_region": "Ташкентская область",
                "store_phone": "+998712345678",
                "store_email": "info@asiamarket.uz",
                "store_legal_name": "ООО Супермаркет Азия",
                "store_tax_id": "123456789"
            }
        ),
        responses={
            201: openapi.Response(
                description="Успешная регистрация",
                examples={
                    "application/json": {
                        "status": "success",
                        "message": "Регистрация успешна",
                        "data": {
                            "user": {
                                "id": 1,
                                "username": "ivan_owner",
                                "email": "ivan@example.com",
                                "first_name": "Иван",
                                "last_name": "Петров",
                                "full_name": "Петров Иван"
                            },
                            "store": {
                                "id": 1,
                                "name": "Супермаркет Азия",
                                "slug": "asia_market",
                                "tenant_key": "asia_market_a3f4b2c1",
                                "description": ""
                            },
                            "employee": {
                                "id": 1,
                                "role": "owner",
                                "role_display": "Владелец",
                                "permissions": ["all"]
                            },
                            "tokens": {
                                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                                "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
                            }
                        }
                    }
                }
            ),
            400: "Ошибка валидации (пароли не совпадают, логин занят, и т.д.)"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Создаем пользователя, магазин и employee
        result = serializer.save()

        user = result['user']
        store = result['store']
        employee = result['employee']

        # Генерируем JWT токены (без store_id)
        refresh = RefreshToken.for_user(user)

        response_data = {
            'status': 'success',
            'message': 'Регистрация успешна',
            'data': {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': user.get_full_name() or user.username
                },
                'store': {
                    'id': store.id,
                    'name': store.name,
                    'slug': store.slug,
                    'tenant_key': store.tenant_key,  # ВАЖНО: клиент использует это для X-Tenant-Key
                    'schema_name': store.schema_name,
                    'description': store.description,
                    'address': store.address,
                    'city': store.city,
                    'region': store.region,
                    'phone': store.phone,
                    'email': store.email,
                    'legal_name': store.legal_name,
                    'tax_id': store.tax_id
                },
                'employee': {
                    'id': employee.id,
                    'role': employee.role,
                    'role_display': employee.get_role_display(),
                    'phone': employee.phone,
                    'permissions': employee.permissions
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }
            }
        }

        logger.info(f"New user registered: {user.username} with store: {store.name}")

        return Response(response_data, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Вход в систему.

    POST /api/users/auth/login/

    ВАЖНО: В новой архитектуре JWT НЕ содержит store_id.
    Клиент получает список доступных магазинов с tenant_key.
    Для работы с API используйте заголовок: X-Tenant-Key: <tenant_key>

    Параметры:
    - username: логин
    - password: пароль

    Возвращает:
    - JWT токены (без store_id)
    - Список доступных магазинов с tenant_key для каждого
    - Информацию о пользователе
    """

    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_description="Вход в систему (JWT без store_id, используйте X-Tenant-Key header для API запросов)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Логин'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Успешный вход",
                examples={
                    "application/json": {
                        "refresh": "...",
                        "access": "...",
                        "user": {
                            "id": 1,
                            "username": "owner1",
                            "email": "owner@example.com",
                            "full_name": "Иван Иванов"
                        },
                        "available_stores": [
                            {
                                "id": 1,
                                "name": "Мой Магазин",
                                "slug": "moy-magazin",
                                "tenant_key": "moy-magazin_a4b3c2d1",
                                "role": "owner",
                                "role_display": "Владелец",
                                "permissions": ["view_all", "create_all", "update_all", "delete_all"]
                            },
                            {
                                "id": 2,
                                "name": "Второй Магазин",
                                "slug": "vtoroi-magazin",
                                "tenant_key": "vtoroi-magazin_x7y8z9a0",
                                "role": "manager",
                                "role_display": "Менеджер",
                                "permissions": ["view_all", "create_all", "update_all"]
                            }
                        ],
                        "default_store": {
                            "tenant_key": "moy-magazin_a4b3c2d1",
                            "name": "Мой Магазин",
                            "role": "owner"
                        }
                    }
                }
            ),
            401: "Неверные учетные данные"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@swagger_auto_schema(
    method='get',
    operation_description="Получить список магазинов пользователя",
    responses={
        200: StoreSerializer(many=True)
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_stores(request):
    """
    Получить список всех магазинов, к которым пользователь имеет доступ.

    GET /api/auth/my-stores/
    """

    stores = Store.objects.filter(
        employees__user=request.user,
        employees__is_active=True,
        is_active=True
    ).distinct()

    serializer = StoreSerializer(stores, many=True)

    return Response({
        'status': 'success',
        'data': serializer.data
    })


@swagger_auto_schema(
    method='get',
    operation_description="Получить информацию о текущем пользователе",
    responses={200: "Информация о пользователе"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    Получить информацию о текущем пользователе и его контексте.

    GET /api/auth/me/

    Возвращает информацию о:
    - Пользователе
    - Текущем магазине
    - Роли и правах
    """

    user = request.user

    # Получаем информацию о сотруднике
    employee_data = None
    if hasattr(request, 'employee') and request.employee:
        employee_data = {
            'id': request.employee.id,
            'role': request.employee.role,
            'role_display': request.employee.get_role_display(),
            'permissions': request.employee.permissions,
            'phone': request.employee.phone,
            'photo': request.employee.photo.url if request.employee.photo else None
        }

    # Информация о магазине
    store_data = None
    if hasattr(request, 'tenant') and request.tenant:
        store_data = {
            'id': request.tenant.id,
            'name': request.tenant.name,
            'slug': request.tenant.slug,
            'tenant_key': request.tenant.tenant_key,
            'description': request.tenant.description
        }

    response_data = {
        'status': 'success',
        'data': {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name() or user.username
            },
            'store': store_data,
            'employee': employee_data
        }
    }

    return Response(response_data)


@swagger_auto_schema(
    method='post',
    operation_description="Сменить собственный пароль (опционально)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['old_password', 'new_password'],
        properties={
            'old_password': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Текущий пароль'
            ),
            'new_password': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Новый пароль (минимум 8 символов)'
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="Пароль успешно изменен",
            examples={
                "application/json": {
                    "status": "success",
                    "message": "Пароль успешно изменен"
                }
            }
        ),
        400: "Ошибка валидации или неверный текущий пароль",
        401: "Не авторизован"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Сменить собственный пароль (опционально).

    POST /api/users/auth/change-password/
    Body: {
        "old_password": "current_password",
        "new_password": "new_password_123"
    }

    Сотрудник может сам поменять пароль, но это НЕ обязательно.
    """

    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    # Проверка наличия полей
    if not old_password or not new_password:
        return Response({
            'status': 'error',
            'message': 'Поля old_password и new_password обязательны'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Проверка текущего пароля
    if not user.check_password(old_password):
        return Response({
            'status': 'error',
            'message': 'Неверный текущий пароль'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Валидация нового пароля
    try:
        from django.contrib.auth.password_validation import validate_password
        validate_password(new_password, user)
    except DjangoValidationError as e:
        return Response({
            'status': 'error',
            'message': 'Некорректный новый пароль',
            'errors': list(e.messages)
        }, status=status.HTTP_400_BAD_REQUEST)

    # Устанавливаем новый пароль
    user.set_password(new_password)
    user.save()

    logger.info(f"Password changed by user: {user.username}")

    return Response({
        'status': 'success',
        'message': 'Пароль успешно изменен'
    })


class StoreViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления магазинами.
    Владелец может создавать новые магазины и управлять существующими.

    Endpoints:
    - GET /api/users/stores/ - список магазинов пользователя
    - POST /api/users/stores/ - создать новый магазин
    - GET /api/users/stores/{id}/ - детали магазина
    - PUT/PATCH /api/users/stores/{id}/ - обновить магазин
    - DELETE /api/users/stores/{id}/ - удалить магазин
    - GET /api/users/stores/staff-credentials/ - получить credentials staff аккаунта
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Используем разные сериализаторы для создания и просмотра"""
        if self.action == 'create':
            return CreateStoreSerializer
        return StoreSerializer

    def get_queryset(self):
        """Пользователь видит только свои магазины (где он owner или сотрудник)"""
        user = self.request.user

        # Для создания/редактирования/удаления - только магазины владельца
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return Store.objects.filter(owner=user)

        # Для просмотра - все магазины где пользователь является сотрудником
        return Store.objects.filter(
            employees__user=user,
            employees__is_active=True
        ).distinct()

    def create(self, request, *args, **kwargs):
        """Создание нового магазина"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Создаем магазин
        store = serializer.save()

        # Возвращаем данные магазина с tenant_key и staff credentials
        response_data = {
            'status': 'success',
            'message': 'Магазин успешно создан',
            'data': {
                'store': {
                    'id': store.id,
                    'name': store.name,
                    'slug': store.slug,
                    'tenant_key': store.tenant_key,
                    'schema_name': store.schema_name,
                    'address': store.address,
                    'city': store.city,
                    'phone': store.phone,
                    'email': store.email,
                    'is_active': store.is_active,
                    'created_at': store.created_at
                },
                'staff_credentials': {
                    'username': f"{store.slug}_staff",
                    'password': '12345678',
                    'note': 'Общий аккаунт для всех сотрудников магазина'
                }
            }
        }

        logger.info(
            f"Store created: {store.name} by {request.user.username}"
        )

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='staff-credentials')
    def staff_credentials(self, request):
        """
        Получить учетные данные общего staff аккаунта для текущего магазина.

        Магазин определяется автоматически из X-Tenant-Key заголовка.
        Доступно только владельцу магазина.

        GET /api/users/stores/staff-credentials/

        Headers:
        - X-Tenant-Key: test_shop_4dfa7a5a
        - Authorization: Bearer {owner_token}

        Response:
        {
            "status": "success",
            "data": {
                "username": "test_shop_staff",
                "password": "12345678",
                "full_name": "Сотрудники Тестовый Магазин",
                "note": "Общий аккаунт для всех сотрудников магазина"
            }
        }
        """
        # Получаем текущий магазин из tenant context
        store = request.tenant

        if not store:
            return Response({
                'status': 'error',
                'code': 'bad_request',
                'message': 'Не указан X-Tenant-Key заголовок'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что пользователь - владелец магазина
        if store.owner != request.user:
            return Response({
                'status': 'error',
                'code': 'forbidden',
                'message': 'Только владелец магазина может просматривать учетные данные'
            }, status=status.HTTP_403_FORBIDDEN)

        # Формируем username общего аккаунта
        staff_username = f"{store.slug}_staff"

        # Проверяем, существует ли такой пользователь
        try:
            staff_user = User.objects.get(username=staff_username)

            return Response({
                'status': 'success',
                'data': {
                    'username': staff_username,
                    'password': '12345678',  # Стандартный пароль (может быть изменен в будущем)
                    'full_name': f"{staff_user.first_name} {staff_user.last_name}",
                    'is_active': staff_user.is_active,
                    'store_name': store.name,
                    'tenant_key': store.tenant_key,
                    'note': 'Общий аккаунт для всех сотрудников магазина. Используйте его для входа кассиров.'
                }
            })
        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'code': 'not_found',
                'message': f'Общий аккаунт для магазина "{store.name}" не найден. Возможно, он был удален.'
            }, status=status.HTTP_404_NOT_FOUND)


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления сотрудниками в магазине.
    Требует права manage_employees для создания/редактирования.

    Endpoints:
    - GET /api/users/employees/ - список сотрудников
    - POST /api/users/employees/ - создать сотрудника (owner/manager)
    - GET /api/users/employees/{id}/ - детали сотрудника
    - PUT/PATCH /api/users/employees/{id}/ - обновить сотрудника
    - DELETE /api/users/employees/{id}/ - удалить сотрудника
    - POST /api/users/employees/{id}/reset-password/ - сбросить пароль
    """

    permission_classes = [IsTenantUser, CanManageEmployees]

    def get_serializer_class(self):
        """Используем разные сериализаторы для создания и просмотра"""
        if self.action == 'create':
            return CreateEmployeeSerializer
        return EmployeeSerializer

    def get_queryset(self):
        """Показываем только сотрудников текущего магазина"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return Employee.objects.filter(
                store=self.request.tenant
            ).select_related('user', 'store')

        return Employee.objects.none()

    @swagger_auto_schema(
        operation_description="Создать нового сотрудника (только owner/manager)",
        request_body=CreateEmployeeSerializer,
        responses={
            201: openapi.Response(
                description="Сотрудник успешно создан",
                examples={
                    "application/json": {
                        "status": "success",
                        "message": "Сотрудник создан",
                        "data": {
                            "employee": {
                                "id": 2,
                                "full_name": "Иван Петров",
                                "username": "cashier1",
                                "role": "cashier",
                                "role_display": "Кассир",
                                "phone": "+998901234567",
                                "position": "Кассир",
                                "is_active": True
                            },
                            "credentials": {
                                "username": "cashier1",
                                "password": "secure_password_123"
                            }
                        }
                    }
                }
            ),
            400: "Ошибка валидации",
            403: "Недостаточно прав"
        }
    )
    def create(self, request, *args, **kwargs):
        """Создание сотрудника"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Создаем User + Employee
        result = serializer.save()

        employee = result['employee']
        username = result['username']
        password = result['password']

        # Возвращаем данные сотрудника + учетные данные для владельца
        response_data = {
            'status': 'success',
            'message': 'Сотрудник успешно создан',
            'data': {
                'employee': {
                    'id': employee.id,
                    'full_name': employee.full_name,
                    'username': username,
                    'email': employee.user.email if employee.user else None,
                    'role': employee.role,
                    'role_display': employee.get_role_display(),
                    'phone': employee.phone,
                    'position': employee.position,
                    'is_active': employee.is_active,
                    'hired_at': employee.hired_at
                },
                'credentials': {
                    'username': username,
                    'password': password  # Plaintext для владельца
                } if username and password else None
            }
        }

        logger.info(
            f"Employee created: {username} by {request.user.username} "
            f"in store: {request.tenant.name}"
        )

        return Response(response_data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        method='post',
        operation_description="Сбросить пароль сотрудника (только owner/manager)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'new_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Новый пароль (минимум 8 символов)'
                )
            },
            required=['new_password']
        ),
        responses={
            200: openapi.Response(
                description="Пароль успешно сброшен",
                examples={
                    "application/json": {
                        "status": "success",
                        "message": "Пароль сотрудника сброшен",
                        "data": {
                            "username": "cashier1",
                            "new_password": "new_secure_password"
                        }
                    }
                }
            ),
            400: "Ошибка валидации",
            403: "Недостаточно прав",
            404: "Сотрудник не найден"
        }
    )
    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        """
        Сброс пароля сотрудника владельцем/менеджером.

        POST /api/users/employees/{id}/reset-password/
        Body: {"new_password": "new_password_123"}
        """
        employee = self.get_object()
        new_password = request.data.get('new_password')

        if not new_password:
            return Response({
                'status': 'error',
                'message': 'Поле new_password обязательно'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Валидация пароля
        try:
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password)
        except DjangoValidationError as e:
            return Response({
                'status': 'error',
                'message': 'Некорректный пароль',
                'errors': list(e.messages)
            }, status=status.HTTP_400_BAD_REQUEST)

        # Устанавливаем новый пароль
        employee.user.set_password(new_password)
        employee.user.save()

        logger.info(
            f"Password reset for employee: {employee.user.username} "
            f"by {request.user.username} in store: {request.tenant.name}"
        )

        return Response({
            'status': 'success',
            'message': 'Пароль сотрудника успешно сброшен',
            'data': {
                'username': employee.user.username,
                'new_password': new_password  # Возвращаем plaintext для владельца
            }
        })

    @action(detail=False, methods=['get'], url_path='cashiers', permission_classes=[IsTenantUser])
    def get_cashiers(self, request):
        """
        Получить список кассиров для выбора при открытии смены.

        GET /api/users/employees/cashiers/

        Возвращает только активных кассиров текущего магазина.
        Доступно всем авторизованным пользователям магазина (включая staff).
        """
        if not hasattr(request, 'tenant') or not request.tenant:
            return Response({
                'status': 'error',
                'message': 'Не указан магазин'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Получаем всех активных кассиров (без user аккаунта)
        cashiers = Employee.objects.filter(
            store=request.tenant,
            role__in=[Employee.Role.CASHIER, Employee.Role.STOCKKEEPER],
            is_active=True,
            user__isnull=True  # Только кассиры без user аккаунта
        )

        cashiers_data = []
        for cashier in cashiers:
            cashiers_data.append({
                'id': cashier.id,
                'full_name': cashier.full_name,
                'phone': cashier.phone,
                'role': cashier.role,
            })

        return Response({
            'status': 'success',
            'data': cashiers_data
        })


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями/сотрудниками.

    GET - просмотр пользователей
    POST - создание сотрудника (делегирует в Employee)
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['username', 'first_name', 'last_name', 'date_joined']
    ordering = ['username']

    def get_queryset(self):
        """
        Возвращает пользователей текущего магазина.
        Показываем только тех пользователей, которые являются сотрудниками в текущем магазине.
        """
        # Проверяем что есть tenant_key (магазин)
        if not hasattr(self.request, 'tenant') or not self.request.tenant:
            return User.objects.none()

        # Получаем пользователей, которые являются сотрудниками в этом магазине
        queryset = User.objects.filter(
            employments__store=self.request.tenant,
            employments__is_active=True
        ).distinct()

        # Фильтр по имени (для совместимости с frontend)
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(
                Q(first_name__icontains=name) |
                Q(last_name__icontains=name) |
                Q(username__icontains=name)
            )

        return queryset

    def get_serializer_class(self):
        """Используем CreateEmployeeSerializer для создания"""
        if self.action == 'create':
            return CreateEmployeeSerializer
        return UserSerializer

    def create(self, request):
        """
        Создание нового сотрудника.
        Делегирует логику в CreateEmployeeSerializer.
        """
        # Проверяем что есть tenant (магазин)
        if not hasattr(request, 'tenant') or not request.tenant:
            return Response({
                'status': 'error',
                'code': 'forbidden',
                'message': 'Не указан магазин. Добавьте заголовок X-Tenant-Key',
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Получаем Employee текущего пользователя для этого магазина
        try:
            employee = Employee.objects.get(user=request.user, store=request.tenant)
        except Employee.DoesNotExist:
            return Response({
                'status': 'error',
                'code': 'forbidden',
                'message': 'У вас нет доступа к этому магазину',
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Проверяем роль
        if employee.role not in ['owner', 'manager']:
            return Response({
                'status': 'error',
                'code': 'forbidden',
                'message': 'Только владелец или менеджер может создавать сотрудников',
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Используем CreateEmployeeSerializer
        serializer = CreateEmployeeSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            try:
                result = serializer.save()

                # CreateEmployeeSerializer возвращает словарь с employee, username, password
                employee_obj = result.get('employee')
                username = result.get('username')
                password = result.get('password')

                # Перезагружаем employee с select_related для правильной сериализации
                employee_refreshed = Employee.objects.select_related('user', 'store').get(pk=employee_obj.pk)

                return Response({
                    'status': 'success',
                    'message': 'Сотрудник создан',
                    'data': {
                        'employee': EmployeeSerializer(employee_refreshed).data,
                        'username': username,
                        'initial_password': password  # Пароль для передачи сотруднику
                    }
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.error(f"Ошибка создания сотрудника: {str(e)}")
                return Response({
                    'status': 'error',
                    'code': 'creation_failed',
                    'message': f'Ошибка при создании сотрудника: {str(e)}',
                    'errors': {}
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'error',
            'code': 'validation_error',
            'message': 'Ошибка валидации',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='update-employee')
    def update_employee_info(self, request, pk=None):
        """
        Обновить информацию об Employee для конкретного пользователя.

        PATCH /api/users/users/{user_id}/update-employee/
        Body: {
            "role": "manager",
            "phone": "+998901234567",
            "position": "Менеджер зала",
            "is_active": true
        }
        """
        # Проверяем что есть tenant
        if not hasattr(request, 'tenant') or not request.tenant:
            return Response({
                'status': 'error',
                'code': 'forbidden',
                'message': 'Не указан магазин. Добавьте заголовок X-Tenant-Key',
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Получаем Employee текущего пользователя
        try:
            current_employee = Employee.objects.get(user=request.user, store=request.tenant)
        except Employee.DoesNotExist:
            return Response({
                'status': 'error',
                'code': 'forbidden',
                'message': 'У вас нет доступа к этому магазину',
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Проверяем роль (только owner/manager могут обновлять)
        if current_employee.role not in ['owner', 'manager']:
            return Response({
                'status': 'error',
                'code': 'forbidden',
                'message': 'Только владелец или менеджер может обновлять сотрудников',
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Получаем пользователя которого нужно обновить
        user = self.get_object()

        # Получаем Employee для этого пользователя в текущем магазине
        try:
            employee = Employee.objects.get(user=user, store=request.tenant)
        except Employee.DoesNotExist:
            return Response({
                'status': 'error',
                'code': 'not_found',
                'message': 'Сотрудник не найден в этом магазине',
                'errors': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Обновляем только разрешенные поля
        allowed_fields = ['role', 'phone', 'position', 'sex', 'is_active']
        updated_fields = []

        for field in allowed_fields:
            if field in request.data:
                setattr(employee, field, request.data[field])
                updated_fields.append(field)

        if updated_fields:
            employee.save(update_fields=updated_fields)

            logger.info(
                f"Employee {employee.id} updated by {request.user.username}. "
                f"Fields: {', '.join(updated_fields)}"
            )

        # Перезагружаем с select_related для правильной сериализации
        employee = Employee.objects.select_related('user', 'store').get(pk=employee.pk)

        return Response({
            'status': 'success',
            'message': 'Информация о сотруднике обновлена',
            'data': {
                'employee': EmployeeSerializer(employee).data
            }
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='update-profile')
    def update_profile(self, request, pk=None):
        """
        Обновить базовую информацию пользователя (имя, email).

        PATCH /api/users/users/{user_id}/update-profile/
        Body: {
            "first_name": "Иван",
            "last_name": "Петров",
            "email": "ivan@example.com",
            "username": "ivan123"
        }

        Только owner и manager могут обновлять профили других сотрудников.
        """
        # Проверяем что есть tenant
        if not hasattr(request, 'tenant') or not request.tenant:
            return Response({
                'status': 'error',
                'code': 'forbidden',
                'message': 'Не указан магазин. Добавьте заголовок X-Tenant-Key',
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Получаем Employee текущего пользователя
        try:
            current_employee = Employee.objects.get(user=request.user, store=request.tenant)
        except Employee.DoesNotExist:
            return Response({
                'status': 'error',
                'code': 'forbidden',
                'message': 'У вас нет доступа к этому магазину',
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Получаем пользователя которого нужно обновить
        user = self.get_object()

        # Проверяем права: можно редактировать себя или если ты owner/manager
        is_self = user.id == request.user.id
        can_edit_others = current_employee.role in ['owner', 'manager']

        if not is_self and not can_edit_others:
            return Response({
                'status': 'error',
                'code': 'forbidden',
                'message': 'Вы можете редактировать только свой профиль',
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Проверяем что пользователь есть в текущем магазине
        try:
            Employee.objects.get(user=user, store=request.tenant)
        except Employee.DoesNotExist:
            return Response({
                'status': 'error',
                'code': 'not_found',
                'message': 'Сотрудник не найден в этом магазине',
                'errors': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Обновляем только разрешенные поля User
        allowed_fields = ['first_name', 'last_name', 'email', 'username']
        updated_fields = []

        for field in allowed_fields:
            if field in request.data:
                value = request.data[field]

                # Проверка уникальности username
                if field == 'username' and value != user.username:
                    if User.objects.filter(username=value).exists():
                        return Response({
                            'status': 'error',
                            'code': 'validation_error',
                            'message': 'Пользователь с таким username уже существует',
                            'errors': {'username': ['Этот username уже занят']}
                        }, status=status.HTTP_400_BAD_REQUEST)

                # Проверка уникальности email
                if field == 'email' and value and value != user.email:
                    if User.objects.filter(email=value).exists():
                        return Response({
                            'status': 'error',
                            'code': 'validation_error',
                            'message': 'Пользователь с таким email уже существует',
                            'errors': {'email': ['Этот email уже занят']}
                        }, status=status.HTTP_400_BAD_REQUEST)

                setattr(user, field, value)
                updated_fields.append(field)

        if updated_fields:
            user.save(update_fields=updated_fields)

            logger.info(
                f"User profile {user.id} updated by {request.user.username}. "
                f"Fields: {', '.join(updated_fields)}"
            )

        # Возвращаем обновленные данные
        serializer = self.get_serializer(user)

        return Response({
            'status': 'success',
            'message': 'Профиль пользователя обновлен',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='change-password')
    def change_password(self, request, pk=None):
        """
        Изменить пароль сотрудника.

        POST /api/users/users/{user_id}/change-password/
        Body: {
            "new_password": "NewSecurePass123!"
        }

        Только owner и manager могут менять пароли других сотрудников.
        """
        # Проверяем что есть tenant
        if not hasattr(request, 'tenant') or not request.tenant:
            return Response({
                'status': 'error',
                'code': 'forbidden',
                'message': 'Не указан магазин. Добавьте заголовок X-Tenant-Key',
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Получаем Employee текущего пользователя
        try:
            current_employee = Employee.objects.get(user=request.user, store=request.tenant)
        except Employee.DoesNotExist:
            return Response({
                'status': 'error',
                'code': 'forbidden',
                'message': 'У вас нет доступа к этому магазину',
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Проверяем роль (только owner/manager могут менять пароли)
        if current_employee.role not in ['owner', 'manager']:
            return Response({
                'status': 'error',
                'code': 'forbidden',
                'message': 'Только владелец или менеджер может менять пароли сотрудников',
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)

        # Получаем пользователя которому нужно изменить пароль
        user = self.get_object()

        # Проверяем что пользователь есть в текущем магазине
        try:
            Employee.objects.get(user=user, store=request.tenant)
        except Employee.DoesNotExist:
            return Response({
                'status': 'error',
                'code': 'not_found',
                'message': 'Сотрудник не найден в этом магазине',
                'errors': {}
            }, status=status.HTTP_404_NOT_FOUND)

        # Валидация нового пароля
        new_password = request.data.get('new_password')

        if not new_password:
            return Response({
                'status': 'error',
                'code': 'validation_error',
                'message': 'Укажите новый пароль',
                'errors': {'new_password': ['Это поле обязательно']}
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({
                'status': 'error',
                'code': 'validation_error',
                'message': 'Пароль слишком короткий',
                'errors': {'new_password': ['Пароль должен содержать минимум 8 символов']}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Меняем пароль
        user.set_password(new_password)
        user.save()

        logger.info(
            f"Password changed for user {user.username} (ID: {user.id}) "
            f"by {request.user.username} in store {request.tenant.name}"
        )

        return Response({
            'status': 'success',
            'message': f'Пароль для пользователя {user.username} успешно изменен',
            'data': {
                'user_id': user.id,
                'username': user.username
            }
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        """Обновление пользователя запрещено через этот эндпоинт"""
        user_id = kwargs.get('pk')
        return Response({
            'status': 'error',
            'code': 'method_not_allowed',
            'message': 'Для обновления сотрудника используйте PATCH /api/users/users/{id}/update-employee/',
            'hint': f'Попробуйте: PATCH /api/users/users/{user_id}/update-employee/',
            'errors': {}
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        """PATCH также запрещен - перенаправляем на update"""
        return self.update(request, *args, **kwargs)

    def destroy(self, request, pk=None):  # noqa: ARG002
        """Удаление пользователя запрещено через этот эндпоинт"""
        return Response({
            'status': 'error',
            'code': 'method_not_allowed',
            'message': 'Используйте /api/users/employees/{id}/ для удаления сотрудника',
            'errors': {}
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
