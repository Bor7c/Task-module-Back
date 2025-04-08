# app/views/task_views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Task
from ..serializers import *
from app.utils.auth import RedisSessionAuthentication, get_session_user
from rest_framework.exceptions import PermissionDenied

class TaskListCreateView(generics.ListCreateAPIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all().select_related('responsible', 'created_by')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TaskCreateUpdateSerializer
        return TaskListSerializer

    def get_authenticate_header(self, request):
        return 'X-Session-ID'

    def get_session_user(self):
        """Получаем пользователя из сессии (из кук или заголовков)"""
        session_id = self.request.COOKIES.get('session_token') or self.request.headers.get('X-Session-ID')
        user = get_session_user(session_id)
        if not user:
            raise PermissionDenied("Сессия недействительна или истекла")
        return user

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
        # Проверяем валидность сессии перед выполнением
        self.get_session_user()
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
        # Проверяем валидность сессии перед выполнением
        self.get_session_user()
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.get_session_user()
        serializer.save(created_by=user)

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all().select_related('responsible', 'created_by')
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TaskCreateUpdateSerializer
        return TaskDetailSerializer

    def get_authenticate_header(self, request):
        return 'X-Session-ID'

    def get_session_user(self):
        """Получаем пользователя из сессии (из кук или заголовков)"""
        session_id = self.request.COOKIES.get('session_token') or self.request.headers.get('X-Session-ID')
        user = get_session_user(session_id)
        if not user:
            raise PermissionDenied("Сессия недействительна или истекла")
        return user

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
        # Проверяем валидность сессии перед выполнением
        self.get_session_user()
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
        # Проверяем валидность сессии перед выполнением
        self.get_session_user()
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
        # Проверяем валидность сессии перед выполнением
        self.get_session_user()
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
        # Проверяем валидность сессии перед выполнением
        self.get_session_user()
        return super().delete(request, *args, **kwargs)