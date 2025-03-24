from django.urls import path
from .views.task_views import TaskListCreateView, TaskDetailView
from .views.comment_views import CommentListCreateView, CommentDetailView
from .views.user_views import (
    UserListView,
    UserDetailView,
    UserCreateView,
    LoginView,
    LogoutView,
    CurrentUserView
)

urlpatterns = [
    # Маршруты для задач
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),

    # Маршруты для комментариев
    path('tasks/<int:task_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),

    # Пользователь
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/create/', UserCreateView.as_view(), name='user-create'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('current-user/', CurrentUserView.as_view(), name='current-user'),
]