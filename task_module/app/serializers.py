from rest_framework import serializers
from .models import Task, Comment, User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_staff']
        extra_kwargs = {
            'password': {'write_only': True}  # Пароль не будет отображаться при сериализации
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'developer')
        )
        return user

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)  # Добавляем информацию об авторе
    
    class Meta:
        model = Comment
        fields = ['id', 'task', 'author', 'text', 'created_at']
        read_only_fields = ['author', 'created_at']

class TaskSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 
            'title', 
            'description', 
            'status', 
            'created_by',
            'assigned_to',
            'created_at', 
            'updated_at', 
            'comments'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """Отдельный сериализатор для создания/обновления задач"""
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'assigned_to']