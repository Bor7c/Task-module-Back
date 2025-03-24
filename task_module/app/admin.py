from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Task, Comment, User

# Кастомный UserAdmin для отображения поля role
class CustomUserAdmin(UserAdmin):
    # Поля, которые будут отображаться в списке пользователей
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    
    # Поля, которые можно редактировать в форме изменения пользователя
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительные поля', {'fields': ('role',)}),
    )
    
    # Поля, которые можно редактировать в форме создания пользователя
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительные поля', {'fields': ('role',)}),
    )
    
    # Фильтры и поиск
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'role')

# Регистрируем модели
admin.site.register(User, CustomUserAdmin)  # ← Важно: регистрируем User с CustomUserAdmin

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text',)