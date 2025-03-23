from django.urls import path
from .views.task_views import TaskListCreateView, TaskDetailView
from .views.comment_views import CommentListCreateView, CommentDetailView

urlpatterns = [
    # Маршруты для задач
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),

    # Маршруты для комментариев
    path('tasks/<int:task_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]