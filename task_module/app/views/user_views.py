from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.exceptions import PermissionDenied
from PIL import Image
from ..models import User
from ..serializers import (
    UserBasicSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)
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
    parser_classes = [JSONParser]  # только JSON

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserBasicSerializer

    def get_object(self):
        if self.kwargs.get('pk') == 'me':
            return self.request.user
        obj = super().get_object()
        if obj != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("Вы можете просматривать только свой профиль")
        return obj

    @swagger_auto_schema(
        operation_description="Обновить данные пользователя (без картинки)",
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER,
                              description="Идентификатор сессии",
                              type=openapi.TYPE_STRING, required=True)
        ],
        request_body=UserUpdateSerializer,
        responses={200: UserBasicSerializer()}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частичное обновление пользователя (без картинки)",
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER,
                              description="Идентификатор сессии",
                              type=openapi.TYPE_STRING, required=True)
        ],
        request_body=UserUpdateSerializer,
        responses={200: UserBasicSerializer()}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


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
    authentication_classes = [RedisSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(
        operation_description="Загрузить фото профиля пользователя",
        manual_parameters=[
            openapi.Parameter('X-Session-ID', openapi.IN_HEADER,
                              description="Сессия", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('user_id', openapi.IN_QUERY,
                              description="ID пользователя", type=openapi.TYPE_INTEGER, required=False)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'profile_picture': openapi.Schema(type=openapi.TYPE_FILE)},
            required=['profile_picture']
        ),
        responses={
            200: openapi.Response("Успешно", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={'profile_picture_url': openapi.Schema(type=openapi.TYPE_STRING)}
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

        try:
            img = Image.open(uploaded_file)
            img.verify()
        except Exception:
            return Response({'detail': 'Недопустимый формат изображения'}, status=400)

        user.profile_picture = uploaded_file
        user.save(update_fields=['profile_picture'])

        return Response({
            'profile_picture_url': user.profile_picture.url
        }, status=200)


class UserProfilePictureDeleteView(views.APIView):
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
            user.profile_picture.delete(save=False)
        user.profile_picture = None
        user.save(update_fields=['profile_picture'])

        return Response(status=status.HTTP_204_NO_CONTENT)
