from apps.accounts.models import User
from apps.tenancy.selectors import visible_clients_for

from .models import AuditLog

RAW_AUDIT_ROLES = {User.Role.ADMIN, User.Role.CONSULTANT, User.Role.MANAGER}


def visible_audit_logs_for(user):
    if not user or not user.is_authenticated or user.role not in RAW_AUDIT_ROLES:
        return AuditLog.objects.none()
    return AuditLog.objects.filter(client__in=visible_clients_for(user)).select_related("client", "assessment", "actor")
