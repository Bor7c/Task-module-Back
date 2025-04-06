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
    author = UserBasicSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='author',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Comment
        fields = [
            'id', 
            'task', 
            'author', 
            'author_id',
            'text', 
            'created_at',
            'is_system'
        ]
        read_only_fields = ['created_at', 'is_system']

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