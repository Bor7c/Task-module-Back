# app/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from app.utils.auth import refresh_session

class RedisSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        session_id = request.COOKIES.get('session_token') or request.headers.get('X-Session-ID')
        if session_id:
            refresh_session(session_id)