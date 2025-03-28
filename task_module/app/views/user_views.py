from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from ..models import User
from ..serializers import UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken, BlacklistMixin
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..utils.redis_token_storage import RedisTokenStorage  # Новый импорт

class UserListView(generics.ListAPIView):
    """Список всех пользователей (только для админов)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали, обновление и удаление пользователя"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

class UserCreateView(generics.CreateAPIView):
    """Создание нового пользователя"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={
            201: openapi.Response("Пользователь создан", UserSerializer),
            400: openapi.Response("Неверные данные")
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class LoginView(APIView):
    """Аутентификация пользователя с JWT и Redis"""
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Response(
                description="Успешная аутентификация",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'role': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                    }
                )
            ),
            401: openapi.Response(
                description="Неверные учетные данные",
                examples={
                    "application/json": {"error": "Invalid credentials"}
                }
            )
        },
        operation_description="Аутентификация пользователя. Возвращает JWT токены и данные пользователя."
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        
        if user:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Сохраняем токен в Redis
            RedisTokenStorage.store_token(access_token, user.id)
            
            return Response({
                'refresh': str(refresh),
                'access': access_token,
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    """Выход из системы с инвалидацией токена"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            200: openapi.Response(
                description="Успешный выход",
                examples={
                    "application/json": {"message": "Successfully logged out"}
                }
            ),
            400: openapi.Response("Ошибка выхода")
        }
    )
    def post(self, request):
        # Инвалидируем access token
        if hasattr(request, 'auth'):
            RedisTokenStorage.blacklist_token(str(request.auth))
        
        # Инвалидируем refresh token если он предоставлен
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except:
                pass
        
        logout(request)
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)

class CurrentUserView(APIView):
    """Получение данных текущего аутентифицированного пользователя"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Получить данные текущего авторизованного пользователя",
        responses={
            200: openapi.Response("Данные пользователя", UserSerializer),
            401: openapi.Response(
                "Не авторизован",
                examples={
                    "application/json": {"detail": "Учетные данные не были предоставлены."}
                }
            )
        },
        security=[{"Bearer": []}],
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT токен в формате 'Bearer {token}'",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class ActiveSessionsView(generics.ListAPIView):
    """Просмотр активных сессий пользователя"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,  # Исправлено здесь
                description="ID пользователя",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={200: "Список активных сессий"}
    )
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Здесь можно реализовать получение активных сессий из Redis
        return Response(
            {'message': 'Active sessions functionality will be implemented here'},
            status=status.HTTP_200_OK
        )