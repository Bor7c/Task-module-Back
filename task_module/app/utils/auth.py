import redis
from django.conf import settings
import uuid
from datetime import timedelta
from redis.exceptions import ConnectionError as RedisConnectionError

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

def get_user_session_key(user_id, username):
    return f"user:{username}:session"  # Новый читаемый формат

def create_or_get_session(user):
    try:
        # Проверяем, есть ли уже активная сессия
        user_session_key = get_user_session_key(user.id, user.username)
        existing_session_id = redis_instance.get(user_session_key)
        
        if existing_session_id:
            # Проверяем, что сессия еще действительна
            if redis_instance.exists(f"session:{existing_session_id}"):
                return existing_session_id
        
        # Создаем новую сессию
        session_id = str(uuid.uuid4())
        user_data = {
            'user_id': str(user.id),
            'username': user.username,
            'email': user.email,
        }
        
        # Сохраняем данные сессии
        redis_instance.hmset(f'session:{session_id}', user_data)
        redis_instance.expire(f'session:{session_id}', 86400)
        
        # Связываем пользователя с сессией (новый формат ключа)
        redis_instance.setex(user_session_key, 86400, session_id)
        
        return session_id
    except RedisConnectionError as e:
        print(f"Redis error in create_or_get_session: {e}")
        raise

def delete_session(session_id):
    try:
        # Получаем данные сессии, чтобы узнать user_id и username
        session_data = redis_instance.hgetall(f'session:{session_id}')
        if session_data:
            user_id = session_data.get('user_id')
            username = session_data.get('username')
            if user_id and username:
                # Удаляем связь пользователь-сессия (новый формат ключа)
                redis_instance.delete(get_user_session_key(user_id, username))
        # Удаляем саму сессию
        redis_instance.delete(f'session:{session_id}')
    except RedisConnectionError as e:
        print(f"Redis error in delete_session: {e}")
        raise