from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event
from apps.imports.parsers.nmap import sanitise_evidence
from apps.tenancy.selectors import can_write_client_records

from ..models import Finding

EDITABLE_FIELDS = {
    "status",
    "business_impact",
    "remediation",
    "remediation_owner",
    "due_date",
    "validation_evidence",
    "risk_acceptance_reason",
    "risk_review_due_date",
}
TEXT_FIELDS = {"business_impact", "remediation", "remediation_owner", "validation_evidence", "risk_acceptance_reason"}
OPEN_STATUSES = {Finding.Status.OPEN, Finding.Status.IN_PROGRESS}
TERMINAL_STATUSES = {Finding.Status.CLOSED, Finding.Status.ACCEPTED_RISK}


def _normalise_value(field: str, value: Any) -> Any:
    if field in TEXT_FIELDS:
        max_length = 255 if field == "remediation_owner" else 4000
        return sanitise_evidence(value or "", max_length=max_length)
    return value


def _date_or_none(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _changed_fields(before: dict[str, Any], finding: Finding) -> list[str]:
    changed = []
    for field, old_value in before.items():
        if old_value != getattr(finding, field):
            changed.append(field)
    return changed


@transaction.atomic
def update_finding_lifecycle(*, finding: Finding, actor, changes: dict[str, Any]) -> Finding:
    if not can_write_client_records(actor, finding.assessment.client):
        raise PermissionDenied("You cannot update findings for this assessment.")

    permitted = {field: _normalise_value(field, value) for field, value in changes.items() if field in EDITABLE_FIELDS}
    before = {field: getattr(finding, field) for field in EDITABLE_FIELDS}
    old_status = finding.status
    old_owner = finding.remediation_owner
    old_due_date = finding.due_date

    for field, value in permitted.items():
        setattr(finding, field, value)

    if finding.status == Finding.Status.CLOSED:
        if not finding.validation_evidence.strip():
            raise ValidationError({"validation_evidence": "Validation evidence is required before closing a finding."})
        if finding.validated_by_id is None:
            finding.validated_by = actor
        if finding.validated_at is None:
            finding.validated_at = timezone.now()

    if finding.status == Finding.Status.ACCEPTED_RISK:
        if not finding.risk_acceptance_reason.strip():
            raise ValidationError({"risk_acceptance_reason": "Accepted risk requires a reason."})
        if finding.risk_review_due_date is None:
            raise ValidationError({"risk_review_due_date": "Accepted risk requires a review due date."})
        if finding.risk_review_due_date < timezone.localdate():
            raise ValidationError({"risk_review_due_date": "Risk review due date cannot be in the past."})
        if finding.risk_accepted_by_id is None:
            finding.risk_accepted_by = actor
        if finding.risk_accepted_at is None:
            finding.risk_accepted_at = timezone.now()

    changed_fields = _changed_fields(before, finding)
    if not changed_fields:
        return finding

    finding.save(
        update_fields=[
            *changed_fields,
            "validated_by",
            "validated_at",
            "risk_accepted_by",
            "risk_accepted_at",
            "updated_at",
        ]
    )

    metadata = {
        "changed_fields": changed_fields,
        "old_status": old_status,
        "new_status": finding.status,
        "old_remediation_owner": old_owner,
        "new_remediation_owner": finding.remediation_owner,
        "old_due_date": _date_or_none(old_due_date),
        "new_due_date": _date_or_none(finding.due_date),
    }
    record_audit_event(
        actor=actor,
        client=finding.assessment.client,
        assessment=finding.assessment,
        action=AuditLog.Action.FINDING_UPDATED,
        entity_type="FINDING",
        entity_id=finding.id,
        summary=f"Finding updated: {', '.join(changed_fields)}.",
        safe_metadata=metadata,
    )

    if "status" in changed_fields:
        record_audit_event(
            actor=actor,
            client=finding.assessment.client,
            assessment=finding.assessment,
            action=AuditLog.Action.FINDING_STATUS_CHANGED,
            entity_type="FINDING",
            entity_id=finding.id,
            summary=f"Finding status changed from {old_status} to {finding.status}.",
            safe_metadata={"old_status": old_status, "new_status": finding.status},
        )
        if old_status in TERMINAL_STATUSES and finding.status in OPEN_STATUSES:
            record_audit_event(
                actor=actor,
                client=finding.assessment.client,
                assessment=finding.assessment,
                action=AuditLog.Action.FINDING_REOPENED,
                entity_type="FINDING",
                entity_id=finding.id,
                summary="Finding reopened.",
                safe_metadata={"old_status": old_status, "new_status": finding.status},
            )
        if finding.status == Finding.Status.CLOSED:
            record_audit_event(
                actor=actor,
                client=finding.assessment.client,
                assessment=finding.assessment,
                action=AuditLog.Action.FINDING_CLOSED,
                entity_type="FINDING",
                entity_id=finding.id,
                summary="Finding closed with validation evidence.",
                safe_metadata={"old_status": old_status, "new_status": finding.status, "validated_by_id": actor.id},
            )
        if finding.status == Finding.Status.ACCEPTED_RISK:
            record_audit_event(
                actor=actor,
                client=finding.assessment.client,
                assessment=finding.assessment,
                action=AuditLog.Action.FINDING_RISK_ACCEPTED,
                entity_type="FINDING",
                entity_id=finding.id,
                summary="Finding risk accepted pending review.",
                safe_metadata={
                    "old_status": old_status,
                    "new_status": finding.status,
                    "risk_accepted_by_id": actor.id,
                    "new_due_date": _date_or_none(finding.risk_review_due_date),
                },
            )

    if "remediation_owner" in changed_fields:
        record_audit_event(
            actor=actor,
            client=finding.assessment.client,
            assessment=finding.assessment,
            action=AuditLog.Action.FINDING_OWNER_CHANGED,
            entity_type="FINDING",
            entity_id=finding.id,
            summary="Finding remediation owner changed.",
            safe_metadata={"old_remediation_owner": old_owner, "new_remediation_owner": finding.remediation_owner},
        )
    if "due_date" in changed_fields:
        record_audit_event(
            actor=actor,
            client=finding.assessment.client,
            assessment=finding.assessment,
            action=AuditLog.Action.FINDING_DUE_DATE_CHANGED,
            entity_type="FINDING",
            entity_id=finding.id,
            summary="Finding due date changed.",
            safe_metadata={
                "old_due_date": _date_or_none(old_due_date),
                "new_due_date": _date_or_none(finding.due_date),
            },
        )
    return finding
