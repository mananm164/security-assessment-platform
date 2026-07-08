from django.db.models import QuerySet

from apps.tenancy.selectors import visible_clients_for

from .models import Finding


def visible_findings_for(user) -> QuerySet[Finding]:
    return Finding.objects.filter(assessment__client__in=visible_clients_for(user)).select_related(
        "assessment",
        "assessment__client",
        "affected_asset",
        "created_by",
    )
