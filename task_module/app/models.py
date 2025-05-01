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
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True, verbose_name='Фото профиля')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

class Task(models.Model):
    STATUS_CHOICES = [
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

    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='awaiting_action',
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
        limit_choices_to={'is_active': True}
    )
    is_assigned = models.BooleanField(
        default=False,
        verbose_name='Назначен ли ответственный'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_tasks',
        verbose_name='Создатель'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата закрытия')
    deadline = models.DateTimeField(null=True, blank=True, verbose_name='Срок выполнения')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалено')
    is_overdue = models.BooleanField(default=False, verbose_name='Просрочено')

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['deadline']),
            models.Index(fields=['is_overdue']),
        ]
    
    def __str__(self):
        return f"{self.title} (Статус: {self.get_status_display()}, Назначен: {'Да' if self.is_assigned else 'Нет'})"
    
    def save(self, *args, **kwargs):
        if self.pk:
            original = Task.objects.get(pk=self.pk)
            if self.status == 'closed' and original.status != 'closed':
                self.closed_at = timezone.now()
            elif self.status != 'closed' and original.status == 'closed':
                self.closed_at = None
        
        self.is_assigned = bool(self.responsible)
        self.update_overdue_status()
        super().save(*args, **kwargs)
    
    def update_overdue_status(self):
        now = timezone.now()
        if not self.deadline or self.deadline >= now:
            self.is_overdue = False
        elif self.status in ['in_progress', 'awaiting_response', 'awaiting_action']:
            self.is_overdue = True

    @classmethod
    def update_all_overdue_statuses(cls):
        now = timezone.now()
        active_tasks = cls.objects.filter(
            status__in=['in_progress', 'awaiting_response', 'awaiting_action'],
            is_deleted=False,
            deadline__isnull=False,
            deadline__lt=now,
            is_overdue=False
        )
        overdue_count = active_tasks.update(is_overdue=True)

        not_overdue_tasks = cls.objects.filter(
            is_deleted=False,
            deadline__isnull=False,
            deadline__gte=now,
            is_overdue=True
        )
        not_overdue_count = not_overdue_tasks.update(is_overdue=False)

        no_deadline_tasks = cls.objects.filter(
            is_deleted=False,
            deadline__isnull=True,
            is_overdue=True
        )
        no_deadline_count = no_deadline_tasks.update(is_overdue=False)
        
        return overdue_count + not_overdue_count + no_deadline_count
    
    def delete(self, *args, **kwargs):
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
        on_delete=models.PROTECT,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_system = models.BooleanField(default=False, verbose_name='Системное сообщение')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалено')
    is_modified = models.BooleanField(default=False, verbose_name='Редактировался')

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
        if self.pk:
            kwargs['update_fields'] = kwargs.get('update_fields', []) + ['updated_at']
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])

class Attachment(models.Model):
    file = models.FileField(upload_to='attachments/', verbose_name='Файл')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments',
        null=True,
        blank=True,
        verbose_name='Задача'
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='attachments',
        null=True,
        blank=True,
        verbose_name='Комментарий'
    )

    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложения'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'Файл: {self.file.name}'
