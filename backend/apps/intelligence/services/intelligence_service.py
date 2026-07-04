from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.findings.models import Finding
from apps.intelligence.models import VulnerabilityIntel
from .cisa_kev_client import CisaKevClient
from .epss_client import EpssClient
from .nvd_client import NvdClient
from .priority_service import PriorityService

CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)


def normalize_cve_id(value: str) -> str:
    cve_id = (value or "").strip().upper()
    if not CVE_RE.match(cve_id):
        raise ValidationError("Finding must have a valid CVE ID such as CVE-2024-1234.")
    return cve_id


@dataclass(frozen=True)
class RefreshResult:
    intel: VulnerabilityIntel | None
    used_cache: bool


class IntelligenceService:
    def __init__(self, *, nvd_client=None, cisa_client=None, epss_client=None):
        self.nvd_client = nvd_client or NvdClient()
        self.cisa_client = cisa_client or CisaKevClient()
        self.epss_client = epss_client or EpssClient()

    @staticmethod
    def get_for_finding(finding: Finding) -> VulnerabilityIntel | None:
        if not finding.cve_id:
            return None
        cve_id = normalize_cve_id(finding.cve_id)
        return VulnerabilityIntel.objects.filter(cve_id=cve_id).first()

    @transaction.atomic
    def refresh_for_finding(self, finding: Finding, *, force: bool = False) -> RefreshResult:
        cve_id = normalize_cve_id(finding.cve_id)
        now = timezone.now()
        ttl = timedelta(hours=settings.INTELLIGENCE_CACHE_TTL_HOURS)
        existing = VulnerabilityIntel.objects.filter(cve_id=cve_id).first()
        if existing and not force and existing.source_retrieved_at and existing.source_retrieved_at >= now - ttl:
            PriorityService.update_finding_priority(finding, existing)
            return RefreshResult(existing, True)

        failures: list[str] = []
        nvd = cisa = epss = None
        try:
            nvd = self.nvd_client.fetch(cve_id)
        except Exception:
            failures.append("NVD unavailable")
        try:
            cisa = self.cisa_client.fetch(cve_id)
        except Exception:
            failures.append("CISA KEV unavailable")
        try:
            epss = self.epss_client.fetch(cve_id)
        except Exception:
            failures.append("EPSS unavailable")

        if nvd is None and cisa is None and epss is None:
            if existing:
                existing.last_refresh_attempt_at = now
                existing.last_refresh_status = VulnerabilityIntel.RefreshStatus.FAILED
                existing.last_safe_error = "Public intelligence providers unavailable."
                existing.save(update_fields=["last_refresh_attempt_at", "last_refresh_status", "last_safe_error", "updated_at"])
                PriorityService.update_finding_priority(finding, existing)
                return RefreshResult(existing, False)
            raise ValidationError("Public intelligence providers unavailable; no cached data exists.")

        intel = existing or VulnerabilityIntel(cve_id=cve_id)
        if nvd is not None:
            intel.nvd_description = nvd.description
            intel.nvd_cvss_score = nvd.cvss_score
            intel.nvd_cvss_vector = nvd.cvss_vector
            intel.cwe_ids = nvd.cwe_ids
            intel.references = nvd.references
        if cisa is not None:
            intel.kev_listed = cisa.listed
            intel.kev_date_added = cisa.date_added
        if epss is not None:
            intel.epss_score = epss.score
            intel.epss_percentile = epss.percentile
        intel.source_retrieved_at = now
        intel.last_refresh_attempt_at = now
        intel.last_refresh_status = VulnerabilityIntel.RefreshStatus.PARTIAL if failures else VulnerabilityIntel.RefreshStatus.SUCCESS
        intel.last_safe_error = "; ".join(failures)[:255] if failures else ""
        intel.save()
        PriorityService.update_finding_priority(finding, intel)
        return RefreshResult(intel, False)
