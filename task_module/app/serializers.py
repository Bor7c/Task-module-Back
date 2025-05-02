from rest_framework import serializers
from .models import Task, Comment, User, Attachment
from django.utils import timezone

class UserBasicSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'role',
            'role_display',
            'is_staff',
            'profile_picture_url'
        ]
        read_only_fields = fields

    def get_profile_picture_url(self, obj):
        if obj.profile_picture and hasattr(obj.profile_picture, 'url'):
            return obj.profile_picture.url
        return None


class UserCreateSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'profile_picture_url'
        ]
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 8
            },
            'email': {
                'required': True,
                'allow_blank': False
            }
        }

    def get_profile_picture_url(self, obj):
        if obj.profile_picture and hasattr(obj.profile_picture, 'url'):
            return obj.profile_picture.url
        return None

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value.lower()

    def create(self, validated_data):
        return User.objects.create_user(
            **validated_data,
            is_active=True
        )


class AttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ['id', 'file', 'file_url', 'uploaded_at']

    def get_file_url(self, obj):
        if obj.file and hasattr(obj.file, 'url'):
            return obj.file.url
        return None


class CommentSerializer(serializers.ModelSerializer):
    author = UserBasicSerializer(read_only=True)
    is_modified = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id',
            'text',
            'author',
            'task',
            'created_at',
            'updated_at',
            'is_system',
            'is_modified',
            'is_deleted',
        ]
        read_only_fields = [
            'id', 'author', 'created_at', 'updated_at', 'is_system', 'is_modified', 'is_deleted', 'attachments'
        ]
        extra_kwargs = {
            'text': {
                'required': True,
                'allow_blank': False,
                'min_length': 2,
                'error_messages': {
                    'blank': 'Текст комментария не может быть пустым',
                    'min_length': 'Комментарий должен содержать минимум 2 символа'
                }
            }
        }

    def get_is_modified(self, obj):
        return obj.is_modified


class TaskListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    responsible = UserBasicSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)

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
            'comments_count',
            'is_overdue'
        ]
        read_only_fields = fields

    def get_comments_count(self, obj):
        return obj.comments.filter(is_deleted=False).count()


class TaskDetailSerializer(TaskListSerializer):
    created_by = UserBasicSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    is_closed = serializers.SerializerMethodField()

    class Meta(TaskListSerializer.Meta):
        fields = TaskListSerializer.Meta.fields + [
            'description',
            'created_by',
            'closed_at',
            'comments',
            'is_closed',
            'attachments'
        ]

    def get_is_closed(self, obj):
        return obj.status == 'closed'


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    responsible_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source='responsible',
        write_only=True,
        required=False,
        allow_null=True
    )
    responsible = UserBasicSerializer(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'status',
            'priority',
            'responsible_id',  # для записи
            'responsible',     # для чтения
            'deadline',
            'is_overdue',
            'attachments'
        ]
        extra_kwargs = {
            'title': {
                'min_length': 3,
                'max_length': 255
            },
            'description': {
                'required': False,
                'allow_blank': True,
                'max_length': 5000
            },
            'priority': {
                'required': False,
                'default': 'medium'
            }
        }

    def validate_status(self, value):
        if value == 'closed' and not self.instance:
            raise serializers.ValidationError("Невозможно создать задачу со статусом 'closed'")
        return value

    def validate(self, data):
        if data.get('status') == 'closed':
            if not self.instance or not self.instance.closed_at:
                data['closed_at'] = timezone.now()
        elif self.instance and self.instance.closed_at and data.get('status') != 'closed':
            data['closed_at'] = None
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

