from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import User
from ..serializers import UserBasicSerializer, UserCreateSerializer
from app.utils.auth import RedisSessionAuthentication, get_session_user

class UserListView(generics.ListAPIView):
    """Получение списка пользователей (для всех авторизованных)"""
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]  # <--- изменено тут
    queryset = User.objects.all()
    serializer_class = UserBasicSerializer

    @swagger_auto_schema(
        operation_description="Получить список всех пользователей",
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
            200: openapi.Response(
                'Success',
                openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'username': openapi.Schema(type=openapi.TYPE_STRING),
                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                            'role': openapi.Schema(type=openapi.TYPE_STRING),
                            'role_display': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                )
            ),
            401: 'Не авторизован',
            403: 'Доступ запрещен'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Просмотр, обновление и удаление пользователя"""
    authentication_classes = [RedisSessionAuthentication]
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserBasicSerializer
        return UserBasicSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    @swagger_auto_schema(
        operation_description="Получить информацию о пользователе",
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
            200: openapi.Response(
                'Success',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'role': openapi.Schema(type=openapi.TYPE_STRING),
                        'role_display': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Пользователь не найден'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Обновить данные пользователя (только админ)",
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID',
                openapi.IN_HEADER,
                description="Идентификатор сессии администратора",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=UserBasicSerializer,
        responses={
            200: openapi.Response(
                'Success',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'role': openapi.Schema(type=openapi.TYPE_STRING),
                        'role_display': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: 'Неверные данные',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Пользователь не найден'
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частичное обновление пользователя (только админ)",
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID',
                openapi.IN_HEADER,
                description="Идентификатор сессии администратора",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=UserBasicSerializer,
        responses={
            200: openapi.Response(
                'Success',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'role': openapi.Schema(type=openapi.TYPE_STRING),
                        'role_display': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: 'Неверные данные',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Пользователь не найден'
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удалить пользователя (только админ)",
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID',
                openapi.IN_HEADER,
                description="Идентификатор сессии администратора",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            204: 'Пользователь удален',
            401: 'Не авторизован',
            403: 'Доступ запрещен',
            404: 'Пользователь не найден'
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

class UserCreateView(generics.CreateAPIView):
    """Регистрация нового пользователя"""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Регистрация нового пользователя",
        request_body=UserCreateSerializer,
        responses={
            201: openapi.Response(
                "Пользователь создан",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response("Неверные данные")
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            # Дополнительные действия после создания пользователя
            user = User.objects.get(id=response.data['id'])
            # Можно отправить email подтверждения и т.д.
        return response