from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'), 
        ('developer', 'Разработчик'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='developer',
        verbose_name='Роль'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активный'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

class Task(models.Model):
    STATUS_CHOICES = [
        ('unassigned', 'Не назначен'),
        ('assigned', 'Назначен'),
        ('in_progress', 'В работе'),
        ('solved', 'Решен'),
        ('closed', 'Закрыт'),
        ('awaiting_response', 'Ожидает ответа'),
        ('awaiting_action', 'Ожидает действий'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]

    title = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unassigned',
        verbose_name='Статус'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Приоритет'
    )
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name='Ответственный',
        limit_choices_to={'is_active': True}  # Только активные пользователи
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,  # Защита от удаления создателя
        related_name='created_tasks',
        verbose_name='Создатель'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата закрытия'
    )
    deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Срок выполнения'
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Удалено'
    )

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['deadline']),
        ]

    def __str__(self):
        return f"{self.title} (Статус: {self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Автоматическая установка/сброс даты закрытия
        if self.pk:
            original = Task.objects.get(pk=self.pk)
            if self.status == 'closed' and original.status != 'closed':
                self.closed_at = timezone.now()
            elif self.status != 'closed' and original.status == 'closed':
                self.closed_at = None
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Мягкое удаление"""
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])

class Comment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Задача'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,  # Защита от удаления автора
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Текст комментария'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    is_system = models.BooleanField(
        default=False,
        verbose_name='Системное сообщение'
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Удалено'
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['task']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Комментарий #{self.id} к задаче {self.task_id}"

    def save(self, *args, **kwargs):
        """Автоматическое обновление updated_at"""
        if self.pk:
            kwargs['update_fields'] = kwargs.get('update_fields', []) + ['updated_at']
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Мягкое удаление"""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])