from datetime import timezone
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

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'





class Task(models.Model):
    STATUS_CHOICES = [
        ('unassigned', 'Не назначен'),  # Добавлен новый статус
        ('assigned', 'Назначен'),
        ('in_progress', 'В работе'),
        ('solved', 'Решен'),
        ('closed', 'Закрыт'),
        ('awaiting_response', 'Ожидает ответа'),
        ('awaiting_action', 'Ожидает действий'),
    ]

    PRIORITY_CHOICES = [  # Добавлены приоритеты
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]

    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
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
        verbose_name='Ответственный'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        verbose_name='Создатель'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата последнего обновления')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата закрытия')
    deadline = models.DateTimeField(null=True, blank=True, verbose_name='Срок выполнения')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалено')
   

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created_at']

    def __str__(self):
        responsible_name = self.responsible.username if self.responsible else "Не назначен"
        return f"{self.title} (Ответственный: {responsible_name})"
    
    def save(self, *args, **kwargs):
        """Автоматическое обновление даты закрытия и updated_at при любых изменениях"""
        update_fields = kwargs.get('update_fields', [])
        
        # Обновление closed_at при изменении статуса
        if self.pk and 'status' in update_fields:
            if self.status == 'closed' and not self.closed_at:
                self.closed_at = timezone.now()
            elif self.status != 'closed' and self.closed_at:
                self.closed_at = None
        
        # Гарантируем обновление updated_at при любом сохранении
        if self.pk:
            if 'updated_at' not in update_fields:
                update_fields.append('updated_at')
            kwargs['update_fields'] = update_fields
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Мягкое удаление с обновлением updated_at"""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])





class Comment(models.Model):
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name='Задача'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_system = models.BooleanField(default=False, verbose_name='Системное сообщение')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата последнего обновления')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалено')

   
    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        """Гарантированное обновление updated_at при любом изменении"""
        update_fields = kwargs.get('update_fields', [])
        if self.pk:  # Только для существующих записей
            if 'updated_at' not in update_fields:
                update_fields.append('updated_at')
            kwargs['update_fields'] = update_fields
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Мягкое удаление с обновлением updated_at"""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])