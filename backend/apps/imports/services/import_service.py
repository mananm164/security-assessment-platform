from __future__ import annotations

import hashlib
import ipaddress
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.assessments.models import Asset, Assessment
from apps.common.exceptions import ImportValidationError
from apps.tenancy.selectors import can_write_client_records

from ..models import ScanImport, ScanImportObservation, ScannerObservation
from ..parsers.base import NormalisedObservation
from ..parsers.nmap import NmapXmlImporter


def parser_for_tool(tool: str):
    normalised_tool = tool.strip().lower()
    if normalised_tool != "nmap":
        raise ImportValidationError("Unsupported scanner import tool.")
    return NmapXmlImporter(max_size_bytes=settings.MAX_IMPORT_FILE_SIZE_BYTES)


def observation_fingerprint(*, assessment: Assessment, observation: NormalisedObservation) -> str:
    components = [
        observation.source_tool.lower(),
        str(assessment.id),
        observation.asset_identifier or "",
        observation.protocol or "",
        str(observation.port or ""),
        observation.scanner_plugin_id or "",
    ]
    return hashlib.sha256("|".join(components).encode("utf-8")).hexdigest()


def import_report(
    *,
    assessment: Assessment,
    actor,
    tool: str,
    filename: str,
    content: bytes,
) -> ScanImport:
    if not can_write_client_records(actor, assessment.client):
        raise ImportValidationError("Actor is not authorised to import into this assessment.")

    parser = parser_for_tool(tool)
    safe_filename = Path(filename).name
    parser.validate(content, safe_filename)
    observations = parser.parse(content)
    file_sha256 = hashlib.sha256(content).hexdigest()

    with transaction.atomic():
        scan_import = ScanImport.objects.create(
            assessment=assessment,
            source_tool=ScanImport.SourceTool.NMAP,
            source_filename=safe_filename,
            file_sha256=file_sha256,
            imported_by=actor,
            status=ScanImport.Status.PROCESSING,
        )
        created_count = 0
        updated_count = 0
        now = timezone.now()

        for observation in observations:
            asset = match_or_create_asset(assessment=assessment, observation=observation)
            fingerprint = observation_fingerprint(assessment=assessment, observation=observation)
            scanner_observation, created = ScannerObservation.objects.get_or_create(
                assessment=assessment,
                fingerprint=fingerprint,
                defaults={
                    "asset": asset,
                    "source_tool": ScanImport.SourceTool.NMAP,
                    "external_id": observation.external_id,
                    "scanner_plugin_id": observation.scanner_plugin_id or "",
                    "title": observation.title,
                    "description": observation.description,
                    "evidence_summary": observation.evidence_summary,
                    "raw_severity": observation.raw_severity or "",
                    "confidence": observation.confidence or "",
                    "port": observation.port,
                    "protocol": observation.protocol or "",
                    "url": observation.url or "",
                    "suggested_remediation": observation.suggested_remediation or "",
                    "cve_ids": observation.cve_ids,
                    "cwe_ids": observation.cwe_ids,
                    "references": observation.references,
                    "raw_location": observation.raw_location or "",
                    "first_seen_at": now,
                    "last_seen_at": now,
                    "first_seen_import": scan_import,
                    "last_seen_import": scan_import,
                },
            )

            state = ScanImportObservation.State.CREATED
            if created:
                created_count += 1
            else:
                updated_count += 1
                state = ScanImportObservation.State.REOBSERVED
                scanner_observation.asset = scanner_observation.asset or asset
                scanner_observation.external_id = observation.external_id
                scanner_observation.scanner_plugin_id = observation.scanner_plugin_id or ""
                scanner_observation.title = observation.title
                scanner_observation.description = observation.description
                scanner_observation.evidence_summary = observation.evidence_summary
                scanner_observation.raw_severity = observation.raw_severity or ""
                scanner_observation.confidence = observation.confidence or ""
                scanner_observation.port = observation.port
                scanner_observation.protocol = observation.protocol or ""
                scanner_observation.url = observation.url or ""
                scanner_observation.suggested_remediation = observation.suggested_remediation or ""
                scanner_observation.cve_ids = observation.cve_ids
                scanner_observation.cwe_ids = observation.cwe_ids
                scanner_observation.references = observation.references
                scanner_observation.raw_location = observation.raw_location or ""
                scanner_observation.last_seen_at = now
                scanner_observation.last_seen_import = scan_import
                scanner_observation.save()

            ScanImportObservation.objects.create(
                scan_import=scan_import,
                scanner_observation=scanner_observation,
                state=state,
            )

        scan_import.observations_created = created_count
        scan_import.observations_updated = updated_count
        scan_import.status = ScanImport.Status.COMPLETED
        scan_import.completed_at = timezone.now()
        scan_import.save(
            update_fields=[
                "observations_created",
                "observations_updated",
                "status",
                "completed_at",
            ]
        )
        return scan_import


def match_or_create_asset(*, assessment: Assessment, observation: NormalisedObservation) -> Asset | None:
    identifier = observation.asset_identifier
    hostname = observation.hostname
    if not identifier and not hostname:
        return None

    if identifier and _looks_like_ip(identifier):
        existing = Asset.objects.filter(assessment=assessment, ip_address=identifier).first()
        if existing:
            return existing
    if hostname:
        existing = Asset.objects.filter(assessment=assessment, hostname=hostname).first()
        if existing:
            return existing

    display_name = hostname or identifier or "Imported host"
    return Asset.objects.create(
        assessment=assessment,
        asset_type=Asset.AssetType.HOST,
        display_name=display_name,
        hostname=hostname or "",
        ip_address=identifier if identifier and _looks_like_ip(identifier) else None,
        environment=Asset.Environment.UNKNOWN,
        criticality=Asset.Criticality.MEDIUM,
        internet_exposed=False,
    )


def _looks_like_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True
