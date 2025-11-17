# coding: utf-8
"""
Views для управления задачами персонала.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, Count
from django.utils import timezone

from tasks.models import Task, TaskComment, TaskReport, TaskReportPhoto, TaskTemplate
from tasks.serializers import (
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateUpdateSerializer,
    TaskCommentSerializer,
    TaskReportSerializer,
    TaskReportCreateSerializer,
    TaskReportPhotoSerializer,
    TaskTemplateSerializer,
    CreateTaskFromTemplateSerializer,
)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления задачами.
    
    Сотрудники видят только свои задачи (назначенные им или созданные ими).
    Менеджеры видят все задачи.
    """
    
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'priority', 'assigned_to', 'created_by', 'category']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        employee = user.employee
        
        # Менеджеры и владельцы видят все задачи
        if employee.role in ['owner', 'manager']:
            return Task.objects.select_related('assigned_to', 'created_by').prefetch_related('comments', 'reports').all()
        
        # Остальные видят только свои задачи
        return Task.objects.select_related('assigned_to', 'created_by').prefetch_related('comments', 'reports').filter(
            Q(assigned_to=employee) | Q(created_by=employee)
        )
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TaskCreateUpdateSerializer
        return TaskDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.employee)
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Мои задачи (назначенные мне)"""
        employee = request.user.employee
        tasks = self.get_queryset().filter(assigned_to=employee)
        
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def created_by_me(self, request):
        """Задачи, созданные мной"""
        employee = request.user.employee
        tasks = self.get_queryset().filter(created_by=employee)
        
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Просроченные задачи"""
        tasks = self.get_queryset().filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress', 'on_review']
        )
        
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Задачи на сегодня"""
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timezone.timedelta(days=1)
        
        tasks = self.get_queryset().filter(
            due_date__gte=today_start,
            due_date__lt=today_end
        )
        
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Статистика по задачам"""
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'by_status': {},
            'by_priority': {},
            'overdue': queryset.filter(
                due_date__lt=timezone.now(),
                status__in=['pending', 'in_progress', 'on_review']
            ).count()
        }
        
        # По статусам
        status_stats = queryset.values('status').annotate(count=Count('id'))
        for stat in status_stats:
            stats['by_status'][stat['status']] = stat['count']
        
        # По приоритетам
        priority_stats = queryset.values('priority').annotate(count=Count('id'))
        for stat in priority_stats:
            stats['by_priority'][stat['priority']] = stat['count']
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Начать выполнение задачи"""
        task = self.get_object()
        
        if task.assigned_to != request.user.employee:
            return Response({
                'error': 'Только назначенный сотрудник может начать задачу'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if task.status != 'pending':
            return Response({
                'error': f'Задача в статусе {task.get_status_display()}, нельзя начать'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task.start_task()
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def submit_for_review(self, request, pk=None):
        """Отправить на проверку"""
        task = self.get_object()
        
        if task.assigned_to != request.user.employee:
            return Response({
                'error': 'Только назначенный сотрудник может отправить на проверку'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if task.status != 'in_progress':
            return Response({
                'error': f'Задача в статусе {task.get_status_display()}, нельзя отправить на проверку'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task.submit_for_review()
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Одобрить выполнение"""
        task = self.get_object()
        employee = request.user.employee
        
        # Одобрить может только создатель задачи или менеджер/владелец
        if task.created_by != employee and employee.role not in ['owner', 'manager']:
            return Response({
                'error': 'Недостаточно прав для одобрения'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if task.status != 'on_review':
            return Response({
                'error': f'Задача в статусе {task.get_status_display()}, нельзя одобрить'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task.approve()
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Отклонить выполнение"""
        task = self.get_object()
        employee = request.user.employee
        
        # Отклонить может только создатель задачи или менеджер/владелец
        if task.created_by != employee and employee.role not in ['owner', 'manager']:
            return Response({
                'error': 'Недостаточно прав для отклонения'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if task.status != 'on_review':
            return Response({
                'error': f'Задача в статусе {task.get_status_display()}, нельзя отклонить'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reason = request.data.get('reason', '')
        if not reason:
            return Response({
                'error': 'Укажите причину отклонения'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task.reject(reason)
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отменить задачу"""
        task = self.get_object()
        employee = request.user.employee
        
        # Отменить может только создатель или менеджер/владелец
        if task.created_by != employee and employee.role not in ['owner', 'manager']:
            return Response({
                'error': 'Недостаточно прав для отмены'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if task.status in ['completed', 'cancelled']:
            return Response({
                'error': 'Задача уже завершена или отменена'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task.status = 'cancelled'
        task.save()
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)


class TaskCommentViewSet(viewsets.ModelViewSet):
    """ViewSet для комментариев к задачам"""
    
    queryset = TaskComment.objects.select_related('task', 'author').all()
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['task']
    ordering = ['created_at']
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user.employee)


class TaskReportViewSet(viewsets.ModelViewSet):
    """ViewSet для отчётов о выполнении"""
    
    queryset = TaskReport.objects.select_related('task', 'submitted_by').prefetch_related('photos').all()
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ['task']
    ordering = ['-submitted_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TaskReportCreateSerializer
        return TaskReportSerializer
    
    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user.employee)


class TaskTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet для шаблонов задач"""
    
    queryset = TaskTemplate.objects.select_related('created_by').all()
    serializer_class = TaskTemplateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category', 'is_active']
    search_fields = ['title', 'description', 'category']
    ordering_fields = ['category', 'title', 'created_at']
    ordering = ['category', 'title']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.employee)
    
    @action(detail=True, methods=['post'])
    def create_task(self, request, pk=None):
        """Создать задачу из шаблона"""
        template = self.get_object()
        
        serializer = CreateTaskFromTemplateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        task = serializer.save()
        
        task_serializer = TaskDetailSerializer(task)
        return Response(task_serializer.data, status=status.HTTP_201_CREATED)
