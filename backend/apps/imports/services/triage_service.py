from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event
from apps.tenancy.selectors import can_write_client_records

from ..models import ScannerObservation
from ..parsers.nmap import sanitise_evidence

ALLOWED_TRIAGE_STATUSES = {
    ScannerObservation.TriageStatus.CONFIRMED,
    ScannerObservation.TriageStatus.FALSE_POSITIVE,
    ScannerObservation.TriageStatus.DUPLICATE,
}


@transaction.atomic
def triage_observation(
    *,
    observation: ScannerObservation,
    actor,
    triage_status: str,
    triage_note: str = "",
    duplicate_of: ScannerObservation | None = None,
) -> ScannerObservation:
    if not can_write_client_records(actor, observation.assessment.client):
        raise PermissionDenied("You cannot triage this observation.")
    if observation.triage_status == ScannerObservation.TriageStatus.PROMOTED:
        raise ValidationError("Promoted observations cannot be triaged again.")
    if triage_status not in ALLOWED_TRIAGE_STATUSES:
        raise ValidationError("Unsupported triage status.")

    safe_note = sanitise_evidence(triage_note, max_length=1000)
    if triage_status == ScannerObservation.TriageStatus.FALSE_POSITIVE and not safe_note:
        raise ValidationError("False positive triage requires a review note.")

    if triage_status == ScannerObservation.TriageStatus.DUPLICATE:
        if duplicate_of is None:
            raise ValidationError("Duplicate triage requires duplicate_of_id.")
        if duplicate_of.id == observation.id:
            raise ValidationError("Observation cannot be marked duplicate of itself.")
        if duplicate_of.assessment_id != observation.assessment_id:
            raise ValidationError("Duplicate observation must belong to the same assessment.")
    else:
        duplicate_of = None

    observation.triage_status = triage_status
    observation.triage_note = safe_note
    observation.duplicate_of = duplicate_of
    observation.triaged_by = actor
    observation.triaged_at = timezone.now()
    observation.save(
        update_fields=[
            "triage_status",
            "triage_note",
            "duplicate_of",
            "triaged_by",
            "triaged_at",
            "updated_at",
        ]
    )
    record_audit_event(
        actor=actor,
        client=observation.assessment.client,
        assessment=observation.assessment,
        action=AuditLog.Action.OBSERVATION_TRIAGED,
        entity_type="ScannerObservation",
        entity_id=observation.id,
        summary=f"Observation triaged as {triage_status}.",
        metadata={"triage_status": triage_status, "duplicate_of_id": duplicate_of.id if duplicate_of else None},
    )
    return observation
