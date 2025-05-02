from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image  # type: ignore
from io import BytesIO

from ..models import User
from ..serializers import UserBasicSerializer, UserCreateSerializer
from app.utils.auth import RedisSessionAuthentication


class UserListView(generics.ListAPIView):
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserBasicSerializer

    @swagger_auto_schema(
        operation_description="Получить список всех пользователей",
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER,
                              description="Идентификатор сессии",
                              type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: UserBasicSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [RedisSessionAuthentication]
    queryset = User.objects.all()

    def get_serializer_class(self):
        return UserBasicSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    @swagger_auto_schema(
        operation_description="Получить информацию о пользователе",
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER,
                              description="Идентификатор сессии",
                              type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: UserBasicSerializer()}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Обновить данные пользователя (только админ)",
        request_body=UserBasicSerializer,
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER,
                              description="Сессия администратора",
                              type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: UserBasicSerializer()}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частичное обновление пользователя (только админ)",
        request_body=UserBasicSerializer,
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER,
                              description="Сессия администратора",
                              type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: UserBasicSerializer()}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удалить пользователя (только админ)",
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER,
                              description="Сессия администратора",
                              type=openapi.TYPE_STRING, required=True)
        ],
        responses={204: 'Пользователь удалён'}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Регистрация нового пользователя",
        request_body=UserCreateSerializer,
        responses={201: UserCreateSerializer()}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserProfilePictureUploadView(views.APIView):
    """Загрузка изображения профиля"""
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(
        operation_description="Загрузить фото профиля пользователя (только изображение)",
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER,
                              description="Сессия", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('user_id', openapi.IN_QUERY,
                              description="ID пользователя", type=openapi.TYPE_INTEGER, required=False)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'profile_picture': openapi.Schema(type=openapi.TYPE_FILE)
            },
            required=['profile_picture']
        ),
        responses={
            200: openapi.Response("Успешно", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'profile_picture_url': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )),
            400: 'Неверный формат файла'
        }
    )
    def post(self, request):
        user_id = request.query_params.get('user_id')
        user = request.user if not user_id else User.objects.get(pk=user_id)

        uploaded_file = request.FILES.get('profile_picture')

        if not uploaded_file:
            return Response({'detail': 'Файл не предоставлен'}, status=400)

        #Проверка, что это изображение с помощью Pillow (закомментировано)
        try:
            img = Image.open(uploaded_file)
            img.verify()  # Проверка, что файл является допустимым изображением
        except Exception:
            return Response({'detail': 'Недопустимый формат изображения'}, status=400)

        # Сохранение изображения
        user.profile_picture = uploaded_file
        user.save(update_fields=['profile_picture'])

        return Response({
            'profile_picture_url': user.profile_picture.url
        }, status=200)


class UserProfilePictureDeleteView(views.APIView):
    """Удаление аватарки пользователя (сброс на null)"""
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Удалить фото профиля пользователя",
        manual_parameters=[
            openapi.Parameter(
                'X-Session-ID',
                openapi.IN_HEADER,
                description="ID сессии пользователя",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,
                description="ID пользователя",
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={
            204: "Фото удалено",
            401: "Не авторизован",
            404: "Пользователь не найден"
        }
    )
    def delete(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        user = request.user if not user_id else User.objects.filter(pk=user_id).first()

        if not user:
            return Response({"detail": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

        if user.profile_picture:
            user.profile_picture.delete(save=False)  # удаляет файл
        user.profile_picture = None
        user.save(update_fields=['profile_picture'])

        return Response(status=status.HTTP_204_NO_CONTENT)
