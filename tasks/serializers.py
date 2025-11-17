# coding: utf-8
"""
Сериализаторы для задач персонала.
"""

from rest_framework import serializers
from tasks.models import Task, TaskComment, TaskReport, TaskReportPhoto, TaskTemplate
from users.models import Employee


class TaskReportPhotoSerializer(serializers.ModelSerializer):
    """Сериализатор для фото отчёта"""
    
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskReportPhoto
        fields = ['id', 'photo', 'photo_url', 'caption', 'uploaded_at']
        read_only_fields = ['uploaded_at']
    
    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        return None


class TaskReportSerializer(serializers.ModelSerializer):
    """Сериализатор для отчёта о выполнении"""
    
    photos = TaskReportPhotoSerializer(many=True, read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.get_full_name', read_only=True)
    
    class Meta:
        model = TaskReport
        fields = [
            'id', 'task', 'submitted_by', 'submitted_by_name',
            'description', 'actual_hours',
            'photos', 'submitted_at'
        ]
        read_only_fields = ['submitted_by', 'submitted_at']


class TaskReportCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания отчёта с фото"""
    
    photos = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    photo_captions = serializers.ListField(
        child=serializers.CharField(max_length=200, allow_blank=True),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = TaskReport
        fields = ['task', 'description', 'actual_hours', 'photos', 'photo_captions']
    
    def create(self, validated_data):
        photos = validated_data.pop('photos', [])
        captions = validated_data.pop('photo_captions', [])
        
        # Создаём отчёт
        report = TaskReport.objects.create(**validated_data)
        
        # Добавляем фото
        for i, photo in enumerate(photos):
            caption = captions[i] if i < len(captions) else ''
            TaskReportPhoto.objects.create(
                report=report,
                photo=photo,
                caption=caption
            )
        
        # Автоматически отправляем задачу на проверку
        report.task.submit_for_review()
        
        return report


class TaskCommentSerializer(serializers.ModelSerializer):
    """Сериализатор для комментария"""
    
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    
    class Meta:
        model = TaskComment
        fields = ['id', 'task', 'author', 'author_name', 'text', 'created_at', 'updated_at']
        read_only_fields = ['author', 'created_at', 'updated_at']


class TaskListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка задач (краткий)"""
    
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    time_left = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'assigned_to', 'assigned_to_name',
            'created_by', 'created_by_name',
            'priority', 'status', 'category',
            'due_date', 'is_overdue', 'time_left',
            'created_at', 'updated_at'
        ]
    
    def get_time_left(self, obj):
        time_left = obj.time_left
        if time_left:
            days = time_left.days
            hours = time_left.seconds // 3600
            return f"{days}д {hours}ч" if days > 0 else f"{hours}ч"
        return None


class TaskDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра задачи"""
    
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    time_left = serializers.SerializerMethodField()
    
    comments = TaskCommentSerializer(many=True, read_only=True)
    reports = TaskReportSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description',
            'assigned_to', 'assigned_to_name',
            'created_by', 'created_by_name',
            'priority', 'status', 'category',
            'due_date', 'estimated_hours',
            'created_at', 'updated_at', 'started_at', 'completed_at',
            'is_overdue', 'time_left',
            'rejection_reason',
            'comments', 'reports'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'started_at', 'completed_at']
    
    def get_time_left(self, obj):
        time_left = obj.time_left
        if time_left:
            days = time_left.days
            hours = time_left.seconds // 3600
            return f"{days}д {hours}ч" if days > 0 else f"{hours}ч"
        return None


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления задачи"""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description',
            'assigned_to', 'priority', 'category',
            'due_date', 'estimated_hours'
        ]
    
    def validate_due_date(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Срок выполнения не может быть в прошлом")
        return value


class TaskTemplateSerializer(serializers.ModelSerializer):
    """Сериализатор для шаблона задачи"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = TaskTemplate
        fields = [
            'id', 'title', 'description', 'category',
            'priority', 'estimated_hours',
            'created_by', 'created_by_name',
            'created_at', 'is_active'
        ]
        read_only_fields = ['created_by', 'created_at']


class CreateTaskFromTemplateSerializer(serializers.Serializer):
    """Сериализатор для создания задачи из шаблона"""
    
    template_id = serializers.IntegerField()
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
    due_date = serializers.DateTimeField()
    
    def validate_template_id(self, value):
        try:
            template = TaskTemplate.objects.get(id=value, is_active=True)
        except TaskTemplate.DoesNotExist:
            raise serializers.ValidationError("Шаблон не найден или неактивен")
        return value
    
    def validate_due_date(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Срок выполнения не может быть в прошлом")
        return value
    
    def create(self, validated_data):
        template = TaskTemplate.objects.get(id=validated_data['template_id'])
        created_by = self.context['request'].user.employee
        
        task = template.create_task(
            assigned_to=validated_data['assigned_to'],
            due_date=validated_data['due_date'],
            created_by=created_by
        )
        return task
