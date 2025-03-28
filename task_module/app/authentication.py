from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from app.utils.redis_token_storage import RedisTokenStorage

class RedisJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            user_and_token = super().authenticate(request)
            if user_and_token and not RedisTokenStorage.is_token_valid(str(user_and_token[1])):
                raise exceptions.AuthenticationFailed('Token is invalid')
            return user_and_token
        except:
            raise exceptions.AuthenticationFailed('Token is invalid')