# coding: utf-8
"""
URL конфигурация для задач персонала.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tasks import views

app_name = 'tasks'

router = DefaultRouter()
router.register(r'tasks', views.TaskViewSet, basename='tasks')
router.register(r'comments', views.TaskCommentViewSet, basename='comments')
router.register(r'reports', views.TaskReportViewSet, basename='reports')
router.register(r'templates', views.TaskTemplateViewSet, basename='templates')

urlpatterns = [
    path('', include(router.urls)),
]
