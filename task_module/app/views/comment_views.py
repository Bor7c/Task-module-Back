import logging
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotFound
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Task, Comment
from ..serializers import CommentSerializer
from app.utils.auth import RedisSessionAuthentication, get_session_user
import traceback
from django.utils import timezone

logger = logging.getLogger(__name__)

class CommentListCreateView(generics.ListCreateAPIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    
    def get_session_user(self):
        """Получаем пользователя из сессии (из кук или заголовков)"""
        session_id = self.request.COOKIES.get('session_token') or self.request.headers.get('X-Session-ID')
        user = get_session_user(session_id)
        if not user:
            logger.warning(f"Invalid session attempt: {session_id}")
            raise PermissionDenied("Сессия недействительна или истекла")
        logger.debug(f"Authenticated user: {user.username} (ID: {user.id})")
        return user
    
    def get_queryset(self):
        task_id = self.kwargs['task_id']
        logger.debug(f"Getting comments for task ID: {task_id}")
        return Comment.objects.filter(
            task_id=task_id, 
            is_deleted=False
        ).select_related('author', 'task')
    
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
        logger.info(f"GET comments for task ID: {kwargs['task_id']}")
        try:
            task = Task.objects.get(id=kwargs['task_id'])
            logger.debug(f"Task found: {task.title} (ID: {task.id})")
        except Task.DoesNotExist:
            logger.error(f"Task not found: ID {kwargs['task_id']}")
            raise NotFound("Задача не найдена")
            
        response = super().get(request, *args, **kwargs)
        logger.debug(f"Returning {len(response.data)} comments")
        return response
    
    @swagger_auto_schema(
        operation_description="Создать новый комментарий к задаче",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['text'],
            properties={
                'text': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Текст комментария",
                    min_length=1
                )
            }
        ),
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
        user = self.get_session_user()
        logger.info(f"User {user.username} creating comment for task {kwargs['task_id']}")
        
        text = request.data.get('text', '').strip()
        logger.debug(f"Received text: '{text}'")
        
        if not text:
            logger.warning("Empty comment text provided")
            return Response(
                {"error": "Текст комментария не может быть пустым"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            task = Task.objects.get(id=kwargs['task_id'])
            logger.debug(f"Task found: {task.title}")
        except Task.DoesNotExist:
            logger.error(f"Task not found: ID {kwargs['task_id']}")
            raise NotFound("Задача не найдена")
        
        try:
            # При создании is_modified явно устанавливаем в False
            comment = Comment.objects.create(
                text=text,
                task=task,
                author=user,
                is_modified=False  # Явно указываем, что комментарий не модифицирован
            )
            logger.info(
                f"Comment created successfully\n"
                f"Comment ID: {comment.id}\n"
                f"Task: {task.title} (ID: {task.id})\n"
                f"Author: {user.username} (ID: {user.id})\n"
                f"Text length: {len(text)} characters\n"
                f"Is modified: {comment.is_modified}"
            )
            
            serializer = self.get_serializer(comment)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            logger.error(
                f"Failed to create comment\n"
                f"Error: {str(e)}\n"
                f"Task ID: {kwargs['task_id']}\n"
                f"User ID: {user.id}"
            )
            return Response(
                {"error": "Не удалось создать комментарий"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'pk'
    
    def get_queryset(self):
        logger.debug(f"Getting comment with ID: {self.kwargs.get('pk')}")
        return Comment.objects.filter(is_deleted=False).select_related('author', 'task')
    
    def get_session_user(self):
        session_id = self.request.COOKIES.get('session_token') or self.request.headers.get('X-Session-ID')
        user = get_session_user(session_id)
        if not user:
            logger.warning(f"Invalid session attempt: {session_id}")
            raise PermissionDenied("Сессия недействительна или истекла")
        logger.debug(f"Authenticated user: {user.username} (ID: {user.id})")
        return user
    
    def get_object(self):
        try:
            comment = super().get_object()
            user = self.get_session_user()
            
            logger.debug(
                f"Accessing comment ID: {comment.id}\n"
                f"Author: {comment.author.username} (ID: {comment.author.id})\n"
                f"Task: {comment.task.title} (ID: {comment.task.id})"
            )
            
            if self.request.method == 'GET':
                return comment
                
            if comment.author != user and not user.is_staff:
                logger.warning(
                    f"Unauthorized edit attempt\n"
                    f"User: {user.username} (ID: {user.id})\n"
                    f"Comment author: {comment.author.username} (ID: {comment.author.id})"
                )
                raise PermissionDenied("Вы не можете изменять этот комментарий")
            return comment
            
        except Exception as e:
            logger.error(f"Error getting comment: {str(e)}")
            raise
    
    @swagger_auto_schema(
        operation_description="Обновить комментарий",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['text'],
            properties={
                'text': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Новый текст комментария",
                    min_length=1
                )
            }
        ),
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
            400: 'Неверные данные',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Комментарий не найден'
        }
    )
    def put(self, request, *args, **kwargs):
        comment = self.get_object()
        user = self.get_session_user()
        text = request.data.get('text', '').strip()
        
        logger.info(
            f"PUT comment update request\n"
            f"Comment ID: {comment.id}\n"
            f"User: {user.username} (ID: {user.id})\n"
            f"Current text: '{comment.text}'\n"
            f"New text: '{text}'"
        )
        
        if not text:
            logger.warning("Empty text in PUT request")
            return Response(
                {"error": "Текст комментария не может быть пустым"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            old_text = comment.text
            # Если текст изменился, устанавливаем is_modified в True
            if old_text != text:
                comment.text = text
                comment.is_modified = True  # Явно указываем, что комментарий модифицирован
                comment.save(update_fields=['text', 'is_modified', 'updated_at'])
                logger.info(
                    f"Comment text changed and marked as modified\n"
                    f"Comment ID: {comment.id}\n"
                    f"Is modified: {comment.is_modified}"
                )
            
            comment.refresh_from_db()
            
            logger.info(
                f"Comment updated successfully\n"
                f"Comment ID: {comment.id}\n"
                f"Old text: '{old_text}'\n"
                f"New text: '{comment.text}'\n"
                f"Updated at: {comment.updated_at}\n"
                f"Is modified: {comment.is_modified}"
            )
            
            serializer = self.get_serializer(comment)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(
                f"Failed to update comment\n"
                f"Comment ID: {comment.id}\n"
                f"Error: {str(e)}"
            )
            return Response(
                {"error": "Не удалось обновить комментарий"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Частично обновить комментарий",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'text': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Новый текст комментария",
                    min_length=1
                )
            }
        ),
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
            400: 'Неверные данные',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Комментарий не найден'
        }
    )
    def patch(self, request, *args, **kwargs):
        comment = self.get_object()
        user = self.get_session_user()
        text = request.data.get('text', '').strip()
        
        logger.info(
            f"PATCH comment update request\n"
            f"Comment ID: {comment.id}\n"
            f"User: {user.username} (ID: {user.id})\n"
            f"Current text: '{comment.text}'\n"
            f"New text: '{text}'"
        )
        
        if not text:
            logger.info("No text provided, returning current comment")
            serializer = self.get_serializer(comment)
            return Response(serializer.data)
            
        if len(text) < 2:
            logger.warning(f"Text too short: {len(text)} characters")
            return Response(
                {"error": "Комментарий должен содержать минимум 2 символа"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Проверяем, изменился ли текст
            if comment.text != text:
                # Вместо прямого обновления через QuerySet используем объект комментария
                comment.text = text
                comment.is_modified = True  # Устанавливаем флаг модификации
                comment.updated_at = timezone.now()
                comment.save(update_fields=['text', 'is_modified', 'updated_at'])
                
                logger.info(
                    f"Comment updated successfully\n"
                    f"Comment ID: {comment.id}\n"
                    f"New text: '{comment.text}'\n"
                    f"Updated at: {comment.updated_at}\n"
                    f"Is modified: {comment.is_modified}"
                )
            else:
                logger.info(f"Text not changed for comment ID: {comment.id}")
            
            # Получаем свежие данные комментария
            comment.refresh_from_db()
            serializer = self.get_serializer(comment)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(
                f"Failed to update comment\n"
                f"Comment ID: {comment.id}\n"
                f"Error: {str(e)}\n"
                f"Stack trace: {traceback.format_exc()}"
            )
            return Response(
                {"error": "Не удалось обновить комментарий"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Удалить комментарий (мягкое удаление)",
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
        user = self.get_session_user()
        
        logger.info(f"Attempt to delete comment ID: {comment.id}")
        
        try:
            # Мягкое удаление с использованием update, но с флагом is_modified
            updated = Comment.objects.filter(id=comment.id).update(
                is_deleted=True,
                updated_at=timezone.now()
                # Не меняем is_modified, так как это не редактирование текста
            )
            
            if not updated:
                logger.error(f"No rows updated for comment ID: {comment.id}")
                return Response(
                    {"error": "Не удалось удалить комментарий"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            logger.info(f"Comment ID: {comment.id} marked as deleted")
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"Delete failed: {str(e)}")
            return Response(
                {"error": "Ошибка при удалении"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )