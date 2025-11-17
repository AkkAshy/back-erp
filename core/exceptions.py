"""
Custom exception handler и исключения для проекта.
"""

from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


class TenantRequiredException(APIException):
    """Исключение когда требуется tenant, но он не указан"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Магазин не указан. Пожалуйста, выберите магазин.'
    default_code = 'tenant_required'


class InactiveTenantException(APIException):
    """Исключение когда магазин неактивен"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Данный магазин неактивен.'
    default_code = 'inactive_tenant'


class PermissionDeniedException(APIException):
    """Исключение при отсутствии прав доступа"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'У вас нет прав для выполнения этого действия.'
    default_code = 'permission_denied'


class InvalidStoreException(APIException):
    """Исключение при попытке доступа к чужому магазину"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Вы не имеете доступа к данному магазину.'
    default_code = 'invalid_store'


class InsufficientStockException(APIException):
    """Исключение при недостатке товара на складе"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Недостаточно товара на складе.'
    default_code = 'insufficient_stock'


class DuplicateBarcodeException(APIException):
    """Исключение при дублировании штрих-кода"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Товар с таким штрих-кодом уже существует в вашем магазине.'
    default_code = 'duplicate_barcode'


def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений для DRF.

    Обрабатывает:
    - Стандартные DRF исключения
    - Django ValidationError
    - Кастомные исключения проекта
    - Неожиданные ошибки
    """

    # Получаем стандартный ответ от DRF
    response = exception_handler(exc, context)

    # Если DRF не обработал исключение
    if response is None:
        # Обрабатываем Django ValidationError
        if isinstance(exc, DjangoValidationError):
            if hasattr(exc, 'message_dict'):
                response_data = {
                    'status': 'error',
                    'code': 'validation_error',
                    'message': 'Ошибка валидации',
                    'errors': exc.message_dict
                }
            else:
                response_data = {
                    'status': 'error',
                    'code': 'validation_error',
                    'message': 'Ошибка валидации',
                    'errors': list(exc.messages)
                }

            from rest_framework.response import Response
            response = Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        # Обрабатываем Http404
        elif isinstance(exc, Http404):
            response_data = {
                'status': 'error',
                'code': 'not_found',
                'message': 'Объект не найден',
                'errors': {}
            }

            from rest_framework.response import Response
            response = Response(response_data, status=status.HTTP_404_NOT_FOUND)

        # Неожиданная ошибка
        else:
            logger.error(f"Unhandled exception: {exc}", exc_info=True)

            response_data = {
                'status': 'error',
                'code': 'internal_error',
                'message': 'Внутренняя ошибка сервера',
                'errors': {}
            }

            from rest_framework.response import Response
            response = Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Форматируем ответ в единообразный формат
    if response is not None:
        custom_response_data = {
            'status': 'error',
            'code': getattr(exc, 'default_code', 'error'),
            'message': str(exc) if str(exc) else 'Произошла ошибка',
            'errors': {}
        }

        # Если есть detail в response.data
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                custom_response_data['message'] = response.data['detail']
                custom_response_data['errors'] = {
                    k: v for k, v in response.data.items() if k != 'detail'
                }
            else:
                custom_response_data['errors'] = response.data

        elif isinstance(response.data, list):
            custom_response_data['errors'] = {'non_field_errors': response.data}

        response.data = custom_response_data

        # Логируем ошибки
        logger.warning(
            f"API Error: {custom_response_data['code']} - {custom_response_data['message']}",
            extra={
                'status_code': response.status_code,
                'path': context.get('request').path if context.get('request') else None,
            }
        )

    return response
