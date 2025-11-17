"""
URL routing для users app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from users.views import (
    RegisterView,
    CustomTokenObtainPairView,
    my_stores,
    me,
    change_password,
    StoreViewSet,
    EmployeeViewSet,
    UserViewSet
)

# Router для ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'stores', StoreViewSet, basename='store')
router.register(r'employees', EmployeeViewSet, basename='employee')

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/my-stores/', my_stores, name='my_stores'),
    path('auth/me/', me, name='me'),
    path('auth/change-password/', change_password, name='change_password'),

    # Alias for compatibility with old frontend
    path('profile/', me, name='profile'),  # ⭐ Alias for /auth/me/

    # ViewSet URLs
    path('', include(router.urls)),
]
