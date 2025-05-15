from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from django.apps import apps
from datetime import timedelta
import random

@receiver(post_migrate)
def create_superuser_and_demo_data(sender, **kwargs):
    if sender.name != 'app':
        return

    User = get_user_model()
    Task = apps.get_model('app', 'Task')
    Team = apps.get_model('app', 'Team')
    Comment = apps.get_model('app', 'Comment')

    # ✅ Удаляем "тестовых" пользователей и перераспределяем задачи
    test_users = User.objects.filter(first_name="Пользователь", last_name="Тестов")
    other_users = User.objects.exclude(id__in=test_users.values_list('id', flat=True))

    for user in test_users:
        Task.objects.filter(responsible=user).update(responsible=random.choice(other_users))
        Task.objects.filter(created_by=user).update(created_by=random.choice(other_users))
        print(f"❌ Удалён пользователь {user.username}")
        user.delete()

    # ✅ Суперпользователь
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'password': 'admin',
            'role': 'admin',
            'first_name': 'Админ',
            'last_name': 'Супер',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin.set_password('admin')
        admin.save()
        print('✅ Суперпользователь admin/admin создан')

    # ✅ Команды
    if hasattr(Team, 'create_default_teams'):
        Team.create_default_teams()

    team_admin = Team.objects.get(name='Администраторы')
    team_manager = Team.objects.get(name='Менеджеры')

    team_alpha = Team.objects.get_or_create(name='Альфа', defaults={'description': 'Команда Альфа'})[0]
    team_beta = Team.objects.get_or_create(name='Бета', defaults={'description': 'Команда Бета'})[0]

    team_admin.members.add(admin)

    # ✅ Пользователи
    users_data = [
        ('boris.sokolov', 'Соколов', 'Борис', 'manager'),
        ('yana.zhdanova', 'Жданова', 'Яна', 'developer'),
        ('mikhail.lavrenov', 'Лавренов', 'Михаил', 'developer'),
        ('oleg.petrov', 'Петров', 'Олег', 'developer'),
        ('irina.kuznetsova', 'Кузнецова', 'Ирина', 'developer'),
    ]

    users = {}
    for username, last_name, first_name, role in users_data:
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': first_name,
                'last_name': last_name,
                'role': role,
            }
        )
        user.set_password('12345')
        user.save()
        users[username] = user

    # ✅ Назначение в команды
    team_manager.members.add(users['boris.sokolov'])
    team_alpha.members.add(users['yana.zhdanova'])
    team_beta.members.add(users['mikhail.lavrenov'], users['oleg.petrov'], users['irina.kuznetsova'])

    # ✅ Генерация задач с заданной датой создания
    statuses = ['in_progress', 'closed', 'awaiting_response', 'awaiting_action', 'solved']
    priorities = ['low', 'medium', 'high', 'critical']
    titles = [
        'Настроить интеграцию с API', 'Обновить документацию', 'Исправить баг в отчёте',
        'Добавить фильтр по дате', 'Реализовать экспорт CSV', 'Оптимизировать запросы БД',
        'Создание справочника', 'Анализ пользовательского фидбека', 'Проверка безопасности',
        'Внедрение логирования', 'Рефакторинг сервисов', 'Миграция данных', 'UI тесты',
        'Внедрение CI/CD', 'Создание бэкапа', 'Добавление уведомлений',
        'Создание отчёта', 'Модуль авторизации', 'Проверка роли пользователя',
        'Создание dashboard интерфейса'
    ]

    teams = [team_manager, team_alpha, team_beta]
    responsible_users = list(users.values())
    creators = responsible_users + [admin]

    now = timezone.now()
    for i, title in enumerate(titles):
        created_by = random.choice(creators)
        team = random.choice(teams)
        responsible = random.choice(team.members.all()) if team.members.exists() else None

        deadline = now + timedelta(days=random.randint(-10, 10)) if i % 3 != 0 else None
        closed_at = now + timedelta(days=random.randint(1, 5)) if i % 4 == 0 else None
        status = random.choice(statuses)
        priority = random.choice(priorities)
        created_at = now - timedelta(days=random.randint(1, 30))

        task = Task.objects.create(
            title=title,
            description=f"Подробное описание задачи '{title}'.",
            status=status,
            priority=priority,
            responsible=responsible,
            created_by=created_by,
            team=team,
            deadline=deadline,
            closed_at=closed_at,
            created_at=created_at
        )

        # ✅ Комментарии от допустимых пользователей (создатель или члены команды)
        possible_commenters = list(team.members.all())
        if created_by not in possible_commenters:
            possible_commenters.append(created_by)

        possible_commenters = list(set(possible_commenters))  # Уникальные

        for j in range(random.randint(1, 3)):
            author = random.choice(possible_commenters)
            Comment.objects.create(
                task=task,
                author=author,
                text=f"Комментарий {j + 1} к задаче '{title}'"
            )

        print(f"✅ Задача '{title}' создана для команды '{team.name}'")
