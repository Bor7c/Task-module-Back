from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class Team(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    members = models.ManyToManyField('User', related_name='teams', blank=True, verbose_name='Участники')
    is_default = models.BooleanField(default=False, verbose_name='Команда по умолчанию')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалена')  # новое поле

    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        """Мягкое удаление"""
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])

    @classmethod
    def create_default_teams(cls):
        default_teams = [
            {'name': 'Администраторы', 'description': 'Команда администраторов системы', 'is_default': True},
            {'name': 'Менеджеры', 'description': 'Команда менеджеров проекта', 'is_default': True},
        ]
        
        for team_data in default_teams:
            cls.objects.get_or_create(
                name=team_data['name'],
                defaults={
                    'description': team_data['description'],
                    'is_default': team_data['is_default']
                }
            )

    @classmethod
    def active(cls):
        """Возвращает только не удалённые команды"""
        return cls.objects.filter(is_deleted=False)



def sync_user_team_membership(user: 'User'):
    role_team_mapping = {
        'admin': 'Администраторы',
        'manager': 'Менеджеры',
    }

    for role, team_name in role_team_mapping.items():
        team, _ = Team.objects.get_or_create(name=team_name)
        if user.role == role:
            team.members.add(user)
        else:
            team.members.remove(user)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
        ('developer', 'Разработчик'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='developer',
        verbose_name='Роль'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активный')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True, verbose_name='Фото профиля')
    first_name = models.CharField(max_length=150, blank=True, verbose_name='Имя')
    last_name = models.CharField(max_length=150, blank=True, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=150, blank=True, verbose_name='Отчество')

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        previous_role = None

        if not is_new:
            previous_role = User.objects.get(pk=self.pk).role

        super().save(*args, **kwargs)

        if is_new or self.role != previous_role:
            sync_user_team_membership(self)

    def get_available_teams(self):
        """Возвращает queryset команд, доступных пользователю"""
        if self.role in ['admin', 'manager']:
            return Team.objects.all()
        return self.teams.all()

    def get_my_teams(self):
        """Возвращает команды, в которых пользователь является участником"""
        return self.teams.all()

    def can_manage_team(self, team):
        return self.role == 'admin'

    def can_view_team(self, team):
        return self.role in ['admin', 'manager'] or team in self.teams.all()

    def can_add_members_to_team(self, team):
        return self.role in ['admin', 'manager']

    def can_remove_members_from_team(self, team):
        return self.role == 'admin'


    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    def get_full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join(part for part in parts if part).strip() or self.username

class Task(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'В работе'),
        ('solved', 'Решен'),
        ('closed', 'Закрыт'),
        ('awaiting_response', 'Ожидает ответа'),
        ('awaiting_action', 'Ожидает действий'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]

    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='awaiting_action',
        verbose_name='Статус'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Приоритет'
    )
    responsible = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name='Ответственный',
        limit_choices_to={'is_active': True}
    )
    is_assigned = models.BooleanField(
        default=False,
        verbose_name='Назначен ли ответственный'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_tasks',
        verbose_name='Создатель'
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        related_name='tasks',
        verbose_name='Команда',
        null=False,
        blank=False
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата закрытия')
    deadline = models.DateTimeField(null=True, blank=True, verbose_name='Срок выполнения')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалено')
    is_overdue = models.BooleanField(default=False, verbose_name='Просрочено')

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['deadline']),
            models.Index(fields=['is_overdue']),
        ]
    
    def __str__(self):
        return f"{self.title} (Статус: {self.get_status_display()}, Назначен: {'Да' if self.is_assigned else 'Нет'})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Проверка, что создатель имеет доступ к выбранной команде
        if self.pk is None:  # Только для новых задач
            if not self.created_by.get_available_teams().filter(pk=self.team_id).exists():
                raise ValidationError("Создатель задачи не имеет доступа к выбранной команде")
            
        # Проверка, что ответственный находится в команде задачи
        if self.responsible and not self.team.members.filter(pk=self.responsible.pk).exists():
            raise ValidationError("Ответственный должен быть членом команды задачи")

    def save(self, *args, **kwargs):
        if self.pk:
            original = Task.objects.get(pk=self.pk)
            if self.status == 'closed' and original.status != 'closed':
                self.closed_at = timezone.now()
            elif self.status != 'closed' and original.status == 'closed':
                self.closed_at = None
        
        self.is_assigned = bool(self.responsible)
        self.update_overdue_status()
        super().save(*args, **kwargs)
    
    def update_overdue_status(self):
        now = timezone.now()
        if not self.deadline or self.deadline >= now:
            self.is_overdue = False
        elif self.status in ['in_progress', 'awaiting_response', 'awaiting_action']:
            self.is_overdue = True

    @classmethod
    def update_all_overdue_statuses(cls):
        now = timezone.now()
        active_tasks = cls.objects.filter(
            status__in=['in_progress', 'awaiting_response', 'awaiting_action'],
            is_deleted=False,
            deadline__isnull=False,
            deadline__lt=now,
            is_overdue=False
        )
        overdue_count = active_tasks.update(is_overdue=True)

        not_overdue_tasks = cls.objects.filter(
            is_deleted=False,
            deadline__isnull=False,
            deadline__gte=now,
            is_overdue=True
        )
        not_overdue_count = not_overdue_tasks.update(is_overdue=False)

        no_deadline_tasks = cls.objects.filter(
            is_deleted=False,
            deadline__isnull=True,
            is_overdue=True
        )
        no_deadline_count = no_deadline_tasks.update(is_overdue=False)
        
        return overdue_count + not_overdue_count + no_deadline_count
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])

class Comment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Задача'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_system = models.BooleanField(default=False, verbose_name='Системное сообщение')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалено')
    is_modified = models.BooleanField(default=False, verbose_name='Редактировался')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['task']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Комментарий #{self.id} к задаче {self.task_id}"

    def save(self, *args, **kwargs):
        if self.pk:
            kwargs['update_fields'] = kwargs.get('update_fields', []) + ['updated_at']
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])

def get_attachment_upload_path(instance, filename):
    task_id = instance.task.id if instance.task else 'no_task'
    return f'attachments/task_{task_id}/{filename}'

class Attachment(models.Model):
    file = models.FileField(upload_to=get_attachment_upload_path, verbose_name='Файл')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='uploaded_attachments',
        verbose_name='Загрузивший пользователь'
    )
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments',
        null=True,
        blank=True,
        verbose_name='Задача'
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='attachments',
        null=True,
        blank=True,
        verbose_name='Комментарий'
    )

    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложения'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'Файл: {self.file.name}'

# Сигнал для создания команд по умолчанию после миграций
@receiver(post_migrate)
def create_default_teams(sender, **kwargs):
    from django.apps import apps
    if sender.name == 'app':
        Team = apps.get_model('app', 'Team')
        Team.create_default_teams()
