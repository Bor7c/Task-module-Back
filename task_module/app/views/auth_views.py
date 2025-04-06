from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from ..utils.auth import * # Измененный импорт
from ..serializers import UserSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class LoginView(APIView):
    permission_classes = [AllowAny]

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
            200: openapi.Response('Successful login', UserSerializer),
            401: 'Invalid credentials'
        }
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Используем функцию, которая возвращает существующую сессию или создает новую
            session_id = create_or_get_session(user)
            
            response_data = {
                "session_id": session_id,
                "user": UserSerializer(user).data
            }
            
            response = Response(response_data, status=status.HTTP_200_OK)
            response.set_cookie(
                "session_token", 
                session_id, 
                httponly=True, 
                max_age=86400,
                secure=False,
                samesite='Lax'
            )
            return response
        return Response(
            {"error": "Invalid credentials"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            201: openapi.Response('Successful registration', UserSerializer),
            400: 'Username already exists'
        }
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email", "")
        
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = User.objects.create_user(username, email, password)
        user = authenticate(request, username=username, password=password)
        
        # При регистрации тоже используем create_or_get_session
        session_id = create_or_get_session(user)
        
        response_data = {
            "session_id": session_id,
            "user": UserSerializer(user).data
        }
        
        response = Response(response_data, status=status.HTTP_201_CREATED)
        response.set_cookie(
            "session_token", 
            session_id, 
            httponly=True, 
            max_age=86400,
            secure=False,
            samesite='Lax'
        )
        return response


class LogoutView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='session_token',
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description='Session token from cookie',
                required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description='Successfully logged out',
                examples={
                    'application/json': {
                        "message": "Successfully logged out"
                    }
                }
            ),
            400: 'Invalid session token'
        }
    )
    def post(self, request):
        session_id = request.headers.get('session_token') or request.COOKIES.get('session_token')
        
        if not session_id:
            return Response(
                {"error": "Session token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        delete_session(session_id)
        
        response = Response(
            {"message": "Successfully logged out"},
            status=status.HTTP_200_OK
        )
        response.delete_cookie('session_token')
        return response


class CheckAuthView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: openapi.Response('User data', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'username': openapi.Schema(type=openapi.TYPE_STRING),
                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                }
            )),
            401: 'Not authenticated or session expired'
        }
    )
    def get(self, request):
        session_id = request.COOKIES.get('session_token')
        if not session_id:
            return Response(
                {"error": "Not authenticated"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        session_data = get_session(session_id)
        if not session_data:
            return Response(
                {"error": "Session expired or invalid"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return Response({
            "user": {
                "id": session_data['user_id'],
                "username": session_data['username'],
                "email": session_data.get('email', '')
            }
        })