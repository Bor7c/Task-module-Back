from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static
from .views.team_views import TeamViewSet

from .views.task_views import (
    AttachmentDetailView,
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
    permission_classes=[permissions.AllowAny],
)

# TeamViewSet actions
team_list = TeamViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

team_detail = TeamViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

team_add_member = TeamViewSet.as_view({
    'post': 'add_member',
})

team_remove_member = TeamViewSet.as_view({
    'post': 'remove_member',
})

team_all = TeamViewSet.as_view({
    'get': 'list_all_teams',
})

urlpatterns = [
    # Документация API
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Аутентификация
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/session-check/', SessionCheckView.as_view(), name='auth-session-check'),
    
    # Команды
    path('teams/', team_list, name='team-list'),
    path('teams/<int:pk>/', team_detail, name='team-detail'),
    path('teams/<int:pk>/add-member/', team_add_member, name='team-add-member'),
    path('teams/<int:pk>/remove-member/', team_remove_member, name='team-remove-member'),
    path('teams/all/', team_all, name='team-all'),

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
    path('tasks/<int:task_id>/attachments/', AttachmentView.as_view(), name='task-attachments'),
    path('attachments/<int:attachment_id>/', AttachmentDetailView.as_view(), name='attachment-detail'),
    
    # Комментарии
    path('tasks/<int:task_id>/comments/', CommentListCreateView.as_view(), name='task-comment-list'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]
