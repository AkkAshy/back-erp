# coding: utf-8
"""
Конфигурация приложения analytics.
"""

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    """Конфигурация приложения Analytics"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'
    verbose_name = 'Аналитика и отчётность'
    
    def ready(self):
        """Регистрируем signals при старте приложения."""
        import analytics.signals
