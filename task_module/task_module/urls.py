from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Настройка Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Task API",
        default_version='v1',
        description="API for managing tasks",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@tasks.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Админка Django
    path('admin/', admin.site.urls),

    # Подключение маршрутов из приложения app
    path('api/', include('app.urls')),  # Все маршруты из app.urls будут начинаться с /api/

    # Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Маршрут для фронтенда (React)
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
]