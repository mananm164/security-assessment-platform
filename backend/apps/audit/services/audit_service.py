from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.audit.models import AuditLog

SAFE_METADATA_KEYS = {
    "source_tool",
    "source_filename",
    "observations_created",
    "observations_updated",
    "observations_reobserved",
    "assessment_id",
    "file_sha256",
    "file_sha256_prefix",
    "file_size_bytes",
    "observation_count",
    "scan_import_id",
    "triage_status",
    "duplicate_of_id",
    "finding_id",
    "scanner_observation_id",
    "changed_fields",
    "status",
    "old_status",
    "new_status",
    "remediation_owner",
    "old_remediation_owner",
    "new_remediation_owner",
    "due_date",
    "old_due_date",
    "new_due_date",
    "severity",
    "provider",
    "model",
    "artifact_id",
    "priority_score",
    "priority_label",
    "used_cache",
    "validated_by_id",
    "risk_accepted_by_id",
}
UNSAFE_KEY_MARKERS = {
    "password",
    "token",
    "secret",
    "cookie",
    "authorization",
    "jwt",
    "session",
    "prompt",
    "payload",
    "raw",
}


def _safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in UNSAFE_KEY_MARKERS):
            return "[redacted]"
        return value[:255]
    if isinstance(value, list):
        return [_safe_value(item) for item in value[:20]]
    if isinstance(value, dict):
        return {str(key)[:80]: _safe_value(item) for key, item in list(value.items())[:20]}
    return str(value)[:255]


def safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    cleaned: dict[str, Any] = {}
    for key, value in metadata.items():
        normalised_key = str(key)
        lowered = normalised_key.lower()
        if normalised_key not in SAFE_METADATA_KEYS:
            continue
        if any(marker in lowered for marker in UNSAFE_KEY_MARKERS):
            continue
        cleaned[normalised_key] = _safe_value(value)
    return cleaned


@transaction.atomic
def record_audit_event(
    *,
    actor,
    client,
    action: str,
    entity_type: str,
    entity_id: int | str,
    summary: str | None = None,
    assessment=None,
    metadata: dict[str, Any] | None = None,
    safe_metadata: dict[str, Any] | None = None,
) -> AuditLog:
    cleaned = globals()["safe_metadata"](safe_metadata if safe_metadata is not None else metadata)
    safe_summary = (summary or action.replace("_", " ").title())[:255]
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        client=client,
        assessment=assessment,
        action=action,
        entity_type=entity_type,
        entity_id=int(entity_id),
        summary=safe_summary,
        metadata=cleaned,
        safe_metadata=cleaned,
    )
