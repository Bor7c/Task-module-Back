# app/views/task_views.py
import os
from django.http import FileResponse
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Task, User, Attachment
from ..serializers import *
from app.utils.auth import RedisSessionAuthentication, get_session_user
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

def get_user_from_request(request):
    session_id = request.COOKIES.get('session_token') or request.headers.get('X-Session-ID')
    user = get_session_user(session_id)
    if not user:
        raise PermissionDenied("Сессия недействительна или истекла")
    return user

def update_overdue_tasks():
    now = timezone.now()
    active_tasks = Task.objects.filter(
        status__in=['in_progress', 'awaiting_response', 'awaiting_action'],
        is_deleted=False,
        deadline__isnull=False,
        deadline__lt=now,
        is_overdue=False
    )
    overdue_count = active_tasks.update(is_overdue=True)
    
    not_overdue_tasks = Task.objects.filter(
        is_deleted=False,
        deadline__isnull=False,
        deadline__gte=now,
        is_overdue=True
    )
    not_overdue_count = not_overdue_tasks.update(is_overdue=False)
    
    no_deadline_tasks = Task.objects.filter(
        is_deleted=False,
        deadline__isnull=True,
        is_overdue=True
    )
    no_deadline_count = no_deadline_tasks.update(is_overdue=False)
    
    return overdue_count + not_overdue_count + no_deadline_count

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
        update_overdue_tasks()
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
        task = serializer.save(created_by=user)
        
        now = timezone.now()
        if (task.status in ['in_progress', 'awaiting_response', 'awaiting_action'] and 
            task.deadline and task.deadline < now):
            task.is_overdue = True
            task.save(update_fields=['is_overdue'])
        
        return task

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
        task = self.get_object()
        now = timezone.now()

        if (task.status in ['in_progress', 'awaiting_response', 'awaiting_action'] and 
            task.deadline and task.deadline < now and not task.is_overdue):
            task.is_overdue = True
            task.save(update_fields=['is_overdue'])

        elif ((task.deadline and task.deadline >= now) or not task.deadline) and task.is_overdue:
            task.is_overdue = False
            task.save(update_fields=['is_overdue'])
        
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
        original_task = self.get_object()
        original_deadline = original_task.deadline
        
        response = super().put(request, *args, **kwargs)
        
        if response.status_code == 200:
            task = self.get_object()
            now = timezone.now()
            deadline_changed = original_deadline != task.deadline
            
            if (task.status in ['in_progress', 'awaiting_response', 'awaiting_action'] and 
                task.deadline and task.deadline < now and not task.is_overdue):
                task.is_overdue = True
                task.save(update_fields=['is_overdue'])
            
            elif deadline_changed and ((task.deadline and task.deadline >= now) or not task.deadline) and task.is_overdue:
                task.is_overdue = False
                task.save(update_fields=['is_overdue'])
        
        return response
    
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

class AttachmentView(APIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        """Получить список вложений задачи"""
        try:
            user = get_user_from_request(request)
            task = get_object_or_404(Task, pk=task_id, is_deleted=False)
            attachments = task.attachments.all()
            serializer = AttachmentSerializer(attachments, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def post(self, request, task_id):
        """Добавить вложения к задаче"""
        try:
            user = get_user_from_request(request)
            task = get_object_or_404(Task, pk=task_id, is_deleted=False)
            
            if not request.FILES.getlist('files'):
                return Response(
                    {"error": "No files were provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            attachments = []
            for file in request.FILES.getlist('files'):
                # Проверка размера файла (например, не более 10MB)
                if file.size > 10 * 1024 * 1024:
                    continue
                
                attachment = Attachment.objects.create(
                    file=file,
                    task=task,
                    uploaded_by=user  # Теперь это поле существует в модели
                )
                attachments.append(attachment)

            if not attachments:
                return Response(
                    {"error": "No valid files were uploaded"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = AttachmentSerializer(attachments, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )



class AttachmentDetailView(APIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, attachment_id):
        """Скачать вложение"""
        try:
            user = get_user_from_request(request)
            attachment = get_object_or_404(Attachment, pk=attachment_id)
            
            if not attachment.file:
                return Response(
                    {"error": "File not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            file = attachment.file.open('rb')
            response = FileResponse(file)
            filename = os.path.basename(attachment.file.name)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, attachment_id):
        """Удалить вложение"""
        try:
            user = get_user_from_request(request)
            attachment = get_object_or_404(Attachment, pk=attachment_id)
            
            # Проверка прав - только автор или ответственный может удалить
            if (user.id != attachment.uploaded_by.id and 
                (not attachment.task.responsible or user.id != attachment.task.responsible.id)):
                return Response(
                    {"error": "You don't have permission to delete this attachment"},
                    status=status.HTTP_403_FORBIDDEN
                )

            attachment.file.delete()  # Удаляем файл из хранилища
            attachment.delete()       # Удаляем запись из БД
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
                  
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
            200: openapi.Response('Задача успешно обновлена', TaskDetailSerializer),
            404: 'Задача не найдена',
            401: 'Не авторизован',
            403: 'Доступ запрещен'
        }
    )
    def post(self, request, task_id):
        user = get_user_from_request(request)
        task = get_object_or_404(Task, pk=task_id, is_deleted=False)
        task.responsible = user
        
        now = timezone.now()
        if (task.status in ['in_progress', 'awaiting_response', 'awaiting_action'] and 
            task.deadline and task.deadline < now and not task.is_overdue):
            task.is_overdue = True
        
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
        
        now = timezone.now()
        if (task.status in ['in_progress', 'awaiting_response', 'awaiting_action'] and 
            task.deadline and task.deadline < now and not task.is_overdue):
            task.is_overdue = True
        
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
        
        now = timezone.now()
        if (task.status in ['in_progress', 'awaiting_response', 'awaiting_action'] and 
            task.deadline and task.deadline < now and not task.is_overdue):
            task.is_overdue = True
        
        task.save()
        return Response(TaskDetailSerializer(task).data, status=status.HTTP_200_OK)

class UpdateOverdueTasksView(APIView):
    """Ручное обновление статуса просроченных задач"""
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Обновить статус просроченных задач",
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER, description="Идентификатор сессии", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: openapi.Response('Задачи обновлены', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'updated_count': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            )),
            401: 'Не авторизован',
            403: 'Доступ запрещен'
        }
    )
    def post(self, request):
        get_user_from_request(request)
        updated_count = update_overdue_tasks()
        return Response({"updated_count": updated_count}, status=status.HTTP_200_OK)
