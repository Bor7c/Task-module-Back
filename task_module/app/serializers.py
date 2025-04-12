from rest_framework import serializers
from .models import Task, Comment, User

class UserBasicSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'role',
            'role_display',
            'is_staff'
        ]
        read_only_fields = ['id', 'role_display', 'is_staff']

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'first_name',
            'last_name'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'text', 'author', 'created_at', 'is_system']
        extra_kwargs = {
            'text': {
                'required': True,
                'allow_blank': False,  # Запрещаем пустые строки
                'error_messages': {
                    'blank': 'Текст комментария не может быть пустым'
                }
            }
        }

    def validate_text(self, value):
        """Дополнительная валидация текста"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Текст комментария не может быть пустым")
        return value

    def get_author(self, obj):
        """Информация об авторе"""
        if obj.is_system:
            return {'username': 'system', 'id': None}
        if not obj.author:
            return None
        return {
            'id': obj.author.id,
            'username': obj.author.username,
            'role': obj.author.role
        }

class TaskListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    responsible = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'responsible',
            'deadline',
            'created_at'
        ]

class TaskDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    responsible = UserBasicSerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'responsible',
            'created_by',
            'created_at',
            'updated_at',
            'deadline',
            'comments'
        ]
        read_only_fields = ['created_at', 'updated_at']

class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    responsible_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='responsible',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'status',
            'priority',
            'responsible_id',
            'deadline'
        ]
        extra_kwargs = {
            'status': {'required': False},
            'priority': {'required': False}
        }