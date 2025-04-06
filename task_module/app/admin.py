from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Task, Comment

class UserAdminConfig(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Role', {'fields': ('role',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'responsible', 'created_by', 'created_at', 'deadline')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'description')
    raw_id_fields = ('responsible', 'created_by')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'status', 'priority')
        }),
        ('People', {
            'fields': ('responsible', 'created_by')
        }),
        ('Dates', {
            'fields': ('deadline',)
        }),
    )

class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at', 'short_text')
    list_filter = ('created_at', 'author')
    search_fields = ('text', 'task__title')
    date_hierarchy = 'created_at'
    
    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = 'Текст'

admin.site.register(User, UserAdminConfig)
admin.site.register(Task, TaskAdmin)
admin.site.register(Comment, CommentAdmin)