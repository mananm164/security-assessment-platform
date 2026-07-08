from django.db.models import QuerySet

from apps.tenancy.selectors import visible_clients_for

from .models import Asset, Assessment


def visible_assessments_for(user) -> QuerySet[Assessment]:
    return Assessment.objects.filter(client__in=visible_clients_for(user)).select_related("client", "created_by")


def visible_assets_for(user) -> QuerySet[Asset]:
    return Asset.objects.filter(assessment__client__in=visible_clients_for(user)).select_related(
        "assessment", "assessment__client"
    )
