# coding: utf-8
"""
Модели для управления задачами персонала.

Включает задачи, комментарии и фото-отчёты.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


def task_photo_path(instance, filename):
    """Путь для загрузки фото отчётов."""
    return f'tasks/reports/{instance.task.id}/{filename}'


class Task(models.Model):
    """Задача для сотрудника"""
    
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочно'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('in_progress', 'В работе'),
        ('on_review', 'На проверке'),
        ('completed', 'Выполнена'),
        ('rejected', 'Отклонена'),
        ('cancelled', 'Отменена'),
    ]
    
    # Основные поля
    title = models.CharField(max_length=200, verbose_name="Название задачи")
    description = models.TextField(verbose_name="Описание")
    
    # Назначение
    assigned_to = models.ForeignKey(
        'users.Employee',
        on_delete=models.CASCADE,
        related_name='assigned_tasks',
        verbose_name="Назначена"
    )
    created_by = models.ForeignKey(
        'users.Employee',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name="Создал"
    )
    
    # Приоритет и статус
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Приоритет"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )
    
    # Сроки
    due_date = models.DateTimeField(verbose_name="Срок выполнения")
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Ожидаемое время (часов)"
    )
    
    # Категория (опционально)
    category = models.CharField(max_length=100, blank=True, verbose_name="Категория")
    
    # Даты
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Начата")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Завершена")
    
    # Отклонение
    rejection_reason = models.TextField(blank=True, verbose_name="Причина отклонения")
    
    class Meta:
        db_table = 'tasks_task'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['created_by', 'created_at']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['due_date']),
            models.Index(fields=['category']),
        ]
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    @property
    def is_overdue(self):
        """Просрочена ли задача."""
        if self.status in ['completed', 'cancelled']:
            return False
        return timezone.now() > self.due_date
    
    @property
    def time_left(self):
        """Оставшееся время."""
        if self.status in ['completed', 'cancelled']:
            return None
        delta = self.due_date - timezone.now()
        return delta if delta.total_seconds() > 0 else None
    
    def start_task(self):
        """Начать выполнение задачи."""
        if self.status == 'pending':
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.save()
    
    def submit_for_review(self):
        """Отправить на проверку."""
        if self.status == 'in_progress':
            self.status = 'on_review'
            self.save()
    
    def approve(self):
        """Одобрить выполнение."""
        if self.status == 'on_review':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
    
    def reject(self, reason):
        """Отклонить выполнение."""
        if self.status == 'on_review':
            self.status = 'rejected'
            self.rejection_reason = reason
            self.save()


class TaskComment(models.Model):
    """Комментарий к задаче"""
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Задача"
    )
    author = models.ForeignKey(
        'users.Employee',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Автор"
    )
    text = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")
    
    class Meta:
        db_table = 'tasks_comment'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['task', 'created_at']),
        ]
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
    
    def __str__(self):
        return f"Комментарий к {self.task.title} от {self.author}"


class TaskReport(models.Model):
    """Отчёт о выполнении задачи с фото"""
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name="Задача"
    )
    submitted_by = models.ForeignKey(
        'users.Employee',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Отправил"
    )
    
    # Отчёт
    description = models.TextField(verbose_name="Описание работы")
    actual_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Фактическое время (часов)"
    )
    
    # Дата
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Отправлен")
    
    class Meta:
        db_table = 'tasks_report'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['task', 'submitted_at']),
        ]
        verbose_name = "Отчёт"
        verbose_name_plural = "Отчёты"
    
    def __str__(self):
        return f"Отчёт по {self.task.title}"


class TaskReportPhoto(models.Model):
    """Фото к отчёту о выполнении"""
    
    report = models.ForeignKey(
        TaskReport,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name="Отчёт"
    )
    photo = models.ImageField(
        upload_to=task_photo_path,
        verbose_name="Фото"
    )
    caption = models.CharField(max_length=200, blank=True, verbose_name="Подпись")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Загружено")
    
    class Meta:
        db_table = 'tasks_report_photo'
        ordering = ['uploaded_at']
        indexes = [
            models.Index(fields=['report']),
        ]
        verbose_name = "Фото отчёта"
        verbose_name_plural = "Фото отчётов"
    
    def __str__(self):
        return f"Фото для {self.report}"


class TaskTemplate(models.Model):
    """Шаблон задачи для быстрого создания"""
    
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    category = models.CharField(max_length=100, verbose_name="Категория")
    priority = models.CharField(
        max_length=20,
        choices=Task.PRIORITY_CHOICES,
        default='medium',
        verbose_name="Приоритет"
    )
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Ожидаемое время (часов)"
    )
    
    created_by = models.ForeignKey(
        'users.Employee',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Создал"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    class Meta:
        db_table = 'tasks_template'
        ordering = ['category', 'title']
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]
        verbose_name = "Шаблон задачи"
        verbose_name_plural = "Шаблоны задач"
    
    def __str__(self):
        return f"{self.category}: {self.title}"
    
    def create_task(self, assigned_to, due_date, created_by=None):
        """Создать задачу из шаблона."""
        return Task.objects.create(
            title=self.title,
            description=self.description,
            assigned_to=assigned_to,
            created_by=created_by or self.created_by,
            priority=self.priority,
            category=self.category,
            estimated_hours=self.estimated_hours,
            due_date=due_date,
        )
