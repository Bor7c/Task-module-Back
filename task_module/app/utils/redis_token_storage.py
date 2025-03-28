# app/utils/redis_token_storage.py
import redis
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken

# Подключение к Redis
redis_conn = redis.StrictRedis.from_url(settings.CACHES['default']['LOCATION'])

class RedisTokenStorage:
    @staticmethod
    def store_token(token, user_id):
        try:
            access_token = AccessToken(token)
            jti = access_token.payload['jti']
            expires = access_token.payload['exp'] - access_token.payload['iat']
            
            # Сохраняем access token
            redis_conn.set(
                f'access_{user_id}_{jti}',
                str(token),
                ex=expires
            )
            
            # Добавляем в список активных токенов пользователя
            redis_conn.sadd(f'user_tokens:{user_id}', jti)
            redis_conn.expire(f'user_tokens:{user_id}', expires)
            return True
        except Exception as e:
            print(f"Error storing token: {e}")
            return False

    @staticmethod
    def is_token_valid(token):
        try:
            access_token = AccessToken(token)
            return bool(redis_conn.exists(f'access_{access_token.payload["user_id"]}_{access_token.payload["jti"]}'))
        except Exception as e:
            print(f"Error checking token: {e}")
            return False

    @staticmethod
    def blacklist_token(token):
        try:
            access_token = AccessToken(token)
            jti = access_token.payload['jti']
            user_id = access_token.payload['user_id']
            
            redis_conn.delete(f'access_{user_id}_{jti}')
            redis_conn.srem(f'user_tokens:{user_id}', jti)
            return True
        except Exception as e:
            print(f"Error blacklisting token: {e}")
            return False