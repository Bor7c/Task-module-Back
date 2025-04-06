from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from .views.task_views import TaskListCreateView, TaskDetailView
from .views.comment_views import CommentListCreateView, CommentDetailView
from .views.user_views import UserListView, UserDetailView, UserCreateView
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
    
    # Задачи
    path('tasks/', TaskListCreateView.as_view(), name='task-list'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    
    # Комментарии
    path('tasks/<int:task_id>/comments/', CommentListCreateView.as_view(), name='task-comment-list'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]