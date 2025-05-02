from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from .views.task_views import (
    TaskListCreateView,
    TaskDetailView,
    AssignResponsibleView,
    RemoveResponsibleView,
    AssignToMeView,
    AttachmentView,
)
from .views.comment_views import CommentListCreateView, CommentDetailView
from .views.user_views import (
    UserListView,
    UserDetailView,
    UserCreateView,
    UserProfilePictureDeleteView,
    UserProfilePictureUploadView,
)
from .views.auth_views import LoginView, RegisterView, LogoutView, SessionCheckView

schema_view = get_schema_view(
    openapi.Info(
        title="Task Management API",
        default_version='v1',
        description="API для управления задачами и комментариями",
        contact=openapi.Contact(email="support@taskmanager.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],  # Разрешаем доступ без аутентификации
)

urlpatterns = [
    # Документация API
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Аутентификация
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/session-check/', SessionCheckView.as_view(), name='auth-session-check'),
    
    # Пользователи
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/create/', UserCreateView.as_view(), name='user-create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/profile/upload-picture/', UserProfilePictureUploadView.as_view(), name='user-upload-picture'), 
    path('users/profile/delete-picture/', UserProfilePictureDeleteView.as_view(), name='user-delete-picture'),

    # Задачи
    path('tasks/', TaskListCreateView.as_view(), name='task-list'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('tasks/<int:task_id>/assign_to_me/', AssignToMeView.as_view(), name='assign_to_me'),
    path('tasks/<int:pk>/assign_responsible/', AssignResponsibleView.as_view(), name='assign-responsible'),
    path('tasks/<int:pk>/remove_responsible/', RemoveResponsibleView.as_view(), name='remove-responsible'),
    
    # Вложения
    path('tasks/<int:task_id>/attachments/', AttachmentView.as_view(), name='task-attachment-create'),
    path('tasks/<int:task_id>/attachments/<int:attachment_id>/', AttachmentView.as_view(), name='task-attachment-delete'),

    # Комментарии
    path('tasks/<int:task_id>/comments/', CommentListCreateView.as_view(), name='task-comment-list'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]
