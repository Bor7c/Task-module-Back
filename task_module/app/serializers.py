from rest_framework import serializers
from .models import Task, Comment, User
from django.utils import timezone

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
        read_only_fields = fields

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
            'password': {
                'write_only': True,
                'min_length': 8  # Добавлена минимальная длина пароля
            },
            'email': {
                'required': True,
                'allow_blank': False
            }
        }

    def validate_email(self, value):
        """Проверка уникальности email с учетом регистра"""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value.lower()  # Приводим email к нижнему регистру

    def create(self, validated_data):
        """Создание пользователя с хешированием пароля"""
        return User.objects.create_user(
            **validated_data,
            is_active=True
        )

class CommentSerializer(serializers.ModelSerializer):
    author = UserBasicSerializer(read_only=True)
    is_modified = serializers.SerializerMethodField()  # Изменено на метод
    
    class Meta:
        model = Comment
        fields = [
            'id',
            'text',
            'author',
            'task',
            'created_at',
            'updated_at',  # Исправлено с modified_at на updated_at (как в модели)
            'is_system',
            'is_modified',
            'is_deleted'
        ]
        read_only_fields = [
            'id', 'author', 'created_at', 'updated_at',
            'is_system', 'is_modified', 'is_deleted'
        ]
        extra_kwargs = {
            'text': {
                'required': True,
                'allow_blank': False,
                'min_length': 2,  # Добавлена минимальная длина
                'error_messages': {
                    'blank': 'Текст комментария не может быть пустым',
                    'min_length': 'Комментарий должен содержать минимум 2 символа'
                }
            }
        }

    def get_is_modified(self, obj):
        """Определяем, был ли изменен комментарий"""
        return obj.updated_at > obj.created_at

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
        return obj.status == 'closed'

class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    responsible_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),  # Добавлен фильтр по активным пользователям
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
            'title': {
                'min_length': 3,
                'max_length': 255  # Добавлена максимальная длина
            },
            'description': {
                'required': False,
                'allow_blank': True,
                'max_length': 5000  # Добавлена максимальная длина
            },
            'status': {
                'required': False,
                'default': 'unassigned'  # Добавлено значение по умолчанию
            },
            'priority': {
                'required': False,
                'default': 'medium'  # Добавлено значение по умолчанию
            }
        }

    def validate_status(self, value):
        if value == 'closed' and not self.instance:
            raise serializers.ValidationError(
                "Невозможно создать задачу со статусом 'closed'"
            )
        return value

    def validate(self, data):
        if data.get('status') == 'closed':
            if not data.get('description'):
                raise serializers.ValidationError(
                    {"description": "Требуется описание перед закрытием задачи"}
                )
            # Автоматически устанавливаем дату закрытия
            if not self.instance or not self.instance.closed_at:
                data['closed_at'] = timezone.now()
        elif 'status' in data and data['status'] != 'closed' and self.instance and self.instance.closed_at:
            # Сбрасываем дату закрытия если статус изменился с closed
            data['closed_at'] = None
            
        return data

    def create(self, validated_data):
        """Автоматическое назначение created_by"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)