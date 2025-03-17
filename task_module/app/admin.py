from django.contrib import admin
from .models import Task  # Импортируем вашу модель

# Регистрируем модель в админке
admin.site.register(Task)
