from __future__ import annotations

from typing import Any

from .models import AuditLog

SAFE_METADATA_KEYS = {
    "source_tool",
    "source_filename",
    "observations_created",
    "observations_updated",
    "triage_status",
    "duplicate_of_id",
    "finding_id",
    "scanner_observation_id",
    "changed_fields",
    "status",
    "remediation_owner",
    "due_date",
    "severity",
}


def safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    return {key: value for key, value in metadata.items() if key in SAFE_METADATA_KEYS}


def record_audit_event(
    *,
    actor,
    client,
    action: str,
    entity_type: str,
    entity_id: int,
    summary: str,
    assessment=None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        client=client,
        assessment=assessment,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary[:255],
        metadata=safe_metadata(metadata),
    )
