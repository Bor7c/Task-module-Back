from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from app.models import Team, User
from app.serializers import (
    TeamBasicSerializer,
    TeamDetailSerializer,
    TeamCreateUpdateSerializer
)
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TeamDetailSerializer
        return TeamCreateUpdateSerializer

    def get_queryset(self):
        return self.request.user.get_available_teams()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != 'admin':
            raise PermissionDenied("У вас нет прав на создание команды.")
        serializer.save()

    def perform_update(self, serializer):
        team = self.get_object()
        if not self.request.user.can_manage_team(team):
            raise PermissionDenied("У вас нет прав на редактирование этой команды.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        team = self.get_object()
        if not request.user.can_manage_team(team):
            raise PermissionDenied("У вас нет прав на удаление этой команды.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        team = self.get_object()
        user = self.request.user

        if not user.can_add_members_to_team(team):
            raise PermissionDenied("У вас нет прав добавлять пользователей в эту команду.")

        member_id = request.data.get('user_id')
        if not member_id:
            return Response({'error': 'user_id обязателен'}, status=400)

        try:
            new_member = User.objects.get(pk=member_id)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=404)

        team.members.add(new_member)
        team.refresh_from_db()

        serializer = TeamDetailSerializer(team, context={'request': request})
        return Response(serializer.data, status=200)

    @action(detail=True, methods=['post'], url_path='remove-member')
    def remove_member(self, request, pk=None):
        team = self.get_object()
        user = self.request.user

        if not user.can_remove_members_from_team(team):
            raise PermissionDenied("У вас нет прав удалять пользователей из этой команды.")

        member_id = request.data.get('user_id')
        if not member_id:
            return Response({'error': 'user_id обязателен'}, status=400)

        try:
            member = User.objects.get(pk=member_id)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=404)

        if not team.members.filter(pk=member.pk).exists():
            return Response({'error': 'Пользователь не является участником этой команды'}, status=400)

        team.members.remove(member)
        team.refresh_from_db()

        serializer = TeamDetailSerializer(team, context={'request': request})
        return Response(serializer.data, status=200)
