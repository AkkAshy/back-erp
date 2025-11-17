"""
URL configuration for ERP v2 project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI schema
schema_view = get_schema_view(
    openapi.Info(
        title="ERP v2 POS API",
        default_version='v1',
        description="""
        # Мультитенантная POS система

        ## Аутентификация
        API использует JWT токены для аутентификации.

        ### Как получить токен:
        1. **Регистрация**: POST `/api/users/auth/register/`
        2. **Вход**: POST `/api/users/auth/login/`

        ### Использование токена:
        Добавьте заголовок в каждый запрос:
        ```
        Authorization: Bearer <ваш_access_token>
        ```

        ## Мультитенантность
        Каждый пользователь может иметь доступ к нескольким магазинам.
        - `store_id` автоматически извлекается из JWT токена
        - Для переключения между магазинами: POST `/api/users/auth/switch-store/`

        ## Роли
        - **owner** - владелец магазина (полный доступ)
        - **manager** - менеджер (управление товарами, продажами, клиентами)
        - **cashier** - кассир (только продажи)
        - **stockkeeper** - складчик (управление товарами и остатками)
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@erp-v2.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # API endpoints
    path('api/users/', include('users.urls', namespace='users')),
    path('api/products/', include('products.urls', namespace='products')),
    path('api/sales/', include('sales.urls', namespace='sales')),
    path('api/customers/', include('customers.urls')),
    path('api/analytics/', include('analytics.urls', namespace='analytics')),
    path('api/tasks/', include('tasks.urls', namespace='tasks')),
]

# Static and media files (только в dev режиме)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
