# app/views/task_views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Task
from ..serializers import *
from app.utils.auth import RedisSessionAuthentication, get_session_user

class TaskListCreateView(generics.ListCreateAPIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Task.objects.all().select_related('responsible', 'created_by')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TaskCreateUpdateSerializer
        return TaskListSerializer

    @swagger_auto_schema(
        operation_description="Получить список всех задач",
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID',
                openapi.IN_HEADER,
                description="Идентификатор сессии",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: TaskListSerializer(many=True),
            401: 'Не авторизован',
            403: 'Доступ запрещен'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=TaskCreateUpdateSerializer,
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID',
                openapi.IN_HEADER,
                description="Идентификатор сессии",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: openapi.Response('Задача создана', TaskDetailSerializer),
            400: 'Неверные данные',
            401: 'Не авторизован',
            403: 'Доступ запрещен'
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = get_session_user(self.request.headers.get('X-Session-ID'))
        serializer.save(created_by=user)

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Task.objects.all().select_related('responsible', 'created_by')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TaskCreateUpdateSerializer
        return TaskDetailSerializer

    @swagger_auto_schema(
        operation_description="Получить детальную информацию о задаче",
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID',
                openapi.IN_HEADER,
                description="Идентификатор сессии",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: TaskDetailSerializer,
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Задача не найдена'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=TaskCreateUpdateSerializer,
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID',
                openapi.IN_HEADER,
                description="Идентификатор сессии",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response('Задача обновлена', TaskDetailSerializer),
            400: 'Неверные данные',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Задача не найдена'
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=TaskCreateUpdateSerializer,
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID',
                openapi.IN_HEADER,
                description="Идентификатор сессии",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response('Задача обновлена', TaskDetailSerializer),
            400: 'Неверные данные',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Задача не найдена'
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удалить задачу",
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID',
                openapi.IN_HEADER,
                description="Идентификатор сессии",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            204: 'Задача удалена',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Задача не найдена'
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)