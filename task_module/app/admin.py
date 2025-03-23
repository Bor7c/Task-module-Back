from django.contrib import admin
from .models import Task, Comment

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_at', 'updated_at')  # Убрали created_by и assigned_to
    list_filter = ('status', 'created_at')  # Добавили фильтры
    search_fields = ('title', 'description')  # Добавили поиск

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'text', 'created_at')  # Убрали author
    list_filter = ('created_at',)  # Добавили фильтры
    search_fields = ('text',)  # Добавили поиск