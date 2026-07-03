from .models import AuditLog
from apps.tenancy.selectors import visible_clients_for


RAW_AUDIT_ROLES = {"ADMIN", "CONSULTANT", "MANAGER", "CLIENT"}


def visible_audit_logs_for(user):
    if not user or not user.is_authenticated or user.role not in RAW_AUDIT_ROLES:
        return AuditLog.objects.none()
    return AuditLog.objects.filter(client__in=visible_clients_for(user)).select_related(
        "client", "assessment", "actor"
    )
