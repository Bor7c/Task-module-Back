from rest_framework import serializers
from .models import Task, Comment, User, Attachment, Team
from django.utils import timezone

class TeamBasicSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            'id',
            'name',
            'description',
            'members_count',
            'is_default'
        ]
        read_only_fields = fields

    def get_members_count(self, obj):
        return obj.members.count()

class TeamDetailSerializer(TeamBasicSerializer):
    members = serializers.SerializerMethodField()

    class Meta(TeamBasicSerializer.Meta):
        fields = TeamBasicSerializer.Meta.fields + ['members']

    def get_members(self, obj):
        members = obj.members.filter(is_active=True)
        return UserBasicSerializer(members, many=True, context=self.context).data

class TeamCreateUpdateSerializer(serializers.ModelSerializer):
    members_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source='members',
        many=True,
        required=False
    )

    class Meta:
        model = Team
        fields = [
            'name',
            'description',
            'members_ids'
        ]
        extra_kwargs = {
            'name': {'min_length': 3, 'max_length': 255},
            'description': {'required': False, 'allow_blank': True}
        }

    def validate_name(self, value):
        if Team.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Команда с таким названием уже существует")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        members = validated_data.pop('members', [])
        team = Team.objects.create(**validated_data)
        
        # Автоматически добавляем создателя в команду, если он не админ/менеджер
        creator = request.user
        if creator.role not in ['admin', 'manager'] and creator not in members:
            team.members.add(creator)
        
        if members:
            team.members.add(*members)
        
        return team

class UserBasicSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    profile_picture_url = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    teams = TeamBasicSerializer(many=True, read_only=True)

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
            'profile_picture_url',
            'teams'
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
            'profile_picture',
            'role'
        ]
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'middle_name': {'required': False, 'allow_blank': True},
            'profile_picture': {'required': False},
            'role': {'required': False, 'default': 'developer'}
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value.lower()

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data, is_active=True)
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    teams_ids = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        source='teams',
        many=True,
        required=False
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'middle_name',
            'email',
            'profile_picture',
            'role',
            'teams_ids'
        ]
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'middle_name': {'required': False, 'allow_blank': True},
            'email': {'required': False},
            'profile_picture': {'required': False},
            'role': {'required': False}
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value.lower()

    def update(self, instance, validated_data):
        # Разрешаем обновлять только определенные поля для обычных пользователей
        request = self.context.get('request')
        if not request.user.is_staff and request.user != instance:
            allowed_fields = {'first_name', 'last_name', 'middle_name', 'email', 'profile_picture'}
            for field in list(validated_data.keys()):
                if field not in allowed_fields:
                    validated_data.pop(field)
        
        teams = validated_data.pop('teams', None)
        instance = super().update(instance, validated_data)
        
        # Обновляем команды, если они были переданы и пользователь имеет права
        if teams is not None and request.user.can_add_to_team():
            instance.teams.set(teams)
        
        return instance

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
    attachments = AttachmentSerializer(many=True, read_only=True)

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
            'attachments'
        ]
        read_only_fields = [
            'id', 'author', 'created_at', 'updated_at', 'is_system', 'is_modified', 'is_deleted', 'attachments'
        ]

    def get_is_modified(self, obj):
        return obj.created_at != obj.updated_at

class TaskListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    responsible = UserBasicSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    team = TeamBasicSerializer(read_only=True)

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
            'team',
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
        return obj.is_overdue

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
    team_id = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        source='team',
        write_only=True,
        required=True
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
            'team_id',
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

    def validate_team_id(self, team):
        request = self.context.get('request')
        if not request.user.get_available_teams().filter(pk=team.pk).exists():
            raise serializers.ValidationError("У вас нет доступа к этой команде")
        return team

    def validate_responsible_id(self, responsible):
        team = self.initial_data.get('team_id')
        if responsible and team:
            if not Team.objects.get(pk=team).members.filter(pk=responsible.pk).exists():
                raise serializers.ValidationError("Ответственный должен быть членом выбранной команды")
        return responsible

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