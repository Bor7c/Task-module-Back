# app/views/task_views.py

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Task, User
from ..serializers import *
from app.utils.auth import RedisSessionAuthentication, get_session_user
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404


def get_user_from_request(request):
    session_id = request.COOKIES.get('session_token') or request.headers.get('X-Session-ID')
    user = get_session_user(session_id)
    if not user:
        raise PermissionDenied("Сессия недействительна или истекла")
    return user


class TaskListCreateView(generics.ListCreateAPIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.filter(is_deleted=False).select_related('responsible', 'created_by')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TaskCreateUpdateSerializer
        return TaskListSerializer

    @swagger_auto_schema(
        operation_description="Получить список всех задач",
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID', openapi.IN_HEADER,
                description="Идентификатор сессии",
                type=openapi.TYPE_STRING, required=True
            )
        ],
        responses={
            200: TaskListSerializer(many=True),
            401: 'Не авторизован',
            403: 'Доступ запрещен'
        }
    )
    def get(self, request, *args, **kwargs):
        get_user_from_request(request)
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=TaskCreateUpdateSerializer,
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID', openapi.IN_HEADER,
                description="Идентификатор сессии",
                type=openapi.TYPE_STRING, required=True
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
        get_user_from_request(request)
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = get_user_from_request(self.request)
        serializer.save(created_by=user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.filter(is_deleted=False).select_related('responsible', 'created_by')
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TaskCreateUpdateSerializer
        return TaskDetailSerializer

    @swagger_auto_schema(
        operation_description="Получить детальную информацию о задаче",
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER, description="Идентификатор сессии", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: TaskDetailSerializer,
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Задача не найдена'
        }
    )
    def get(self, request, *args, **kwargs):
        get_user_from_request(request)
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=TaskCreateUpdateSerializer,
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER, description="Идентификатор сессии", type=openapi.TYPE_STRING, required=True)
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
        get_user_from_request(request)
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=TaskCreateUpdateSerializer,
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER, description="Идентификатор сессии", type=openapi.TYPE_STRING, required=True)
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
        get_user_from_request(request)
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удалить задачу (мягкое удаление)",
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER, description="Идентификатор сессии", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            204: 'Задача удалена',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Задача не найдена'
        }
    )
    def delete(self, request, *args, **kwargs):
        get_user_from_request(request)
        task = self.get_object()
        task.is_deleted = True
        task.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AssignToMeView(APIView):
    """Назначить себя ответственным за задачу"""
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Назначить себя ответственным за задачу",
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER, description="Идентификатор сессии пользователя", type=openapi.TYPE_STRING, required=True),
        ],
        responses={
            200: openapi.Response('Task successfully updated', TaskDetailSerializer),
            404: 'Task not found',
            401: 'Unauthorized',
            403: 'Forbidden'
        }
    )
    def post(self, request, task_id):
        user = get_user_from_request(request)
        task = get_object_or_404(Task, pk=task_id, is_deleted=False)

        task.responsible = user
        task.save()

        return Response(TaskDetailSerializer(task).data, status=status.HTTP_200_OK)


class AssignResponsibleView(APIView):
    """Назначить другого пользователя ответственным за задачу"""
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Назначить ответственного за задачу",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["user_id"],
            properties={
                "user_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID пользователя"),
            },
        ),
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER, description="Идентификатор сессии", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: TaskDetailSerializer,
            400: 'Неверные данные',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Задача или пользователь не найдены'
        }
    )
    def post(self, request, pk):
        get_user_from_request(request)

        task = get_object_or_404(Task, pk=pk, is_deleted=False)
        user_id = request.data.get('user_id')

        if not user_id:
            return Response({"error": "Не указан user_id"}, status=status.HTTP_400_BAD_REQUEST)

        responsible_user = get_object_or_404(User, pk=user_id)
        task.responsible = responsible_user
        task.save()

        return Response(TaskDetailSerializer(task).data, status=status.HTTP_200_OK)


class RemoveResponsibleView(APIView):
    """Удалить ответственного с задачи"""
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Снять ответственного с задачи",
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER, description="Идентификатор сессии", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: TaskDetailSerializer,
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Задача не найдена'
        }
    )
    def post(self, request, pk):
        get_user_from_request(request)

        task = get_object_or_404(Task, pk=pk, is_deleted=False)
        task.responsible = None
        task.save()

        return Response(TaskDetailSerializer(task).data, status=status.HTTP_200_OK)
