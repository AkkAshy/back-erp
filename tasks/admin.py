# coding: utf-8
"""
Django Admin для задач персонала.
"""

from django.contrib import admin
from tasks.models import Task, TaskComment, TaskReport, TaskReportPhoto, TaskTemplate


class TaskReportPhotoInline(admin.TabularInline):
    """Inline для фото отчётов"""
    model = TaskReportPhoto
    extra = 1
    fields = ['photo', 'caption']


class TaskCommentInline(admin.TabularInline):
    """Inline для комментариев"""
    model = TaskComment
    extra = 0
    fields = ['author', 'text', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin для задач"""
    
    list_display = [
        'title', 'assigned_to', 'created_by', 
        'status', 'priority', 'due_date', 
        'is_overdue', 'created_at'
    ]
    list_filter = ['status', 'priority', 'category', 'due_date', 'created_at']
    search_fields = ['title', 'description', 'assigned_to__first_name', 'assigned_to__last_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'completed_at', 'is_overdue']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'category')
        }),
        ('Назначение', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Статус и приоритет', {
            'fields': ('status', 'priority', 'rejection_reason')
        }),
        ('Сроки', {
            'fields': ('due_date', 'estimated_hours', 'is_overdue')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TaskCommentInline]
    
    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Просрочена'


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """Admin для комментариев"""
    
    list_display = ['task', 'author', 'text_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['task__title', 'text']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Текст'


@admin.register(TaskReport)
class TaskReportAdmin(admin.ModelAdmin):
    """Admin для отчётов"""
    
    list_display = ['task', 'submitted_by', 'actual_hours', 'submitted_at']
    list_filter = ['submitted_at']
    search_fields = ['task__title', 'description']
    ordering = ['-submitted_at']
    readonly_fields = ['submitted_at']
    
    inlines = [TaskReportPhotoInline]


@admin.register(TaskReportPhoto)
class TaskReportPhotoAdmin(admin.ModelAdmin):
    """Admin для фото отчётов"""
    
    list_display = ['report', 'caption', 'uploaded_at']
    list_filter = ['uploaded_at']
    ordering = ['-uploaded_at']
    readonly_fields = ['uploaded_at']


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    """Admin для шаблонов"""
    
    list_display = ['title', 'category', 'priority', 'estimated_hours', 'is_active', 'created_at']
    list_filter = ['category', 'priority', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'category']
    ordering = ['category', 'title']
    readonly_fields = ['created_at']
