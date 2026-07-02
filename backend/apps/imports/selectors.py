from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from apps.tenancy.selectors import visible_clients_for

from .models import ScanImport, ScannerObservation

User = get_user_model()


def can_read_raw_imports(user) -> bool:
    return bool(user and user.is_authenticated and user.role != User.Role.CLIENT)


def visible_imports_for(user) -> QuerySet[ScanImport]:
    if not can_read_raw_imports(user):
        return ScanImport.objects.none()
    return ScanImport.objects.filter(
        assessment__client__in=visible_clients_for(user)
    ).select_related("assessment", "assessment__client", "imported_by")


def visible_observations_for(user) -> QuerySet[ScannerObservation]:
    if not can_read_raw_imports(user):
        return ScannerObservation.objects.none()
    return ScannerObservation.objects.filter(
        assessment__client__in=visible_clients_for(user)
    ).select_related("assessment", "assessment__client", "asset", "last_seen_import")
