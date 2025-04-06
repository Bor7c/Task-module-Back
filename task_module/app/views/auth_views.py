from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, logout
from django.contrib.auth.models import User
from ..utils.auth import (
    create_or_get_session,
    delete_session,
    get_session_user,
    refresh_session
)
from ..serializers import UserBasicSerializer  # Изменено на UserBasicSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Аутентификация пользователя",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format="password"),
            },
        ),
        responses={
            200: openapi.Response(
                description="Успешная аутентификация",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'session_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'role': openapi.Schema(type=openapi.TYPE_STRING),
                                'role_display': openapi.Schema(type=openapi.TYPE_STRING),
                                'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            }
                        )
                    }
                )
            ),
            401: "Неверные учетные данные",
            400: "Не указаны имя пользователя или пароль"
        }
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        
        if not username or not password:
            return Response(
                {"error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"error": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        session_id = create_or_get_session(user)
        
        response_data = {
            "session_id": session_id,
            "user": UserBasicSerializer(user).data  # Используем UserBasicSerializer
        }
        
        response = Response(response_data, status=status.HTTP_200_OK)
        response.set_cookie(
            key="session_token",
            value=session_id,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Strict',
            max_age=86400
        )
        return response


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Регистрация нового пользователя",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password', 'email'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, min_length=4),
                'password': openapi.Schema(type=openapi.TYPE_STRING, min_length=8, format="password"),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format="email"),
            },
        ),
        responses={
            201: openapi.Response(
                description="Пользователь успешно зарегистрирован",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'session_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'role': openapi.Schema(type=openapi.TYPE_STRING),
                                'role_display': openapi.Schema(type=openapi.TYPE_STRING),
                                'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            }
                        )
                    }
                )
            ),
            400: "Некорректные данные",
            409: "Пользователь уже существует"
        }
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email", "")
        
        if not username or not password:
            return Response(
                {"error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(password) < 8:
            return Response(
                {"error": "Password must be at least 8 characters long"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"},
                status=status.HTTP_409_CONFLICT
            )
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        session_id = create_or_get_session(user)
        
        response_data = {
            "session_id": session_id,
            "user": UserBasicSerializer(user).data  # Используем UserBasicSerializer
        }
        
        response = Response(response_data, status=status.HTTP_201_CREATED)
        response.set_cookie(
            key="session_token",
            value=session_id,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Strict',
            max_age=86400
        )
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Выход из системы",
        manual_parameters=[
            openapi.Parameter(
                name='X-Session-ID',
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description='Идентификатор сессии',
                required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description="Успешный выход",
                examples={
                    'application/json': {
                        "message": "Successfully logged out"
                    }
                }
            ),
            400: "Не указан идентификатор сессии",
            401: "Не авторизован"
        }
    )
    def post(self, request):
        session_id = request.headers.get('X-Session-ID') or request.COOKIES.get('session_token')
        
        if not session_id:
            return Response(
                {"error": "Session ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        delete_session(session_id)
        logout(request)
        
        response = Response(
            {"message": "Successfully logged out"},
            status=status.HTTP_200_OK
        )
        response.delete_cookie('session_token')
        return response


class SessionCheckView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Проверка активности сессии",
        manual_parameters=[
            openapi.Parameter(
                name='X-Session-ID',
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description="Сессия активна",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'role': openapi.Schema(type=openapi.TYPE_STRING),
                        'role_display': openapi.Schema(type=openapi.TYPE_STRING),
                        'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            ),
            401: "Сессия недействительна"
        }
    )
    def get(self, request):
        session_id = request.headers.get('X-Session-ID')
        user = get_session_user(session_id)
        
        if not user:
            return Response(
                {"error": "Invalid session"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        refresh_session(session_id)
        
        return Response(
            UserBasicSerializer(user).data,  # Используем UserBasicSerializer
            status=status.HTTP_200_OK
        )