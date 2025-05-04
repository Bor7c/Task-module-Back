from rest_framework import serializers
from .models import Task, Comment, User, Attachment
from django.utils import timezone

class UserBasicSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    profile_picture_url = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'middle_name',
            'full_name',
            'role',
            'role_display',
            'profile_picture_url'
        ]
        read_only_fields = fields

    def get_profile_picture_url(self, obj):
        if obj.profile_picture and hasattr(obj.profile_picture, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'middle_name',
            'profile_picture'
        ]
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'middle_name': {'required': False, 'allow_blank': True},
            'profile_picture': {'required': False}
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value.lower()

    def create(self, validated_data):
        return User.objects.create_user(
            **validated_data,
            is_active=True
        )

class UserUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'middle_name',
            'email',
            'profile_picture'
        ]
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'middle_name': {'required': False, 'allow_blank': True},
            'email': {'required': False},
            'profile_picture': {'required': False}
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value.lower()

    def update(self, instance, validated_data):
        # Разрешаем обновлять только определенные поля для обычных пользователей
        if not self.context['request'].user.is_staff:
            allowed_fields = {'first_name', 'last_name', 'middle_name', 'email', 'profile_picture'}
            for field in list(validated_data.keys()):
                if field not in allowed_fields:
                    validated_data.pop(field)
        
        return super().update(instance, validated_data)



class AttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    filename = serializers.SerializerMethodField()
    uploaded_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = Attachment
        fields = [
            'id',
            'file_url',
            'filename',
            'uploaded_at',
            'uploaded_by',
            'task'
        ]
        read_only_fields = fields

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None

    def get_filename(self, obj):
        return obj.file.name.split('/')[-1] if obj.file else None


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
            'id', 'author', 'created_at', 'updated_at', 'is_system', 'is_modified', 'is_deleted'
        ]

    def get_is_modified(self, obj):
        return obj.created_at != obj.updated_at


class TaskListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    responsible = UserBasicSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

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

    def get_is_overdue(self, obj):
        if obj.deadline and obj.status != 'closed':
            return obj.deadline < timezone.now()
        return False


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
    attachments = serializers.ListField(
        child=serializers.FileField(),
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
            'deadline',
            'responsible_id',
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
            },
            'status': {
                'required': False,
                'default': 'awaiting_action'
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
        attachments = validated_data.pop('attachments', [])
        validated_data['created_by'] = self.context['request'].user
        task = super().create(validated_data)
        
        for attachment in attachments:
            Attachment.objects.create(
                file=attachment,
                task=task,
                uploaded_by=validated_data['created_by']
            )
        
        return task

    def update(self, instance, validated_data):
        attachments = validated_data.pop('attachments', [])
        task = super().update(instance, validated_data)
        
        for attachment in attachments:
            Attachment.objects.create(
                file=attachment,
                task=task,
                uploaded_by=self.context['request'].user
            )
        
        return task