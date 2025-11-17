# coding: utf-8
"""
Signals для уведомлений о задачах.

Отправляет уведомления при создании, изменении статуса и т.д.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from tasks.models import Task, TaskComment, TaskReport


@receiver(post_save, sender=Task)
def notify_on_task_created(sender, instance, created, **kwargs):
    """
    Уведомление при создании задачи.
    
    Отправляет уведомление назначенному сотруднику.
    """
    if created:
        # TODO: Интеграция с системой уведомлений
        # Пока просто логируем
        print(f"✉️ Новая задача для {instance.assigned_to.get_full_name()}: {instance.title}")


@receiver(pre_save, sender=Task)
def notify_on_status_change(sender, instance, **kwargs):
    """
    Уведомление при изменении статуса задачи.
    
    Отправляет уведомления:
    - Создателю при отправке на проверку
    - Исполнителю при одобрении/отклонении
    """
    if instance.pk:
        try:
            old_task = Task.objects.get(pk=instance.pk)
            
            # Если статус изменился
            if old_task.status != instance.status:
                
                # Отправлена на проверку
                if instance.status == 'on_review':
                    print(f"✉️ Задача '{instance.title}' отправлена на проверку от {instance.assigned_to.get_full_name()}")
                
                # Одобрена
                elif instance.status == 'completed':
                    print(f"✅ Задача '{instance.title}' одобрена для {instance.assigned_to.get_full_name()}")
                
                # Отклонена
                elif instance.status == 'rejected':
                    print(f"❌ Задача '{instance.title}' отклонена для {instance.assigned_to.get_full_name()}")
                    print(f"   Причина: {instance.rejection_reason}")
                
                # Отменена
                elif instance.status == 'cancelled':
                    print(f"🚫 Задача '{instance.title}' отменена")
        
        except Task.DoesNotExist:
            pass


@receiver(post_save, sender=TaskComment)
def notify_on_comment_added(sender, instance, created, **kwargs):
    """
    Уведомление при добавлении комментария.
    
    Уведомляет исполнителя и создателя задачи.
    """
    if created:
        task = instance.task
        author = instance.author
        
        # Уведомляем исполнителя (если комментарий не от него)
        if task.assigned_to != author:
            print(f"💬 Новый комментарий к задаче '{task.title}' от {author.get_full_name()}")
        
        # Уведомляем создателя (если комментарий не от него)
        if task.created_by and task.created_by != author:
            print(f"💬 Новый комментарий к задаче '{task.title}' от {author.get_full_name()}")


@receiver(post_save, sender=TaskReport)
def notify_on_report_submitted(sender, instance, created, **kwargs):
    """
    Уведомление при отправке отчёта.
    
    Уведомляет создателя задачи о готовности отчёта.
    """
    if created:
        task = instance.task
        print(f"📊 Отчёт по задаче '{task.title}' отправлен от {instance.submitted_by.get_full_name()}")
        print(f"   Фактическое время: {instance.actual_hours} ч")
        print(f"   Фото: {instance.photos.count()} шт.")


# TODO: Интеграция с Celery для отправки напоминаний
# @shared_task
# def send_overdue_reminders():
#     """Отправляет напоминания о просроченных задачах."""
#     from django.utils import timezone
#     overdue_tasks = Task.objects.filter(
#         due_date__lt=timezone.now(),
#         status__in=['pending', 'in_progress']
#     )
#     for task in overdue_tasks:
#         # Отправить уведомление
#         pass
