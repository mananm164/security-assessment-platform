from __future__ import annotations

import hashlib
from dataclasses import fields
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event
from apps.common.exceptions import ImportValidationError
from apps.tenancy.selectors import can_write_client_records, user_is_admin, visible_clients_for

from ..models import ImportPreview, ScanImport
from ..parsers.base import NormalisedObservation
from .import_service import ImportResult, parser_for_tool, persist_normalised_import

PREVIEW_EXPIRES_MINUTES = 15
MAX_PREVIEW_OBSERVATIONS = 2000
PREVIEW_OBSERVATION_SAMPLE_SIZE = 100
EXPECTED_EXTENSIONS = {
    "nmap": {".xml"},
    "zap": {".json"},
    "nessus": {".nessus"},
    "burp": {".xml"},
}
UNSAFE_VALUE_MARKERS = (
    "requestresponse",
    "authorization",
    "cookie",
    "password",
    "passwd",
    "token",
    "secret",
    "payload",
    "raw plugin output",
)


class ImportPreviewExpired(Exception):
    pass


def create_import_preview(*, actor, assessment, source_tool: str, upload) -> ImportPreview:
    if not can_write_client_records(actor, assessment.client):
        raise PermissionDenied("You are not authorised to import reports for this assessment.")

    normalised_tool = _normalise_tool(source_tool)
    safe_filename = Path(getattr(upload, "name", "") or "report").name
    if not safe_filename or safe_filename in {".", ".."}:
        raise ImportValidationError("The selected report could not be validated.")

    _validate_extension(normalised_tool, safe_filename)
    declared_size = int(getattr(upload, "size", 0) or 0)
    if declared_size > settings.MAX_IMPORT_FILE_SIZE_BYTES:
        raise ImportValidationError("The selected report is too large.")

    content = upload.read()
    file_size = len(content)
    if file_size <= 0:
        raise ImportValidationError("The selected report is empty.")
    if file_size > settings.MAX_IMPORT_FILE_SIZE_BYTES:
        raise ImportValidationError("The selected report is too large.")

    parser = parser_for_tool(normalised_tool)
    try:
        parser.validate(content, safe_filename)
        observations = parser.parse(content)
    except ImportValidationError:
        raise ImportValidationError("The selected report could not be validated.")

    if len(observations) > MAX_PREVIEW_OBSERVATIONS:
        raise ImportValidationError(
            f"The selected report has more than {MAX_PREVIEW_OBSERVATIONS} observations."
        )

    safe_observations = [_observation_to_safe_dict(observation) for observation in observations]
    preview = ImportPreview.objects.create(
        assessment=assessment,
        source_tool=parser.source_tool,
        source_filename=safe_filename,
        file_sha256=hashlib.sha256(content).hexdigest(),
        file_size_bytes=file_size,
        parser_version=f"{normalised_tool}-v1",
        safe_observations=safe_observations,
        observation_count=len(safe_observations),
        created_by=actor,
        expires_at=timezone.now() + timezone.timedelta(minutes=PREVIEW_EXPIRES_MINUTES),
    )
    record_audit_event(
        actor=actor,
        client=assessment.client,
        assessment=assessment,
        action=AuditLog.Action.IMPORT_PREVIEW_CREATED,
        entity_type="IMPORT_PREVIEW",
        entity_id=preview.id,
        summary=f"Created {preview.source_tool} import preview {preview.source_filename}.",
        safe_metadata={
            "assessment_id": assessment.id,
            "source_tool": preview.source_tool,
            "source_filename": preview.source_filename,
            "file_sha256_prefix": preview.file_sha256[:12],
            "file_size_bytes": preview.file_size_bytes,
            "observation_count": preview.observation_count,
        },
    )
    return preview


def get_visible_preview(*, actor, preview_id) -> ImportPreview:
    preview = (
        ImportPreview.objects.select_related("assessment", "assessment__client", "created_by", "scan_import")
        .filter(id=preview_id)
        .first()
    )
    if preview is None:
        raise ImportPreview.DoesNotExist
    if not visible_clients_for(actor).filter(id=preview.assessment.client_id).exists():
        raise ImportPreview.DoesNotExist
    if not can_write_client_records(actor, preview.assessment.client):
        raise PermissionDenied("You are not authorised to view this import preview.")
    if not user_is_admin(actor) and preview.created_by_id != actor.id:
        raise PermissionDenied("You are not authorised to view this import preview.")
    if preview.expires_at <= timezone.now() and preview.confirmed_at is None:
        raise ImportPreviewExpired
    return preview


