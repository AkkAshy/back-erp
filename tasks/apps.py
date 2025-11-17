# coding: utf-8
"""
Конфигурация приложения tasks.
"""

from django.apps import AppConfig


class TasksConfig(AppConfig):
    """Конфигурация приложения Tasks"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'
    verbose_name = 'Задачи персонала'
    
    def ready(self):
        """Регистрируем signals при старте приложения."""
        import tasks.signals
