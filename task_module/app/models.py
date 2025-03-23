from django.contrib.auth.models import AbstractUser
from django.db import models

# Кастомная модель пользователя
# class CustomUser(AbstractUser):
#     # Роли пользователя
#     ROLE_CHOICES = [
#         ('admin', 'Администратор'),
#         ('manager', 'Менеджер'),
#         ('developer', 'Разработчик'),
#         ('guest', 'Гость'),
#     ]

#     role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest')
#     full_name = models.CharField(max_length=255, blank=True, null=True)

#     def __str__(self):
#         return self.username

# Модель задачи
class Task(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Назначен'),
        ('in_progress', 'В работе'),
        ('solved', 'Решен'),
        ('closed', 'Закрыт'),
        ('awaiting_response', 'Ожидает ответа'),
        ('awaiting_action', 'Ожидает действий от сторонних'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on {self.task.title}"
