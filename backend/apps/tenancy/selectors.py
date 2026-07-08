from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from .models import Client, ClientMembership

User = get_user_model()


def user_is_admin(user) -> bool:
    return bool(user and user.is_authenticated and (user.role == User.Role.ADMIN or user.is_superuser))


def visible_clients_for(user) -> QuerySet[Client]:
    if not user or not user.is_authenticated:
        return Client.objects.none()
    if user_is_admin(user):
        return Client.objects.all()
    return Client.objects.filter(
        memberships__user=user,
        memberships__is_active=True,
    ).distinct()


def has_active_client_membership(user, client: Client) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    return ClientMembership.objects.filter(
        user=user,
        client=client,
        is_active=True,
    ).exists()


def can_write_client_records(user, client: Client) -> bool:
    if user_is_admin(user):
        return True
    return bool(
        user
        and user.is_authenticated
        and user.role == User.Role.CONSULTANT
        and has_active_client_membership(user, client)
    )


def can_manage_clients(user) -> bool:
    return user_is_admin(user)
