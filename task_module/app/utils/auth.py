# app/utils/auth.py
import redis
from django.conf import settings
import uuid
from datetime import timedelta
from redis.exceptions import ConnectionError as RedisConnectionError
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from rest_framework import authentication


# Инициализация Redis подключения
try:
    redis_instance = redis.StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=2,
        retry_on_timeout=True
    )
    redis_instance.ping()
except RedisConnectionError as e:
    print(f"Redis connection error: {e}")
    raise

class RedisSessionAuthentication(authentication.BaseAuthentication):
    """Кастомный класс аутентификации через Redis сессии"""
    
    def authenticate(self, request):
        # Пробуем получить session_id из кук или заголовков
        session_id = request.COOKIES.get('session_token') or request.headers.get('X-Session-ID')
        
        if not session_id:
            return None
        
        try:
            session_data = redis_instance.hgetall(f'session:{session_id}')
            
            if not session_data:
                raise AuthenticationFailed('Сессия недействительна или истекла')
                
            User = get_user_model()
            try:
                user = User.objects.get(id=session_data['user_id'])
                return (user, None)
            except User.DoesNotExist:
                raise AuthenticationFailed('Пользователь не найден')
                
        except Exception as e:
            raise AuthenticationFailed(f'Ошибка аутентификации: {str(e)}')

def get_user_session_key(user_id, username):
    """Генерация ключа для хранения связи пользователь-сессия"""
    return f"user:{user_id}:session:{username}"

def create_or_get_session(user):
    """Создание или получение существующей сессии"""
    try:
        # Проверка существующей сессии
        user_session_key = get_user_session_key(user.id, user.username)
        existing_session_id = redis_instance.get(user_session_key)
        
        if existing_session_id and redis_instance.exists(f"session:{existing_session_id}"):
            # Обновляем TTL существующей сессии
            redis_instance.expire(f"session:{existing_session_id}", 86400)
            redis_instance.expire(user_session_key, 86400)
            return existing_session_id
        
        # Создание новой сессии
        session_id = str(uuid.uuid4())
        user_data = {
            'user_id': str(user.id),
            'username': user.username,
            'email': user.email,
            'is_active': str(user.is_active),
            'is_staff': str(user.is_staff),
            'is_superuser': str(user.is_superuser),
        }
        
        # Сохраняем данные сессии
        redis_instance.hmset(f'session:{session_id}', user_data)
        redis_instance.expire(f'session:{session_id}', 86400)
        
        # Связываем пользователя с сессией
        redis_instance.setex(user_session_key, 86400, session_id)
        
        return session_id
        
    except RedisConnectionError as e:
        print(f"Redis error in create_or_get_session: {e}")
        raise

def delete_session(session_id):
    """Удаление сессии по её ID"""
    try:
        session_data = redis_instance.hgetall(f'session:{session_id}')
        if session_data:
            user_id = session_data.get('user_id')
            username = session_data.get('username')
            if user_id and username:
                redis_instance.delete(get_user_session_key(user_id, username))
        redis_instance.delete(f'session:{session_id}')
    except RedisConnectionError as e:
        print(f"Redis error in delete_session: {e}")
        raise

def get_session_user(session_id):
    """Получение пользователя по ID сессии"""
    try:
        session_data = redis_instance.hgetall(f'session:{session_id}')
        if not session_data:
            return None
            
        User = get_user_model()
        return User.objects.get(id=session_data['user_id'])
    except Exception:
        return None

def refresh_session(session_id):
    """Обновление TTL сессии"""
    try:
        if redis_instance.exists(f'session:{session_id}'):
            redis_instance.expire(f'session:{session_id}', 86400)
            session_data = redis_instance.hgetall(f'session:{session_id}')
            if session_data.get('user_id') and session_data.get('username'):
                user_key = get_user_session_key(
                    session_data['user_id'],
                    session_data['username']
                )
                redis_instance.expire(user_key, 86400)
            return True
        return False
    except RedisConnectionError as e:
        print(f"Redis error in refresh_session: {e}")
        raise