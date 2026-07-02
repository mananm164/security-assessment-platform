from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.findings.models import Finding
from apps.tenancy.selectors import can_write_client_records

from ..models import FindingSource, ScannerObservation
from ..parsers.nmap import sanitise_evidence


@transaction.atomic
def promote_observation_to_finding(
    *,
    observation: ScannerObservation,
    actor,
    cvss_score,
    business_impact: str,
    remediation_owner: str,
    due_date,
    title: str | None = None,
    description: str | None = None,
    remediation: str | None = None,
) -> Finding:
    if not can_write_client_records(actor, observation.assessment.client):
        raise PermissionDenied("You cannot promote this observation.")
    if observation.triage_status != ScannerObservation.TriageStatus.CONFIRMED:
        raise ValidationError("Only confirmed observations can be promoted.")
    if observation.asset is None:
        raise ValidationError("Observation must have an affected asset before promotion.")
    if FindingSource.objects.filter(scanner_observation=observation).exists():
        raise ValidationError("Observation has already been promoted.")

    finding = Finding.objects.create(
        assessment=observation.assessment,
        affected_asset=observation.asset,
        title=sanitise_evidence(title or observation.title, max_length=255),
        description=sanitise_evidence(description or observation.description, max_length=4000),
        cvss_score=cvss_score,
        business_impact=sanitise_evidence(business_impact, max_length=4000),
        remediation=sanitise_evidence(
            remediation or observation.suggested_remediation or "Review and remediate the confirmed observation.",
            max_length=4000,
        ),
        remediation_owner=sanitise_evidence(remediation_owner, max_length=255),
        due_date=due_date,
        created_by=actor,
    )
    FindingSource.objects.create(
        finding=finding,
        scanner_observation=observation,
        first_seen_at=observation.first_seen_at,
        last_seen_at=observation.last_seen_at,
    )
    observation.triage_status = ScannerObservation.TriageStatus.PROMOTED
    observation.triaged_by = actor
    observation.triaged_at = timezone.now()
    observation.save(update_fields=["triage_status", "triaged_by", "triaged_at", "updated_at"])
    return finding
