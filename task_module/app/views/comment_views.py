from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Task, Comment
from ..serializers import CommentSerializer
from rest_framework import serializers
from app.utils.auth import RedisSessionAuthentication, get_session_user

class CommentListCreateView(generics.ListCreateAPIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer

    def get_session_user(self):
        session_id = self.request.COOKIES.get('session_token') or self.request.headers.get('X-Session-ID')
        user = get_session_user(session_id)
        if not user:
            raise PermissionDenied("Сессия недействительна или истекла")
        return user

    def get_queryset(self):
        task_id = self.kwargs['task_id']
        return Comment.objects.filter(task_id=task_id, is_deleted=False).select_related('author')

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
        self.get_session_user()
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
        self.get_session_user()
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        task_id = self.kwargs['task_id']
        task = Task.objects.get(id=task_id)
        user = self.get_session_user()
        serializer.save(task=task, author=user)
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
        self.get_session_user()
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
        # Создаем копию данных для безопасного изменения
        data = request.data.copy()
        text = data.get('text', '').strip()
        
        # Валидация текста
        if not text:
            return Response(
                {"error": "Текст комментария не может быть пустым"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Обновляем текст в данных
        data['text'] = text
        
        # Создаем и валидируем сериализатор
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Сохраняем комментарий
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        task_id = self.kwargs['task_id']
        task = Task.objects.get(id=task_id)
        user = self.get_session_user()
        
        # Дополнительная проверка текста
        text = serializer.validated_data.get('text', '').strip()
        if not text:
            raise serializers.ValidationError("Текст комментария не может быть пустым")
        
        print("Сохранение комментария:", {
            'text': text,
            'task': task.id,
            'author': user.id
        })
        
        serializer.save(task=task, author=user, text=text)




class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.filter(is_deleted=False).select_related('author')
    serializer_class = CommentSerializer

    def get_session_user(self):
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
        self.get_session_user()
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
        self.get_session_user()
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
        self.get_session_user()
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
        comment = self.get_object()
        comment.delete()  # Используем мягкое удаление
        return Response(status=status.HTTP_204_NO_CONTENT)
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all().select_related('author')
    serializer_class = CommentSerializer

    def get_session_user(self):
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
        self.get_session_user()
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
        self.get_session_user()
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
        self.get_session_user()
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
        self.get_session_user()
        return super().delete(request, *args, **kwargs)