def confirm_import_preview(*, actor, preview: ImportPreview) -> ImportResult:
    with transaction.atomic():
        locked_preview = (
            ImportPreview.objects.select_for_update()
            .select_related("assessment", "assessment__client")
            .get(id=preview.id)
        )
        if not visible_clients_for(actor).filter(id=locked_preview.assessment.client_id).exists():
            raise ImportPreview.DoesNotExist
        if not can_write_client_records(actor, locked_preview.assessment.client):
            raise PermissionDenied("You are not authorised to confirm this import preview.")
        if not user_is_admin(actor) and locked_preview.created_by_id != actor.id:
            raise PermissionDenied("You are not authorised to confirm this import preview.")
        if locked_preview.confirmed_at and locked_preview.scan_import_id:
            scan_import = locked_preview.scan_import
            return ImportResult(
                scan_import=scan_import,
                observations_created=scan_import.observations_created,
                observations_reobserved=scan_import.observations_updated,
            )
        if locked_preview.expires_at <= timezone.now():
            raise ImportPreviewExpired

        observations = [_safe_dict_to_observation(item) for item in locked_preview.safe_observations]
        result = persist_normalised_import(
            assessment=locked_preview.assessment,
            actor=actor,
            source_tool=locked_preview.source_tool,
            source_filename=locked_preview.source_filename,
            file_sha256=locked_preview.file_sha256,
            observations=observations,
        )
        locked_preview.scan_import = result.scan_import
        locked_preview.confirmed_by = actor
        locked_preview.confirmed_at = timezone.now()
        locked_preview.save(update_fields=["scan_import", "confirmed_by", "confirmed_at"])
        record_audit_event(
            actor=actor,
            client=locked_preview.assessment.client,
            assessment=locked_preview.assessment,
            action=AuditLog.Action.IMPORT_CONFIRMED,
            entity_type="IMPORT_PREVIEW",
            entity_id=locked_preview.id,
            summary=f"Confirmed {locked_preview.source_tool} import preview {locked_preview.source_filename}.",
            safe_metadata={
                "assessment_id": locked_preview.assessment_id,
                "scan_import_id": result.scan_import.id,
                "source_tool": locked_preview.source_tool,
                "source_filename": locked_preview.source_filename,
                "observations_created": result.observations_created,
                "observations_reobserved": result.observations_reobserved,
            },
        )
        return result


def preview_summary(preview: ImportPreview) -> dict:
    assets = {
        _asset_label(item)
        for item in preview.safe_observations
        if _asset_label(item)
    }
    return {
        "total_observations": preview.observation_count,
        "assets_detected": len(assets),
        "source_tool": preview.source_tool,
    }


def preview_observation_sample(preview: ImportPreview) -> list[dict]:
    return [_preview_row(item) for item in preview.safe_observations[:PREVIEW_OBSERVATION_SAMPLE_SIZE]]


def _normalise_tool(source_tool: str) -> str:
    tool = (source_tool or "").strip().lower()
    if tool not in EXPECTED_EXTENSIONS:
        raise ImportValidationError("Unsupported scanner import tool.")
    return tool


def _validate_extension(tool: str, filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in EXPECTED_EXTENSIONS[tool]:
        raise ImportValidationError("The selected report type does not match the source tool.")


def _observation_to_safe_dict(observation: NormalisedObservation) -> dict:
    data = {}
    for field in fields(NormalisedObservation):
        value = getattr(observation, field.name)
        if field.name in {"url", "asset_identifier", "raw_location"}:
            value = _strip_query_and_fragment(value)
        data[field.name] = _clean_value(value)
    return data


def _safe_dict_to_observation(item: dict) -> NormalisedObservation:
    allowed = {field.name for field in fields(NormalisedObservation)}
    values = {key: item.get(key) for key in allowed if key in item}
    values["cve_ids"] = values.get("cve_ids") or []
    values["cwe_ids"] = values.get("cwe_ids") or []
    values["references"] = values.get("references") or []
    return NormalisedObservation(**values)


def _preview_row(item: dict) -> dict:
    return {
        "title": item.get("title") or "Imported observation",
        "raw_severity": item.get("raw_severity") or "",
        "asset_label": _asset_label(item),
        "location": item.get("raw_location") or item.get("url") or "",
        "scanner_plugin_id": item.get("scanner_plugin_id") or "",
        "confidence": item.get("confidence") or "",
    }


def _asset_label(item: dict) -> str:
    return item.get("asset_identifier") or item.get("hostname") or item.get("url") or ""


def _strip_query_and_fragment(value):
    if not isinstance(value, str) or not value:
        return value
    if "://" in value:
        parsed = urlsplit(value)
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    return value.split("?", 1)[0].split("#", 1)[0]


def _clean_value(value):
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        compact = value.replace("\x00", " ").strip()
        lowered = compact.lower()
        if any(marker in lowered for marker in UNSAFE_VALUE_MARKERS):
            return "[redacted]"
        return compact[:2000]
    if isinstance(value, list):
        return [_clean_value(item) for item in value[:50]]
    if isinstance(value, dict):
        return {str(key)[:80]: _clean_value(item) for key, item in list(value.items())[:50]}
    return str(value)[:255]
