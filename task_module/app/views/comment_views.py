# app/views/comment_views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Task, Comment
from ..serializers import CommentSerializer
from app.utils.auth import RedisSessionAuthentication, get_session_user

class CommentListCreateView(generics.ListCreateAPIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer

    def get_session_user(self):
        """Получаем пользователя из сессии (из кук или заголовков)"""
        session_id = self.request.COOKIES.get('session_token') or self.request.headers.get('X-Session-ID')
        user = get_session_user(session_id)
        if not user:
            raise PermissionDenied("Сессия недействительна или истекла")
        return user

    def get_queryset(self):
        task_id = self.kwargs['task_id']
        return Comment.objects.filter(task_id=task_id).select_related('author')

    def get_authenticate_header(self, request):
        return 'X-Session-ID'

    @swagger_auto_schema(
        operation_description="Получить все комментарии к задаче",
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID',
                openapi.IN_HEADER,
                description="Идентификатор сессии",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'task_id',
                openapi.IN_PATH,
                description="ID задачи",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: CommentSerializer(many=True),
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Задача не найдена'
        }
    )
    def get(self, request, *args, **kwargs):
        self.get_session_user()  # Проверка сессии
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=CommentSerializer,
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID',
                openapi.IN_HEADER,
                description="Идентификатор сессии",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'task_id',
                openapi.IN_PATH,
                description="ID задачи",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            201: openapi.Response('Комментарий создан', CommentSerializer),
            400: 'Неверные данные',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Задача не найдена'
        }
    )
    def post(self, request, *args, **kwargs):
        self.get_session_user()  # Проверка сессии
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        task_id = self.kwargs['task_id']
        task = Task.objects.get(id=task_id)
        user = self.get_session_user()
        serializer.save(task=task, author=user)

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all().select_related('author')
    serializer_class = CommentSerializer

    def get_session_user(self):
        """Получаем пользователя из сессии (из кук или заголовков)"""
        session_id = self.request.COOKIES.get('session_token') or self.request.headers.get('X-Session-ID')
        user = get_session_user(session_id)
        if not user:
            raise PermissionDenied("Сессия недействительна или истекла")
        return user

    def get_authenticate_header(self, request):
        return 'X-Session-ID'

    @swagger_auto_schema(
        operation_description="Получить детали комментария",
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
            200: CommentSerializer,
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Комментарий не найден'
        }
    )
    def get(self, request, *args, **kwargs):
        self.get_session_user()  # Проверка сессии
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=CommentSerializer,
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
            200: openapi.Response('Комментарий обновлен', CommentSerializer),
            400: 'Неверные данные',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Комментарий не найден'
        }
    )
    def put(self, request, *args, **kwargs):
        self.get_session_user()  # Проверка сессии
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=CommentSerializer,
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
            200: openapi.Response('Комментарий обновлен', CommentSerializer),
            400: 'Неверные данные',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Комментарий не найден'
        }
    )
    def patch(self, request, *args, **kwargs):
        self.get_session_user()  # Проверка сессии
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удалить комментарий",
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
            204: 'Комментарий удален',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Комментарий не найден'
        }
    )
    def delete(self, request, *args, **kwargs):
        self.get_session_user()  # Проверка сессии
        return super().delete(request, *args, **kwargs)