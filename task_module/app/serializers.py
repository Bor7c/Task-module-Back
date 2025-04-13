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
        read_only_fields = fields  # Все поля только для чтения

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
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate_email(self, value):
        """Проверка уникальности email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value

    def create(self, validated_data):
        """Создание пользователя с хешированием пароля"""
        user = User.objects.create_user(
            **validated_data,
            is_active=True  # Активируем пользователя при создании
        )
        return user

class CommentSerializer(serializers.ModelSerializer):
    author = UserBasicSerializer(read_only=True)
    is_modified = serializers.BooleanField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id',
            'text',
            'author',
            'task',
            'created_at',
            'modified_at',
            'is_system',
            'is_modified',
            'is_deleted'
        ]
        read_only_fields = [
            'id', 'author', 'created_at', 'modified_at',
            'is_system', 'is_modified', 'is_deleted'
        ]
        extra_kwargs = {
            'text': {
                'required': True,
                'allow_blank': False,
                'error_messages': {
                    'blank': 'Текст комментария не может быть пустым'
                }
            }
        }

    def validate(self, data):
        """Дополнительная валидация"""
        if len(data.get('text', '').strip()) < 2:
            raise serializers.ValidationError(
                {"text": "Комментарий должен содержать минимум 2 символа"}
            )
        return data

class TaskListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    responsible = UserBasicSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    
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
            'created_at',
            'updated_at',
            'comments_count'
        ]
        read_only_fields = fields

    def get_comments_count(self, obj):
        """Количество не удаленных комментариев"""
        return obj.comments.filter(is_deleted=False).count()

class TaskDetailSerializer(TaskListSerializer):
    created_by = UserBasicSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    is_closed = serializers.SerializerMethodField()
    
    class Meta(TaskListSerializer.Meta):
        fields = TaskListSerializer.Meta.fields + [
            'description',
            'created_by',
            'closed_at',
            'comments',
            'is_closed'
        ]
    
    def get_is_closed(self, obj):
        """Проверка, закрыта ли задача"""
        return obj.status == 'closed'

class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    responsible_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='responsible',
        write_only=True,
        required=False,
        allow_null=True
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
            'title': {'min_length': 3},
            'description': {'required': False, 'allow_blank': True},
            'status': {'required': False},
            'priority': {'required': False}
        }

    def validate_status(self, value):
        """Валидация статуса"""
        if value == 'closed' and not self.instance:
            raise serializers.ValidationError(
                "Невозможно создать задачу со статусом 'closed'"
            )
        return value

    def validate(self, data):
        """Комплексная валидация"""
        if data.get('status') == 'closed' and not data.get('description'):
            raise serializers.ValidationError(
                {"description": "Требуется описание перед закрытием задачи"}
            )
        return data