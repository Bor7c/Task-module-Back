import redis
from django.conf import settings
import uuid
from datetime import timedelta

# Подключение к Redis
redis_instance = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

def create_session(user):
    """
    Создает сессию пользователя в Redis
    """
    session_id = str(uuid.uuid4())
    user_data = {
        'user_id': str(user.id),
        'username': user.username,
        'email': user.email,
        # Добавьте другие необходимые поля
    }
    
    # Сохраняем данные на 1 день (86400 секунд)
    redis_instance.hmset(f'session:{session_id}', user_data)
    redis_instance.expire(f'session:{session_id}', 86400)
    
    return session_id

def get_session(session_id):
    """
    Получает данные сессии из Redis
    """
    if not session_id:
        return None
    
    session_key = f'session:{session_id}'
    if not redis_instance.exists(session_key):
        return None
    
    return redis_instance.hgetall(session_key)

def delete_session(session_id):
    """
    Удаляет сессию из Redis
    """
    redis_instance.delete(f'session:{session_id}')